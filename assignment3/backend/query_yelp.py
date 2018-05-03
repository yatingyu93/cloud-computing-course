import csv
from botocore.vendored import requests
import urllib.parse
API_KEY = "MY_API_KEY"
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'

DEFAULT_LOCATION = 'New York, NY'
SEARCH_LIMIT = 50
NUM_OF_ITERATIONS = 20


""" --- Helpers to query from yelp fusion API and save to local csv file --- """


def request(host, path, api_key, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, urllib.parse.quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()


def search(api_key, term, offset):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': DEFAULT_LOCATION.replace(' ', '+'),
        'limit': SEARCH_LIMIT,
        'offset': offset
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)


def get_business(api_key, business_id):
    business_path = BUSINESS_PATH + business_id
    return request(API_HOST, business_path, api_key)


def query_api(term, offset, res):
    response = search(API_KEY, term, offset)
    businesses = response.get('businesses')

    if not businesses:
        print(u'No restaurant for {} at {} found.'.format(term, DEFAULT_LOCATION))
        return 0

    for business in businesses:
        rsp = get_business(API_KEY, business['id'])
        info = {'id': rsp['id'],
                'name': rsp['name'],
                'address': ', '.join(rsp['location']['display_address']),
                'latitude': str(rsp['coordinates']['latitude']),
                'longitude': str(rsp['coordinates']['longitude']),
                'review_count': rsp['review_count'],
                'rating': str(rsp['rating']),
                'zipcode': rsp['location']['zip_code']}
        res.append(info)
    return len(res)


if __name__ == '__main__':

    cuisine_types = ['french', 'chinese', 'american', 'italian', 'indian', 'korean', 'japanese']
    query_results = []
    for cuisine in cuisine_types:
        print(cuisine)
        for iter_i in range(NUM_OF_ITERATIONS):
            nums_of_res = query_api(cuisine, iter_i * SEARCH_LIMIT, query_results)
            print(nums_of_res)

        print('count: {}'.format(len(query_results)))

        keys = query_results[0].keys()
        with open('./csv/{}.csv'.format(cuisine), 'w') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(query_results)
        query_results = []

    print('Query done')



