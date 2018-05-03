import boto3
import json
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


def is_subscribed(email, arn):
    client = boto3.client('sns', region_name='us-east-1')
    for sub in client.list_subscriptions_by_topic(TopicArn=arn)["Subscriptions"]:
        if email == sub["Endpoint"]:
            if sub["SubscriptionArn"] != 'PendingConfirmation' and sub["SubscriptionArn"] != 'Deleted':
                return True, sub["SubscriptionArn"]
    return False, None


def send_sns(text, email):
    client = boto3.client('sns', region_name='us-east-1')
    arn = 'arn:aws:sns:us-east-1:795907756437:RestaurantNotification'

    has_sub, sub_arn = is_subscribed(email, arn)
    if not has_sub:
        sub_arn = client.subscribe(TopicArn=arn, Protocol='email', Endpoint=email)

    subscription_confirmed = False
    while not subscription_confirmed:
        has_sub, sub_arn = is_subscribed(email, arn)
        if has_sub:
            subscription_confirmed = True

    response = client.publish(
        TargetArn=sub_arn,
        Message=text,
        Subject='Restaurant Suggestions')
    return sub_arn


def search_es(cuisine):

    MY_ACCESS_KEY = 'MY_ACCESS_KEY'
    MY_SECRET_KEY = 'MY_SECRET_KEY'
    awsauth = AWS4Auth(MY_ACCESS_KEY, MY_SECRET_KEY, 'us-east-1', 'es')
    host = 'https://search-esdomain-27nrbtadyrelwj3jtbzrabuz54.us-east-1.es.amazonaws.com'
    es = Elasticsearch(
        hosts=host,
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    search_results = es.search(
        index='predictions',
        doc_type=['Prediction'],
        body={
            'query': {'term': {'Cuisine': cuisine}},
            'sort': [{'Score': {'order': 'desc'}}],
            'size': 5
        }
    )
    res = []
    for hit in search_results['hits']['hits']:
        hit_item = hit['_source']
        print("id: {}, cuisine: {}, score: {}".format(hit_item['RestaurantId'], hit_item['Cuisine'], hit_item['Score']))
        res.append({'RestaurantId': hit_item['RestaurantId']})
    return res


def lambda_handler(event, context):
    sqs = boto3.resource('sqs', region_name='us-east-1')
    queue = sqs.Queue('https://sqs.us-east-1.amazonaws.com/795907756437/dining_queue')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp_restaurants')

    for message in queue.receive_messages(MaxNumberOfMessages=10):
        msg = json.loads(message.body)
        location = msg['location']
        cuisine = msg['cuisine']
        date = msg['date']
        time = msg['time']
        numberOfPeople = msg['numberOfPeople']
        email = msg['email']

        search_results = search_es(cuisine.lower())
        text = ''
        for search_res in search_results:
            rsp = table.get_item(Key={'id': search_res['RestaurantId']})
            text += '{}, located at {}\n'.format(rsp['Item']['name'], rsp['Item']['address'])

        if search_results.__len__() > 0:
            text = 'Hello! Here are my {} restaurant suggestions for {} people on {} at {}:\n' \
                       .format(cuisine, numberOfPeople, date, time) + text
            text += 'Enjoy!\n'
        else:
            text = 'Sorry, no {} restaurant found in {} on {} at {}'.format(cuisine, location, date, time)

        arn = send_sns(text, email)
        if arn is not None:
            message.delete()

