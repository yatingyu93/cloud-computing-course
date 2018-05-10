from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
import json
import decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def create_item(uid, mid):
    """Create initial attitude item when user clicked on a new movie.

        Args:
            uid: user id.
            mid: movie id.
        Returns:
            a list ['create', True/False].
        Raises:
            ClientError: if query DB fails.

    """
    table = dynamodb.Table('score')
    try:
        response = table.get_item(Key={'uid': uid, 'mid': mid})
    except ClientError as e:
        print(e.response['Error']['Message'])
        return ['create', False]
    else:
        if 'Item' not in response:
            response = table.put_item(Item={'uid': uid, 'mid': mid, 'attitude': 0, 'wishlist': 0, 'score': 3})
    return ['create', True]


def get_attitude(uid, mid):
    """Get an attitude item.

        Args:
            uid: user id.
            mid: movie id
        Returns:
            a list of user's attitude to a certain movie.
        Raises:
            ClientError: if query DB fails.

    """
    table = dynamodb.Table('score')
    res = []
    try:
        response = table.get_item(Key={'uid': uid, 'mid': mid})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        ld = response['Item']['attitude']
        wl = response['Item']['wishlist']
        score = response['Item']['score']
        res = [ld, wl, score]
    return res


def recompute(ld, wl, score):
    """Recompute score.

        Args:
            ld:  -1/0/1, stands for dislike, no attitude, or like.
            wl: 0/1, stands for in wishlist, not in wishlist.
            score: 0/3/6/10, describe user's attitude of a certain movie.
        Returns:
            a recomputed score of type int
        Raises:
            ClientError: if updateDB DB fails.

    """
    if ld == -1:
        return 0
    elif ld == 0 and wl == 0:
        return 3
    elif ld == 0 and wl == 1:
        return 6
    elif ld == 1:
        return 10
    else:
        return score


def update_likedislike_in_score(uid, mid, ld):
    """Update like/dislike and score attributes in table.

        Args:
            uid: user id.
            mid: movie id
            ld: -1, 0, or 1 stands for dislike, no attitude, or like
        Returns:
            a list ['updateld', True/Fale].
        Raises:
            ClientError: if update DB fails.

    """
    table = dynamodb.Table('score')

    [_, wl, score] = get_attitude(uid, mid)
    new_score = recompute(ld, wl, score)
    print('ns:' + str(new_score))
    try:
        response = table.update_item(
            Key={'uid': uid, 'mid': mid},
            UpdateExpression="set attitude=:val, score=:s",
            ExpressionAttributeValues={
                ':val': ld,
                ':s': new_score
            },
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
        return ['updateld', False]
    else:
        print("UpdateItem succeeded:")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))
    return ['updateld', True]


def update_wishlist_in_score(uid, mid, wl):
    """Update wishlist and score attributes in table

        Args:
            uid: user id.
            mid: movie id
            wl: 0 or 1 stands for in wishlist, not in wishlist.
        Returns:
            a list ['updatewl', True/Fale].
        Raises:
            ClientError: if update DB fails.

    """
    table = dynamodb.Table('score')

    [ld, _, score] = get_attitude(uid, mid)
    new_score = recompute(ld, wl, score)
    try:
        response = table.update_item(
            Key={'uid': uid, 'mid': mid},
            UpdateExpression="set wishlist=:val, score=:s",
            ExpressionAttributeValues={':val': wl, ':s': new_score},
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
        return ['updatewl', False]
    else:
        print("UpdateItem succeeded:")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))
    return ['updatewl', True]


def lambda_handler(event, context):
    func = event['f']
    uid = event['uid']
    mid = event['mid']
    if func == 'get':
        return get_attitude(uid, mid)
    elif func == 'updateld':
        return update_likedislike_in_score(uid, mid, event['ld'])
    elif func == 'updatewl':
        return update_wishlist_in_score(uid, mid, event['wl'])
    elif func == 'create':
        return create_item(uid, mid)
    return -1

