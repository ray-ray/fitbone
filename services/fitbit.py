"""
Wrapper around Fitbit APIs
"""
__author__ = 'rcourtney'


import httplib
import keys
import requests_oauthlib


def subscribe(fitbone_user):
    """
    Subscribe to a fitbit user's pubsub
    https://wiki.fitbit.com/display/API/Fitbit+Subscriptions+API

    :param fitbone_user: User object
    :return: None
    """
    fitbit_tokens = fitbone_user.fitbit_tokens
    fitbit_oauth = requests_oauthlib.OAuth1Session(
        keys.fitbit_key,
        keys.fitbit_secret,
        resource_owner_key=fitbit_tokens['oauth_token'],
        resource_owner_secret=fitbit_tokens['oauth_token_secret'])
    fbr = fitbit_oauth.post(
        'https://api.fitbit.com/1/user/-/apiSubscriptions/1.json')

    #
    # Make sure subscription succeeds.
    #
    if fbr.status_code not in (httplib.OK, httplib.CREATED):
        raise SubscriptionFailure('%s - %s' % (fbr.status_code, fbr.json()))


def get_sleep(fitbone_user, day):
    """
    Get the fitbit sleep data for a given day.
    https://wiki.fitbit.com/display/API/API-Get-Sleep

    :param fitbone_user: User object
    :param day: YYYY-MM-DD
    :return: Sleep JSON
    """
    fitbit_tokens = fitbone_user.fitbit_tokens
    fitbit_oauth = requests_oauthlib.OAuth1Session(
        keys.fitbit_key,
        keys.fitbit_secret,
        resource_owner_key=fitbit_tokens['oauth_token'],
        resource_owner_secret=fitbit_tokens['oauth_token_secret'])
    fbr = fitbit_oauth.get(
        'https://api.fitbit.com/1/user/-/sleep/date/%s.json' % day)
    if fbr.status_code == httplib.OK:
        return fbr.json()
    else:
        raise SleepFailure('%s - %s' % (fbr.status_code, fbr.json()))


def get_steps(fitbone_user, day):
    """
    Get the fitbit step count for a given day.
    https://wiki.fitbit.com/display/API/API-Get-Time-Series

    :param fitbone_user: User objevct
    :param day: YYYY-MM-DD
    :return: Step JSON
    :raise StepsFailure: non-200 response from Fitbit
    """
    fitbit_tokens = fitbone_user.fitbit_tokens
    fitbit_oauth = requests_oauthlib.OAuth1Session(
        keys.fitbit_key,
        keys.fitbit_secret,
        resource_owner_key=fitbit_tokens['oauth_token'],
        resource_owner_secret=fitbit_tokens['oauth_token_secret'])
    fbr = fitbit_oauth.get(
        'https://api.fitbit.com/1/user/-/activities/steps/date/%s/1d.json' % day
    )
    if fbr.status_code == httplib.OK:
        return fbr.json()
    else:
        raise StepsFailure('%s - %s' % (fbr.status_code, fbr.json))


class SubscriptionFailure(Exception):
    """
    Raise this if Fitbit's subscription API doesn't return a 200/201.
    """
    pass


class SleepFailure(Exception):
    """
    Raise this if Fitbit's sleep API doesn't return a 200.
    """
    pass


class StepsFailure(Exception):
    """
    Raise this if Fitbit's timeseries API doesn't return a 200.
    """
    pass