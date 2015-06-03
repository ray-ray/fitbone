"""
Wrapper around UP APIs
"""
__author__ = 'rcourtney'


import datetime
import httplib
import json
import keys
import requests_oauthlib
import time


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
    upr = up_oauth.post(
        'https://jawbone.com/nudge/api/v.1.2/users/@me/generic_events',
        data={'verb': 'enqueued', 'title': 'A Message', 'note': note})
    if upr.status_code != httplib.CREATED:
        raise GenericEventFailure('%s - %s' % (upr.status_code, upr.json()))


#
# Translate Fitbit sleep values to UP sleep depth
# asleep -> sound
# awake -> light
# really awake -> awake
#
value_to_depth = {'1': 3, '2': 2, '3': 1}


def to_unixtime(datestr):
    """
    Convert YYYY-MM-DD HH:MM:SS to unix time

    :param datestr: YYYY-MM-DD HH:MM:SS
    :return: unixtime
    """
    return time.mktime(datetime.datetime.strptime(
        datestr,
        '%Y-%m-%d %H:%M:%S').timetuple())


def make_sleep(fitbone_user, fitbit_sleep):
    """
    Create UP sleeps from Fitbone sleep data

    :param fitbone_user: User object
    :param fitbit_sleep: Fitbit sleep JSON
    :return: None
    """
    up_tokens = fitbone_user.up_tokens
    up_oauth = requests_oauthlib.OAuth2Session(keys.up_id, token=up_tokens)
    for sleep in fitbit_sleep['sleep']:
        #
        # Get the YYYY-MM-DD
        #
        datestr = sleep['startTime'][:10]
        tickdepth = None
        time_created = to_unixtime(
            '%s %s' % (datestr, sleep['minuteData'][0]['dateTime']))
        time_completed = to_unixtime(
            '%s %s' % (datestr, sleep['minuteData'][-1]['dateTime'])) + 60
        ticks = []

        #
        # Convert Fitbit's minute data to UP's phase change ticks.
        #
        for minute in sleep['minuteData']:
            depth = value_to_depth[minute['value']]
            if depth != tickdepth:
                ticks.append({
                    'time': to_unixtime('%s %s' % (
                        datestr,
                        minute['dateTime'])),
                    'depth': depth})
                tickdepth = depth

        #
        # Create the UP sleep.
        #
        upr = up_oauth.post(
            'https://jawbone.com/nudge/api/v.1.3/users/@me/sleeps',
            data={
                'time_created': time_created,
                'time_completed': time_completed,
                'ticks': json.dumps(ticks)})
        if upr.status_code not in (httplib.OK, httplib.CREATED):
            raise SleepCreationFailure(
                '%s - %s' % (upr.status_code, upr.json()))


class GenericEventFailure(Exception):
    """
    Raise if UP generic_event API doesn't return a 201.
    """
    pass


class SleepCreationFailure(Exception):
    """
    Raise if UP
    """
    pass