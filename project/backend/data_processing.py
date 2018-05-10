import boto3
import json
import decimal
from botocore.exceptions import ClientError
import csv
import pprint
import io


s3 = boto3.resource('s3', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
my_bucket_name = 'cloud-computing-project-bucket'

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def get_scores():
    """Get all scores in table 'score'.

        Returns:
            a string of all scores in csv style.

    """
    table = dynamodb.Table('score')
    response = table.scan()
    datalist = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        datalist.extend(response['Items'])

    strlist = []
    for data in datalist:
        row = []
        row.append(data['uid'].encode())
        row.append(data['mid'].encode())
        row.append(str(data['score']).encode())
        rowstr = b','.join(row)
        strlist.append(rowstr)
    csvstr = b'\r\n'.join(strlist)

    return csvstr


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


def write_score():
    """Write score to S3.

        Returns:
            True.

    """
    write_obj = s3.Object(my_bucket_name, 'Data/user_like.csv')
    write_obj.put(Body=get_scores())
    return True


def update_recommendation():
    """Update all recommendation lists in dynamoDB.

        Returns:
            True/False.
        Raises:
            ClientError: if query DB fails.

    """
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('recommendation')

    mlist = read_recommendation()

    for item in mlist:
        uid = item['uid']
        mids = item['recommendations']
        try:
            response = table.update_item(
                Key={'uid': uid},
                UpdateExpression="set recommendations=:mids",
                ExpressionAttributeValues={
                    ':mids': mids
                },
                ReturnValues="UPDATED_NEW"
            )
        except ClientError as e:
            if e.response['Error']['Code'] == "ConditionalCheckFailedException":
                print(e.response['Error']['Message'])
            else:
                raise
            return False
        else:
            print("UpdateItem succeeded")
    return True


def read_recommendation():
    """Read predictions from S3 file.

        Returns:
            A list of recommended movies' id.

    """
    read_obj = s3.Object(my_bucket_name, 'Data/predictions.csv')
    bres = read_obj.get()["Body"].read()
    strs = json.dumps(bres.decode('utf-8'))
    lines = json.loads(strs)
    file_reader = csv.DictReader(io.StringIO(lines))

    userdict = {}
    mid_list = []
    idx = 0
    for line in file_reader:
        if float(line['score']) > 3:
            tmp = line['tag'].rsplit('-', 1)
            uid = tmp[0]
            mid = tmp[1]
            if uid not in userdict.keys():
                userdict[uid] = idx
                mid_list.append({'uid': uid, 'recommendations': []})
                idx += 1
            else:
                if len(mid_list[userdict[uid]]['recommendations']) < 50:
                    mid_list[userdict[uid]]['recommendations'].append(mid)
    print(mid_list[0].keys())
    pp = pprint.PrettyPrinter(depth=6)
    for i in range(len(mid_list)):
        print(len(mid_list[i]['recommendations']))
    return mid_list


def lambda_handler(event, context):
    if write_score():
        if read_state()[0] == 'END':
            write_state(['START', '', '', '', '', '', ''])
    update_recommendation()


