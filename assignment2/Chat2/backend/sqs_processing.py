import boto3
import json
from botocore.vendored import requests
import urllib.parse
from dateutil import parser

API_KEY = 'YOUR_API_KEY'
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'

DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'New York, NY'
SEARCH_LIMIT = 3


def request(host, path, api_key, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, urllib.parse.quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()


def search(api_key, term, location, time):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT,
        'open_at': time
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)


def get_business(api_key, business_id):
    business_path = BUSINESS_PATH + business_id
    return request(API_HOST, business_path, api_key)


def query_api(term, location, time):
    response = search(API_KEY, term, location, time)
    businesses = response.get('businesses')
    res = []
    if not businesses:
        print(u'No restaurant for {} at {} found.'.format(term, location))
        return res

    for business in businesses:
        rsp = get_business(API_KEY, business['id'])
        print(rsp['url'])
        info = {'name': rsp['name'],
                'address': rsp['location']['display_address'][0] + ', ' + rsp['location']['display_address'][1]}
        res.append(info)
    return res


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


def lambda_handler(event, context):
    sqs = boto3.resource('sqs', region_name='us-east-1')
    queue = sqs.Queue('https://sqs.us-east-1.amazonaws.com/795907756437/dining_queue')
    for message in queue.receive_messages(MaxNumberOfMessages=10):
        msg = json.loads(message.body)
        location = msg['location']
        cuisine = msg['cuisine']
        date = msg['date']
        time = msg['time']
        numberOfPeople = msg['numberOfPeople']
        email = msg['email']
        dtint = int(parser.parse(date + ' ' + time).timestamp())

        results = query_api(cuisine, location, dtint)
        text = ''
        for res in results:
            text += '{}, located at {}\n'.format(res['name'], res['address'])

        if results.__len__() > 0:
            text = 'Hello! Here are my {} restaurant suggestions for {} people on {} at {}:\n' \
                       .format(cuisine, numberOfPeople, date, time) + text
            text += 'Enjoy!\n'
        else:
            text = 'Sorry, no {} restaurant found in {} on {} at {}'.format(cuisine, location, date, time)

        arn = send_sns(text, email)
        if arn is not None:
            message.delete()


