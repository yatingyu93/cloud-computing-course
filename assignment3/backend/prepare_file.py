"""
 This code sample prepares files for machine learning.

 FILE_1.csv: all restaurant information (ID, Cuisine, Rating, NumberOfReviews)
 FILE_2.csv: recommended and not recommended restaurants information (ID, Cuisine, Rating, NumberOfReviews, Recommended)
 FILE_3.csv: all FILE_1 items with prediction column, predicted using Amazon Machine Learning
"""

import boto3
from datetime import datetime
from elasticsearch import helpers, Elasticsearch, RequestsHttpConnection
import csv
from requests_aws4auth import AWS4Auth


""" --- Helper to store items got from yelp query to DynamoDB --- """


def write_to_db():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp_restaurants')

    # write to db from separate csv (got from yelp query) file for each cuisine
    cuisine_types = ['chinese', 'american', 'italian', 'indian', 'korean', 'japanese', 'french']
    for cuisine in cuisine_types:
        cuisine_reader = csv.DictReader(open('./csv/{}.csv'.format(cuisine), 'r'))
        dict_list = []
        for item in cuisine_reader:
            ok = True
            if 'NY' not in item['address']:
                continue
            for key in item.keys():
                # filter out bad entries
                if item[key] == "":
                    ok = False
                    break
            if ok:
                dict_list.append(item)
        print('size of {} is {}'.format(cuisine, len(dict_list)))

        # write to db
        with table.batch_writer() as batch:
            for i in range(len(dict_list)):
                dict_list[i]['insertedAtTimestamp'] = str(datetime.now())
                dict_list[i]['cuisine'] = cuisine
                batch.put_item(Item=dict_list[i])

    # save ALL db data to local csv, local backup
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    print(len(data))

    keys = data[0].keys()
    with open('./csv/all.csv', 'w') as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)


""" --- Helper to write items to local file FILE1.csv with selected attributes --- """


def write_to_file(source_filename, dst_filename):
    file_reader = csv.DictReader(open(source_filename, 'r'))
    items = []
    for item_line in file_reader:
        item = {'RestaurantId': item_line['id'], 'Cuisine': item_line['cuisine'],
                'Rating': item_line['rating'], 'NumberOfReviews': item_line['review_count']}
        items.append(item)

    file_keys = items[0].keys()
    with open(dst_filename, 'w') as f:
        dict_writer = csv.DictWriter(f, file_keys)
        dict_writer.writeheader()
        dict_writer.writerows(items)


""" --- Helper to write selected items from FILE_1.csv to local file FILE2.csv --- """


def write_trainingdata(source_filename, filename1, filename2):
    restaurants_reader = csv.DictReader(open(source_filename, 'r'))
    liked_items = []
    dislike_items = []
    file1_items = []
    file2_items = []
    count1 = 0
    count2 = 0
    for line in restaurants_reader:
        if float(line['Rating']) >= 4.5 and int(line['NumberOfReviews']) >= 300 and count1 < 100:
            liked_item = {key: line[key] for key in ['RestaurantId', 'Cuisine', 'Rating', 'NumberOfReviews']}
            liked_item['Recommended'] = 1
            liked_items.append(liked_item)
            count1 += 1
        elif float(line['Rating']) <= 3.0 and int(line['NumberOfReviews']) >= 100 and count2 < 100:
            disliked_item = {key: line[key] for key in ['RestaurantId', 'Cuisine', 'Rating', 'NumberOfReviews']}
            disliked_item['Recommended'] = 0
            dislike_items.append(disliked_item)
            count2 += 1
        else:
            file1_item = {key: line[key] for key in ['RestaurantId', 'Cuisine', 'Rating', 'NumberOfReviews']}
            file1_items.append(file1_item)

    file2_items.extend(liked_items)
    file2_items.extend(dislike_items)

    # update FILE1 as FILE1 - FILE2
    file1_keys = file1_items[0].keys()
    with open(filename1, 'w') as f:
        dict_writer = csv.DictWriter(f, file1_keys)
        dict_writer.writeheader()
        dict_writer.writerows(file1_items)

    file2_keys = liked_items[0].keys()
    with open(filename2, 'w') as f:
        dict_writer = csv.DictWriter(f, file2_keys)
        dict_writer.writeheader()
        dict_writer.writerows(file2_items)


""" --- Helper to combine prediction with rows in FILE_1.csv, then write items to FILE_3.csv --- """


def write_prediction(source1, source2, dst_filename):
    rows_reader = csv.DictReader(open(source1, 'r'))
    prediction_reader = csv.DictReader(open(source2, 'r'))
    file3_items = []
    for rline in rows_reader:
        file3_items.append(rline)
    idx = 0
    for pline in prediction_reader:
        file3_items[idx]['Prediction'] = pline['bestAnswer']
        file3_items[idx]['Score'] = pline['score']
        idx += 1

    file3_keys = file3_items[0].keys()
    with open(dst_filename, 'w') as f:
        dict_writer = csv.DictWriter(f, file3_keys)
        dict_writer.writeheader()
        dict_writer.writerows(file3_items)


""" --- Helper to filter out items with recommended = 1, write them to elasticsearch and FILE_4.csv --- """


def write_to_es():
    file_reader = csv.DictReader(open('./csv/FILE_3.csv', 'r'))
    file4_items = []
    for l in file_reader:
        if l['Prediction'] == '1':
            file4_item = {key: l[key] for key in ['RestaurantId', 'Cuisine']}
            file4_item['Score'] = float(l['Score'])
            file4_items.append(file4_item)

    file4_keys = file4_items[0].keys()
    with open('./csv/FILE_4.csv', 'w') as f:
        dict_writer = csv.DictWriter(f, file4_keys)
        dict_writer.writeheader()
        dict_writer.writerows(file4_items)

    my_access_key = 'MY_ACCESS_KEY'
    my_secret_key = 'MY_SECRET_KEY'
    awsauth = AWS4Auth(my_access_key, my_secret_key, 'us-east-1', 'es')
    es = Elasticsearch(
        hosts='https://search-esdomain-27nrbtadyrelwj3jtbzrabuz54.us-east-1.es.amazonaws.com',
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    mapping = {
        "predictions": {
            "mappings": {
                "Prediction": {
                    "properties": {
                        "RestaurantID": {
                            "type": "string",
                        },
                        "Cuisine": {
                            "type": "string"
                        },
                        "Score": {
                            "type": "float"
                        }
                    }
                }
            }
        }
    }
    if es.indices.exists(index='predictions'):
        es.indices.delete(index='predictions')
    es.indices.create(index='predictions', ignore=400, body=mapping)
    helpers.bulk(es, file4_items, index='predictions', doc_type='Prediction')


if __name__ == '__main__':

    write_to_db()
    write_to_file('./csv/all.csv', './csv/FILE.csv')
    write_trainingdata('./csv/FILE.csv', './csv/FILE_1.csv', './csv/FILE_2.csv')
    write_prediction('./csv/FILE_1.csv', './csv/FILE_3_original.csv', './csv/FILE_3.csv')
    write_to_es()







