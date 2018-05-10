import boto3
from botocore.exceptions import ClientError
import time
import sys
import base64
import os
from io import BytesIO
import gzip
import random

# How to use this function
# 1. permissions: S3 + MachineLearning + DynamoDB
# 2. setup cloudwatch events to call self every 10 mins
# 3. need file 's3://bucket/Data/full_mv.csv' (movie vector)
# 4. need file 's3://bucket/Data/user_like.csv' (user preferences)
# 5. After 's3://bucket/Data/user_like.csv' is updated,
#   use the following 2 lines of code to start the ML process.
#   the result 'Data/predictions.csv' will appear about 40 min later
#       if read_state()[0] == 'END':
#           write_state(['START', '', '', '', '', '', ''])
# 6. Change state to 'START' will cause lambda function to
#   start working, will store predictions in 'Data/predictions.csv'
#   After about 40 min, the function state turns back to 'END'
#   We should only change state from 'END' to 'START',
#   The state will change back to 'END' after finishing all the work


my_bucket_name = 'cloud-computing-project-bucket'
file_user_like = 'Data/user_like.csv'  # schema: userid, movieid, score(with header)
file_predictions = 'Data/predictions.csv'  # schema: tag,score (with header)


def read_state():
    '''
    state: s3://bucket/Data/Lambda_State.csv
    schema : state, ds_70, ds_30, ds_batch, ml_id, ev_id, bp_id
    state =
        'END' :
                do nothing
                After Usertable is updated, Change END to START
        'START':
                need training data "Data/training_random.csv"
                and batch data file "Data/batch_data.csv"
                create ds_30, ds_70, ds_batch, ml_id, ev_id
                update state and quit
                advance to next state
        'WAIT':
                wait for bp_id
                create bp_id if ready
                advance
        'FINAL':
                unzip the predict result
                store it in DB or S3
        'CLEANUP':
                delete resources used
    '''
    try:
        client = boto3.client('s3')
        obj = client.get_object(Bucket=my_bucket_name, Key='Data/Lambda_State.csv')
    except ClientError as e:
        print("Unexpected error: %s" % e)
        s3 = boto3.resource('s3')
        write_obj = s3.Object(my_bucket_name, 'Data/Lambda_State.csv')
        write_obj.put(Body=b'END,,,,,,\r\n')
        return tuple([x.decode('ascii') for x in b'END,,,,,,'.split(b',')])
    else:
        lines = obj['Body'].read().split(b'\r\n')
        return tuple([x.decode('ascii') for x in lines[0].split(b',')])


def write_state(state):
    content = b','.join([x.encode('ascii') for x in state])
    s3 = boto3.resource('s3')
    write_obj = s3.Object(my_bucket_name, 'Data/Lambda_State.csv')
    write_obj.put(Body=content)


def get_movie_dict(numVotes_limit=0, rating_limit=0.0, start_year_limit=0):
    client = boto3.client('s3')  # low-level functional API
    obj = client.get_object(Bucket=my_bucket_name, Key='Data/full_mv.csv')
    lines = obj['Body'].read().split(b'\r\n')
    obj['Body'].close()
    movie_dict = {}
    header = True
    for r in lines:
        if header:
            header = False
        else:
            try:
                row = r.split(b',')
                if int(row[3]) >= numVotes_limit and \
                        float(row[2]) + 0.000001 >= rating_limit and \
                        int(row[1]) >= start_year_limit:
                    movie_dict[row[0]] = row[:29]  # omit last 4 genres
            except IndexError:
                pass
            except ValueError:
                pass
    return movie_dict


def generateTrainingData(numVotes_limit=0, rating_limit=0.0, start_year_limit=0):
    '''
    input:
    Data/full_mv.csv : the full movie vector of 217819 movies
    schema: tconst,startYear,rating,numVotes,...,29 genres,...

    Data/user_like.csv : the user-movie relationship
    schema: userid, movieid, score

    output:
    Data/training_random.csv
    output info:  the training data for AWS ML
    schema: userid,movie_vector,Like
    '''
    md = get_movie_dict(numVotes_limit, rating_limit, start_year_limit)

    client = boto3.client('s3')
    obj = client.get_object(Bucket=my_bucket_name, Key=file_user_like)
    lines = obj['Body'].read().split(b'\r\n')
    obj['Body'].close()
    # 2. generate user info
    # ','.join(list(map(str,row)))
    header_row = [b'userid,tconst,startYear,rating,numVotes,Action,Adventure,Mystery,\
Drama,Fantasy,Comedy,None,Horror,Crime,Film-Noir,Musical,Romance,Music,Western,\
Sport,War,Documentary,Biography,History,Thriller,Family,Sci-Fi,Adult,Animation,\
News,Like']
    content = []
    for r in lines:
        row = r.split(b',')
        if len(row) == 3:
            key = row[1]
            if key in md:
                content.append(b','.join([row[0], row[0] + b'-' + md[key][0]] + md[key][1:] + [row[2]]))
        else:
            print(r)
    random.shuffle(content)
    if len(content) > 10000:
        content = content[:10000]
    some_binary_data = b'\r\n'.join(header_row + content) + b'\r\n'

    s3 = boto3.resource('s3')
    write_obj = s3.Object(my_bucket_name, 'Data/training_random.csv')
    write_obj.put(Body=some_binary_data)


def generateBatchData(numVotes_limit=10000, rating_limit=7.5, start_year_limit=2000):
    '''
    input:
    Data/full_mv.csv : the full movie vector of 217819 movies
    schema: tconst,startYear,rating,numVotes,...,29 genres,...

    Data/user_like.csv : the user-movie relationship
    schema: userid, movieid, score

    output:
    Data/batch_data.csv
    output info:  data for ML to predict (limited at 1000 lines)
    schema: userid,movie_vector
    '''
    md = get_movie_dict(numVotes_limit, rating_limit, start_year_limit)

    client = boto3.client('s3')
    obj = client.get_object(Bucket=my_bucket_name, Key=file_user_like)
    lines = obj['Body'].read().split(b'\r\n')
    obj['Body'].close()
    user_ids = {}
    for r in lines:
        row = r.split(b',')
        if len(row) == 3:
            user_ids[row[0]] = True
        else:
            pass
    header_row = [b'userid,tconst,startYear,rating,numVotes,Action,Adventure,Mystery,\
Drama,Fantasy,Comedy,None,Horror,Crime,Film-Noir,Musical,Romance,Music,Western,\
Sport,War,Documentary,Biography,History,Thriller,Family,Sci-Fi,Adult,Animation,\
News']
    content = []
    for key in md:
        for uid in user_ids:
            m_info = md[key]
            content.append(b','.join([uid, uid + b'-' + m_info[0]] + m_info[1:]))
    random.shuffle(content)
    if len(content) > 1000:
        content = content[:1000]
    some_binary_data = b'\r\n'.join(header_row + content) + b'\r\n'
    s3 = boto3.resource('s3')
    write_obj = s3.Object(my_bucket_name, 'Data/batch_data.csv')
    write_obj.put(Body=some_binary_data)


def check_ds_status(ds_id):
    # 'Status': 'PENDING'|'INPROGRESS'|'FAILED'|'COMPLETED'|'DELETED'
    client = boto3.client('machinelearning', region_name='us-east-1')
    response = client.get_data_source(DataSourceId=ds_id)
    return response.get('Status')


def check_ml_status(ml_id):
    client = boto3.client('machinelearning', region_name='us-east-1')
    response = client.get_ml_model(MLModelId=ml_id)
    return response.get('Status')


def check_bp_status(bp_id):
    client = boto3.client('machinelearning', region_name='us-east-1')
    response = client.get_batch_prediction(BatchPredictionId=bp_id)
    return response.get('Status')


def check_ev_status(ev_id):
    client = boto3.client('machinelearning', region_name='us-east-1')
    response = client.get_evaluation(EvaluationId=ev_id)
    return response.get('Status')


def create_training_data_70():
    client = boto3.client('machinelearning', region_name='us-east-1')
    ds_id = 'ds-' + base64.b64encode(os.urandom(30), b'-_').decode('ascii')
    response = client.create_data_source_from_s3(
        DataSourceId=ds_id,
        DataSourceName='movie-training-70-' + ds_id[3:9],
        DataSpec={
            'DataLocationS3': 's3://cloud-computing-project-bucket/Data/training_random.csv',
            'DataRearrangement': '{"splitting":{"percentBegin":0, "percentEnd":70, "strategy":"sequential"}}',
            'DataSchemaLocationS3': 's3://cloud-computing-project-bucket/Data/training_data_schema.json'
        },
        ComputeStatistics=True
    )
    return ds_id


def create_training_data_30():
    client = boto3.client('machinelearning', region_name='us-east-1')
    ds_id = 'ds-' + base64.b64encode(os.urandom(30), b'-_').decode('ascii')
    response = client.create_data_source_from_s3(
        DataSourceId=ds_id,
        DataSourceName='movie-training-30-' + ds_id[3:9],
        DataSpec={
            'DataLocationS3': 's3://cloud-computing-project-bucket/Data/training_random.csv',
            'DataRearrangement': '{"splitting":{"percentBegin":70, "percentEnd":100, "strategy":"sequential"}}',
            'DataSchemaLocationS3': 's3://cloud-computing-project-bucket/Data/training_data_schema.json'
        },
        ComputeStatistics=True
    )
    return ds_id


def create_batch_data():
    client = boto3.client('machinelearning', region_name='us-east-1')
    ds_id = 'ds-' + base64.b64encode(os.urandom(30), b'-_').decode('ascii')
    response = client.create_data_source_from_s3(
        DataSourceId=ds_id,
        DataSourceName='batch-training-' + ds_id[3:9],
        DataSpec={
            'DataLocationS3': 's3://cloud-computing-project-bucket/Data/batch_data.csv',
            'DataSchemaLocationS3': 's3://cloud-computing-project-bucket/Data/batch_data_schema.json'
        },
        ComputeStatistics=True
    )
    return ds_id


def delete_ds(ds_id):
    client = boto3.client('machinelearning', region_name='us-east-1')
    response = client.delete_data_source(DataSourceId=ds_id)
    return ds_id


def delete_evaluation(ev_id):
    client = boto3.client('machinelearning', region_name='us-east-1')
    client.delete_evaluation(EvaluationId=ev_id)
    return ev_id


def delete_ml_model(ml_id):
    client = boto3.client('machinelearning', region_name='us-east-1')
    client.delete_ml_model(MLModelId=ml_id)
    return ml_id


def delete_batch_prediction(bp_id):
    client = boto3.client('machinelearning', region_name='us-east-1')
    client.delete_batch_prediction(BatchPredictionId=bp_id)
    return bp_id


def delete_s3_file(key):
    response = client.delete_object(
        Bucket=my_bucket_name,
        Key=key
    )


def create_ml_model(ds_70):
    client = boto3.client('machinelearning', region_name='us-east-1')
    ml_id = 'ml-' + base64.b64encode(os.urandom(30), b'-_').decode('ascii')
    response = client.create_ml_model(
        MLModelId=ml_id,
        MLModelName='ML Model: movie recommendation - ' + ml_id[3:9],
        MLModelType='REGRESSION',
        Parameters={
            'sgd.maxPasses': '20'
        },
        TrainingDataSourceId=ds_70,
        # Recipe='string',
        # RecipeUri='string'
    )
    return ml_id


def create_evaluation(ml_id, ds_30):
    client = boto3.client('machinelearning', region_name='us-east-1')
    ev_id = 'ev-' + base64.b64encode(os.urandom(30), b'-_').decode('ascii')
    response = client.create_evaluation(
        EvaluationId=ev_id,
        EvaluationName='movie eval - ' + ev_id[3:9],
        MLModelId=ml_id,
        EvaluationDataSourceId=ds_30
    )
    return ev_id


def create_batch_prediction(ml_id, ds_batch):
    client = boto3.client('machinelearning', region_name='us-east-1')
    bp_id = 'bp-' + base64.b64encode(os.urandom(30), b'-_').decode('ascii')
    response = client.create_batch_prediction(
        BatchPredictionId=bp_id,
        BatchPredictionName='batch Prediction - ' + bp_id[3:9],
        MLModelId=ml_id,
        BatchPredictionDataSourceId=ds_batch,
        OutputUri='s3://cloud-computing-project-bucket/Data/'
    )
    return bp_id


def get_batch_prediction(bp_id):
    zip_file_path = 'Data/batch-prediction/result/' + bp_id + '-batch_data.csv.gz'
    try:
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=my_bucket_name, Key=zip_file_path)
    except ClientError as e:
        print("Unexpected error: %s" % e)
        return False
    else:
        compressed = BytesIO(obj['Body'].read())
        deFile = gzip.GzipFile(fileobj=compressed)
        obj['Body'].close()

        s3 = boto3.resource('s3')
        write_obj = s3.Object(my_bucket_name, file_predictions)
        write_obj.put(Body=deFile.read())
        return True
    return False


def lambda_handler(event, context):
    # write_state(['START', '', '', '', '', '', ''])
    # return
    # TODO implement
    # generateTrainingData()
    # generateBatchData()
    # md = get_movie_dict(10000, 7.0, 2000)
    # return len(md)
    row = read_state()
    if len(row) != 7:
        return 'State Error!'

    state, ds_70, ds_30, ds_batch, ml_id, ev_id, bp_id = row
    print(row)
    if state == 'END':
        return 'GO TO END'
    elif state == 'START':
        # start training
        generateTrainingData()
        generateBatchData()
        # delete_s3_file('Data/predictions.csv')
        # ds_30 = create_training_data_30()
        ds_70 = create_training_data_70()
        ds_batch = create_batch_data()
        ml_id = create_ml_model(ds_70)
        # ev_id = create_evaluation(ml_id,ds_30)
        bp_id = create_batch_prediction(ml_id, ds_batch)
        write_state(['WAIT', ds_70, ds_30, ds_batch, ml_id, ev_id, bp_id])
        return 'GO TO WAIT'
    elif state == 'WAIT':
        # 'Status': 'PENDING'|'INPROGRESS'|'FAILED'|'COMPLETED'|'DELETED'
        bp_status = check_bp_status(bp_id)
        if bp_status == 'COMPLETED':
            write_state(['FINAL', ds_70, ds_30, ds_batch, ml_id, ev_id, bp_id])
            return 'GO TO FINAL'
        elif bp_status == 'INPROGRESS' or bp_status == 'PENDING':
            pass
        elif bp_status == 'DELETED' or bp_status == 'FAILED':
            write_state(['CLEANUP', ds_70, ds_30, ds_batch, ml_id, ev_id, bp_id])
            return 'GO TO CLEANUP'
        return 'GO TO WAIT'
    elif state == 'FINAL':
        pass
        if get_batch_prediction(bp_id):
            write_state(['CLEANUP', ds_70, ds_30, ds_batch, ml_id, ev_id, bp_id])
            return 'GO TO CLEANUP'
        else:
            return 'GO TO FINAL'
    elif state == 'CLEANUP':
        if ds_70 != '':
            status = check_ds_status(ds_70)
            if status != 'DELETED':
                delete_ds(ds_70)
            else:
                ds_70 = ''

        if ds_30 != '':
            status = check_ds_status(ds_30)
            if status != 'DELETED':
                delete_ds(ds_30)
            else:
                ds_30 = ''

        if ds_batch != '':
            status = check_ds_status(ds_batch)
            if status != 'DELETED':
                delete_ds(ds_batch)
            else:
                ds_batch = ''

        if ml_id != '':
            status = check_ml_status(ml_id)
            if status != 'DELETED':
                delete_ml_model(ml_id)
            else:
                ml_id = ''

        if ev_id != '':
            status = check_ev_status(ev_id)
            if status != 'DELETED':
                delete_evaluation(ev_id)
            else:
                ev_id = ''

        if bp_id != '':
            status = check_bp_status(bp_id)
            if status != 'DELETED':
                delete_batch_prediction(bp_id)
            else:
                bp_id = ''

        X = len(ds_30) + len(ds_70) + len(ds_batch) + \
            len(ml_id) + len(ev_id) + len(bp_id)

        if X == 0:
            write_state(['END', ds_70, ds_30, ds_batch, ml_id, ev_id, bp_id])
            return 'GO TO END'
        return 'GO TO CLEANUP'