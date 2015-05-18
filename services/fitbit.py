"""
Wrapper around Fitbit APIs
"""
__author__ = 'rcourtney'


import keys
import requests_oauthlib


def subscribe(fitbone_user):
    """
    Subscribe to a fitbit user's pubsub

    :param fitbone_user:
    :return:
    """
    fitbit_tokens = fitbone_user.fitbit_tokens
    fitbit_oauth = requests_oauthlib.OAuth1Session(
        keys.fitbit_key,
        keys.fitbit_secret,
        resource_owner_key=fitbit_tokens['oauth_token'],
        resource_owner_secret=fitbit_tokens['oauth_token_secret'])
    fbr = fitbit_oauth.post(
        'https://api.fitbit.com/1/user/-/apiSubscriptions/1.json')
    return '%s<br>%s' % (fbr.status_code, fbr.json())
