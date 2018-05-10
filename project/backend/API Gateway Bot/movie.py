from __future__ import print_function
import boto3
import json
import decimal
import random
from botocore.exceptions import ClientError
from botocore.vendored import requests


dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
DEFAULT_POSTER = ''

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
    genre_dict = {28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary",
                  18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
                  9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 10770: "TV Movie", 53: "Thriller",
                  10752: "War", 37: "Western"}
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
    genres = " | ".join(x for x in tmp)

    if d['poster_path'] == None:
        poster = DEFAULT_POSTER
    else: poster = 'https://image.tmdb.org/t/p/w342' + d['poster_path']

    res = {'mid': tmdb_id, 'title': title, 'rating': rating, 'release_date': release_date, 'genres': genres,
           'overview': overview, 'poster': poster}
    return res


def get_movie_detail(mid):
    """Get movie detail information.

        Args:
            mid: movie id.
        Returns:
            a dict object contains movie detail.

    """
    detail_res = query_by_tmdbid(mid)
    return detail_res


def search_by_title(mtitle):
    """return movie detail by searching related movie title filter the movie of which vote_count below 500

        Args:
            mtitle: search keyword.
        Returns:
            a list of dict object contains all movies' information.

    """
    movie_search_list = []
    url = 'https://api.themoviedb.org/3/search/movie?api_key=130ed33ec6dcb86fd1af9e8fc6172be0&language=en-US&query=' + mtitle + '&page=1&include_adult=false&output=json'
    response = requests.get(url, verify=True)
    data = response.json()
    d = data['results']
    for i in range(0, len(d)):
        if d[i]['vote_count'] < 500:
            continue
        tmdb_id = str(d[i]['id'])
        res = query_by_tmdbid(tmdb_id)
        if len(res) > 0:
            movie_search_list.append(res)
    return movie_search_list


def create_item(uid):
    """Create initial recommendation list for newly signed user.

        Args:
            uid: user id.
        Returns:
            a list ['create', True/False].
        Raises:
            ClientError: if query DB fails.

    """
    table = dynamodb.Table('recommendation')
    try:
        response = table.get_item(Key={'uid': uid})
    except ClientError as e:
        print(e.response['Error']['Message'])
        return ['create', False]
    else:
        if 'Item' not in response:
            rsp = table.get_item(Key={'uid': 'initial_user'})
            response = table.put_item(Item={'uid': uid, 'recommendations': rsp['Item']['recommendations']})
    return ['create', True]


def get_recommendations(uid, indices, n, offset):
    """Get recommendation list for a user.

        Args:
            uid: user id.
            indices: a random list of index for the recommendation list
            n: number of movie ids to return
            offset: start position of the recommendation list
        Returns:
            a list of recommendation movies.
        Raises:
            ClientError: if query DB fails.

    """
    table = dynamodb.Table('recommendation')
    movie_detail_list = []

    try:
        response = table.get_item(Key={'uid': uid})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        mids = response['Item']['recommendations']

        movie_detail_list = []
        for idx in range(offset, offset + n):
            ridx = indices[idx]
            detail = get_movie_detail(mids[ridx])
            if len(detail) > 0:
                movie_detail_list.append(detail)

    return movie_detail_list


def lambda_handler(event, context):
    func = event['f']
    if func == 'create':
        uid = event['uid']
        return create_item(uid)
    elif func == 'getmoviedetail':
        mid = event['mid']
        return get_movie_detail(mid)
    elif func == 'getrecommendations':
        uid = event['uid']
        return get_recommendations(uid, event['indices'], event['n'], event['offset'])
    elif func == 'search':
        keyword = event['keyword']
        return search_by_title(keyword)
    return False





