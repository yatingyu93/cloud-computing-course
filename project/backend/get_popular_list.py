from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests
import json
import decimal

DEFAULT_POSTER = 'https://s3.amazonaws.com/cloud-computing-project-bucket/frontend/assets/img/m.jpg'

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def conv_genre(genre_ids):
    """
    convert genre_ids to specific genres
    """
    genres = []
    genre_dict = {28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", \
    36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 10770: "TV Movie", 53:"Thriller", 10752: "War", 37: "Western"}
    for i in range(0,len(genre_ids)):
        if genre_ids[i] in genre_dict:
            genres.append(genre_dict[genre_ids[i]])
    return genres


def get_popular_list(num):
    """Get popular movie list by query tmdb

        Args:
            num: number of returns.
        Returns:
            a list of dict object contains all movies' information.

    """
    mlist = []
    for i in range(1, 26):
        url = 'https://api.themoviedb.org/3/movie/popular?api_key=130ed33ec6dcb86fd1af9e8fc6172be0&language=en-US&page=' + str(i)
        response = requests.get(url, verify=True)
        data = response.json()
        d = data['results']
        for i in range(0, len(d)):
            if len(d[i]) == 0:
                continue
            tmdb_id = str(d[i]['id'])
            title = d[i]['title']
            rating = d[i]['vote_average']
            release_date = d[i]['release_date']
            genres_list = conv_genre(d[i]['genre_ids'])
            genres = ' | '.join(str(x) for x in genres_list)
            overview = d[i]['overview']
            if d[i]['poster_path'] == None:
                poster = DEFAULT_POSTER
            else:
                poster = 'https://image.tmdb.org/t/p/w342' + d[i]['poster_path']
            mlist.append({'mid': tmdb_id, 'title': title, 'rating': rating, 'release_date': release_date, 'genres': genres, 'overview': overview, 'poster': poster})
            if len(mlist) >= num:
                return mlist


def update_initial_list(uid):
    """Update initial recommendation list for newly created user

        Args:
            uid: user id.
        Returns:
            True/False.
        Raises:
            ClientError: if query DB fails.

    """
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('recommendation')

    mlist = get_popular_list(50)
    mids = [mid['mid'] for mid in mlist]
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
        print(mids)
    return True

    
def lambda_handler(event, context):
    uid = 'initial_user'
    return update_initial_list(uid)
