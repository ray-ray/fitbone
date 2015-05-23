"""
Wrapper around UP APIs
"""
__author__ = 'rcourtney'


import keys
import requests_oauthlib


def timeseries():
    """
    upr = oauth.post('https://jawbone.com/nudge/api/v.1.2/timeseries', data={'data':'[{"type":"steps", "data": [[1431705600, 10],[1431705660, 50]]}]'})

    :return:
    """
    pass


def generic(fitbone_user, note):
    """
    Create a custom feed nugget.

    :param fitbone_user: User object
    :param note: body text
    :return: None
    """
    up_tokens = fitbone_user.up_tokens
    up_oauth = requests_oauthlib.OAuth2Session(keys.up_id, token=up_tokens)
    up_oauth.post(
        'https://jawbone.com/nudge/api/v.1.2/users/@me/generic_events',
        data={'verb': 'enqueued', 'title': 'A Message', 'note': note})