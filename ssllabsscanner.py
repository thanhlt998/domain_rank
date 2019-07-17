import requests
import time
import sys
import logging

# API = 'https://api.ssllabs.com/api/v2/'
API = 'https://api.ssllabs.com/api/v3/'


def request_api(path, payload={}):
    """
    This is a helper method that takes the path to the relevant
    API call and the user-defined payload and requests the
    data/server test from Qualys SSL Labs.

    Returns JSON formatted data
    """
    url = API + path

    try:
        response = requests.get(url, params=payload)
    except requests.exception.RequestException:
        logging.exception('Request failed.')

    data = response.json()
    return data


def results_from_cache(host, publish='off', startNew='off', fromCache='on', all='done'):
    path = 'analyze'
    payload = {
        'host': host,
        'publish': publish,
        'startNew': startNew,
        'fromCache': fromCache,
        'all': all
    }
    data = request_api(path, payload)
    return data


def new_scan(host, publish='off', startNew='on', all='done', ignoreMismatch='on'):
    path = 'analyze'
    payload = {
        'host': host,
        'publish': publish,
        'startNew': startNew,
        'all': all,
        'ignoreMismatch': ignoreMismatch
    }
    results = request_api(path, payload)

    payload.pop('startNew')

    while results['status'] != 'READY' and results['status'] != 'ERROR':
        time.sleep(30)
        results = request_api(path, payload)

    return results


if __name__ == '__main__':
    result = new_scan('xaydunghoanganh.com')
    print(result)
