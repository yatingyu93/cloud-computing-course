from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests
import json
import decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
DEFAULT_POSTER = 'https://s3.amazonaws.com/cloud-computing-project-bucket/frontend/assets/img/m.jpg'

def conv_genre(genre_ids):
    """
    convert genre_ids to specific genres
    """
    genres = []
    genre_dict = {28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary",
                  18: "Drama", 10751: "Family", 14: "Fantasy",
                  36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance",
                  878: "Science Fiction", 10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"}
    for i in range(0, len(genre_ids)):
        if genre_ids[i] in genre_dict:
            genres.append(genre_dict[genre_ids[i]])
    return genres


def query_by_tmdbid(tmdb_id):
    """Get movie detail by movie id from tmdb query.

        Args:
            tmdb_id: movie id.
        Returns:
            a dict object contains movie detail.

    """
    url = 'https://api.themoviedb.org/3/movie/' + tmdb_id + '?api_key=130ed33ec6dcb86fd1af9e8fc6172be0&language=en-US'
    response = requests.get(url, verify=True)
    d = response.json()
    imdb_id = d['imdb_id']
    title = d['title']
    rating = d['vote_average']
    release_date = d['release_date']
    overview = d['overview']
    genres_list = d['genres']
    tmp = []
    for i in range(len(genres_list)):
        tmp.append(genres_list[i]['name'])
    genres = " | ".join(x for x in tmp[:3])

    if d['poster_path'] == None:
        poster = DEFAULT_POSTER
    else: poster = 'https://image.tmdb.org/t/p/w342' + d['poster_path']

    res = {'mid': tmdb_id, 'title': title, 'rating': rating, 'release_date': release_date, 'genres': genres,
           'overview': overview, 'poster': poster}
    return res


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def create_item(uid):
    """Create initial wishlist item when user clicked on wishlist.

        Args:
            uid: user id.
        Returns:
            a list ['create', True/False].
        Raises:
            ClientError: if query DB fails.

    """
    table = dynamodb.Table('wishlist')
    try:
        response = table.get_item(Key={'uid': uid})
    except ClientError as e:
        print(e.response['Error']['Message'])
        return ['create', False]
    else:
        if 'Item' not in response:
            response = table.put_item(Item={'uid': uid, 'wishlist': []})
    return ['create', True]


def get_wishlist_detail(uid):
    """Get wishlist detail information.

        Args:
            uid: user id.
        Returns:
            a list of dict objects that contain movies' information.

    """
    table = dynamodb.Table('wishlist')
    movie_detail_list = []

    try:
        response = table.get_item(Key={'uid': uid})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        mids = response['Item']['wishlist']
        movie_detail_list = []
        for idx in range(len(mids)):
            detail = query_by_tmdbid(mids[idx])
            if len(detail) > 0:
                movie_detail_list.append(detail)

    return movie_detail_list


def get_movie_detail(mid):
    """Get movie detail by movie id from tmdb query.

        Args:
            mid: movie id.
        Returns:
            a dict object contains movie detail.

    """
    return query_by_tmdbid(mid)


def get_wishlist_mids(uid):
    """Get movies' ids in wishlist

        Args:
            uid: user id.
        Returns:
            a lsit of dict object contains movies' ids.

    """
    table = dynamodb.Table('wishlist')
    mids = []
    try:
        response = table.get_item(Key={'uid': uid})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        if 'Item' in response:
            mids = response['Item']['wishlist']
    return mids


def add_to_wishlist(uid, mid):
    """Add movie to wishlist.

        Args:
            uid: user id.
            mid: movie id
        Returns:
            a list ['add', True/Fale].
        Raises:
            ClientError: if update DB fails.

    """
    wl = get_wishlist_mids(uid)
    idx = len(wl)
    table = dynamodb.Table('wishlist')

    try:
        response = table.update_item(
            Key={'uid': uid},
            UpdateExpression="set wishlist[" + str(idx) + "]=:val",
            ExpressionAttributeValues={':val': mid},
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
        return ['add', False]
    else:
        print("UpdateItem succeeded:")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))
    return ['add', True]


def delete_from_wishlist(uid, mid):
    """Delete a movie from wishlist.

        Args:
            uid: user id.
            mid: movie id.
        Returns:
            a list ['delete', True/Fale].
        Raises:
            ClientError: if update DB fails.

    """
    idx = -1
    wl = get_wishlist_mids(uid)
    for i in range(len(wl)):
        if wl[i] == mid:
            idx = i
    print('found idx: {}'.format(idx))

    table = dynamodb.Table('wishlist')
    try:
        response = table.update_item(
            Key={'uid': uid},
            UpdateExpression="remove wishlist[" + str(idx) + "]",
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
        return ['delete', False]
    else:
        print("UpdateItem succeeded:")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))
    return ['delete', True]


def lambda_handler(event, context):
    func = event['f']
    uid = event['uid']
    if func == 'get':
        return get_wishlist_detail(uid)
    elif func == 'add':
        return add_to_wishlist(uid, event['mid'])
    elif func == 'delete':
        return delete_from_wishlist(uid, event['mid'])
    elif func == 'create':
        return create_item(uid)
    return -1

