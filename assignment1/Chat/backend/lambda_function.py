import json
import random
from datetime import datetime
import re
hello_values = ['Hello there, how can I help?',
                'Hello, good to see you.',
                'Hello! How are you today',
                'Hi there.']
bye_values = ['Bye, have a nice day!',
              'See you!',
              'Goodbye.',
              'Thanks, bye.']

weather_values = ["It's sunny.",
                  "It's raining outside, don't forget to take your umbrella.",
                  "Strong wind, please be careful when walking outside."]

welcome_values = ['You\'re welcome',
                  'Anytime!',
                  'Happy to help.']


def lambda_handler(event, context):
    msg = str(event['message'])
    rsp = dict()
    timenow = str(datetime.now())
    if re.compile(r'\bhi\b|\bhello\b|\bhey\b').search(msg):
        rsp['responseMsg'] = {'id': timenow, 'text': random.SystemRandom().choice(hello_values), 'timestamp': timenow}
    elif re.compile(r'\bgoodbye\b|\bbye\b').search(msg):
        rsp['responseMsg'] = {'id': timenow, 'text': random.SystemRandom().choice(bye_values), 'timestamp': timenow}
    elif re.compile(r'\bthanks\b|\bthank you\b').search(msg):
        rsp['responseMsg'] = {'id': timenow, 'text': random.SystemRandom().choice(welcome_values), 'timestamp': timenow}
    elif re.compile(r'\bweather\b').search(msg):
        rsp['responseMsg'] = {'id': timenow, 'text': random.SystemRandom().choice(weather_values), 'timestamp': timenow}
    elif re.compile(r'\bgood\b|\bok\b|\bfine\b').search(msg):
        rsp['responseMsg'] = {'id': timenow, 'text': 'Anything else I can help?', 'timestamp': timenow}
    else:
        rsp['responseMsg'] = {'id': timenow, 'text': "Sorry, I don't understand. Is there anything else I can help?",
                              'timestamp': timenow}

    return json.dumps(rsp)
    
