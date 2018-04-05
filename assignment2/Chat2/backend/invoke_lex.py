import boto3
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
client_run = boto3.client('lex-runtime',region_name='us-east-1')
client_model = boto3.client('lex-models',region_name='us-east-1')

def lambda_handler(event, context):
    msg = str(event['inputText'])
    response = client_run.post_text(
        botName='DiningChatBot',
        botAlias='DiningChat',
        userId='yy',
        inputText=str(msg)
    )
    bot_details = client_model.get_bot(
        name='DiningChatBot',
        versionOrAlias='$LATEST'
    )
    return response