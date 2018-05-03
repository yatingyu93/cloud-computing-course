import boto3
import math
import dateutil.parser
import datetime
import time
import os
import logging
import re
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return -1


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def isvalid_city(city):
    valid_cities = ['new york', 'brooklyn', 'manhattan', 'queens', 'bronx', 'staten island']
    return city.lower() in valid_cities


def validate_dining_info(cuisine_type, date, dining_time, num_people, email, city):
    cuisine_types = ['chinese', 'american', 'italian', 'indian', 'korean', 'japanese', 'french']
    if cuisine_type is not None and cuisine_type.lower() not in cuisine_types:
        return build_validation_result(False,
                                       'Cuisine',
                                       'We do not have {}, would you like a different type of cuisine? (Chinese, Italian, etc...)'
                                       .format(cuisine_type))
    istoday = False
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'I did not understand that, what date would you like to eat?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'Date', 'You can find information from today onwards. What day?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() == datetime.date.today():
            istoday = True

    if dining_time is not None:
        if len(dining_time) != 5:
            return build_validation_result(False, 'Time', None)
        hour, minute = dining_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        timenow = datetime.datetime.now().time()
        timedining = timenow.replace(hour, minute, 0, 0)
        if math.isnan(hour) or math.isnan(minute):
            return build_validation_result(False, 'Time', 'Sorry, what time?')

        if istoday and timedining <= timenow:
            return build_validation_result(False, 'Time', 'Invalid time. What time would you prefer?')

        if hour < 10 or hour > 22:
            # Outside of business hours
            return build_validation_result(False, 'Time', 'Restaurants may not open at this time. Can you specify another time?')

    if email is not None:
        if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
            return build_validation_result(False, 'Email', 'Sorry, could you please provide a valid email address?')

    if num_people is not None:
        if parse_int(num_people) < 1:
            return build_validation_result(False, 'NumberOfPeople', 'Sorry, how many?')

    if city is not None:
        if not isvalid_city(city):
            return build_validation_result(False, 'Location',
                                       'Sorry, location {} is not found, where would you like to dine in?'.format(city))

    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def suggest_dining(intent_request):

    cuisine_type = get_slots(intent_request)["Cuisine"]
    location = get_slots(intent_request)["Location"]
    date = get_slots(intent_request)["Date"]
    dining_time = get_slots(intent_request)["Time"]
    num_of_people = get_slots(intent_request)["NumberOfPeople"]
    email = get_slots(intent_request)["Email"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)

        validation_result = validate_dining_info(cuisine_type, date, dining_time, num_of_people, email, location)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        output_session_attributes['location'] = location
        output_session_attributes['cuisine'] = cuisine_type
        output_session_attributes['date'] = date
        output_session_attributes['time'] = dining_time
        output_session_attributes['numberOfPeople'] = num_of_people
        output_session_attributes['email'] = email
        return delegate(output_session_attributes, get_slots(intent_request))

    if source == 'FulfillmentCodeHook':
        sqs = boto3.resource('sqs')
        queue = sqs.Queue('https://sqs.us-east-1.amazonaws.com/795907756437/dining_queue')
        msgs = json.dumps(intent_request['sessionAttributes'])
        response = queue.send_message(MessageBody=msgs)

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'You\'re all set. Expect my recommendations shortly! Have a good day.'})


""" --- Intents --- """


def dispatch(intent_request):
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return suggest_dining(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
