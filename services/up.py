"""
Wrapper around UP APIs
"""
__author__ = 'rcourtney'


import calendar
import datetime
import httplib
import json
import keys
import pytz
import requests_oauthlib
import services.fitbit
# import time


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
# awake -> awake
# really awake -> awake
#
value_to_depth = {'1': 3, '2': 1, '3': 1}


def to_unixtime(datestr, tzstr):
    """
    Convert YYYY-MM-DD HH:MM:SS to unix time

    :param datestr: YYYY-MM-DD HH:MM:SS
    :param tzstr: timezone string from Fitbit
    :return: unixtime
    """
    ptz = pytz.timezone(tzstr)
    dt = datetime.datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S')
    ldt = ptz.localize(dt)
    udt = ldt.astimezone(pytz.utc)
    return calendar.timegm(udt.timetuple())
    # return time.mktime(ldt.timetuple())
    # return time.mktime(datetime.datetime.strptime(
    #     datestr,
    #     '%Y-%m-%d %H:%M:%S').timetuple())


def make_sleep(fitbone_user, fitbit_sleep):
    """
    Create UP sleeps from Fitbit sleep data

    :param fitbone_user: User object
    :param fitbit_sleep: Fitbit sleep JSON
    :return: None
    """
    fitbit_profile = services.fitbit.get_profile(fitbone_user)
    timezone = fitbit_profile['user']['timezone']
    up_tokens = fitbone_user.up_tokens
    up_oauth = requests_oauthlib.OAuth2Session(keys.up_id, token=up_tokens)
    for sleep in fitbit_sleep['sleep']:
        #
        # Get the YYYY-MM-DD
        #
        datestr = sleep['startTime'][:10]
        tickdepth = None
        time_created = to_unixtime(
            '%s %s' % (datestr, sleep['minuteData'][0]['dateTime']),
            timezone)
        ticks = []
        ticktime = time_created

        #
        # Convert Fitbit's minute data to UP's phase change ticks.
        #
        for minute in sleep['minuteData']:
            depth = value_to_depth[minute['value']]
            if depth != tickdepth:
                ticks.append({
                    'time': ticktime,
                    'depth': depth})
                tickdepth = depth
            ticktime += 60
        time_completed = ticktime

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


def make_steps(fitbone_user, fitbit_steps):
    """
    Create UP steps from Fitbit step data. Fitbit only gives us 1 data point per
    day so all the steps will appear in up at noon.

    :param fitbone_user: User object
    :param fitbit_steps: Fitbit step JSON
    :return: None
    :raise StepCreationFailure: if UP doesn't return 200/201
    """
    fitbit_profile = services.fitbit.get_profile(fitbone_user)
    timezone = fitbit_profile['user']['timezone']

    up_tokens = fitbone_user.up_tokens
    up_oauth = requests_oauthlib.OAuth2Session(keys.up_id, token=up_tokens)

    #
    # Convert the Fitbit step data into UP timeseries data.
    #
    data = []
    for activity in fitbit_steps['activities-steps']:
        #
        # Since we only get one count per day, always put it at noon.
        #
        timestamp = to_unixtime('%s 12:00:00' % activity['dateTime'], timezone)
        data.append([timestamp, int(activity['value'])])

    #
    # Create the steps in UP.
    #
    upr = up_oauth.post(
        'https://jawbone.com/nudge/api/v.1.2/timeseries',
        data={'data': json.dumps([{'type': 'steps', 'data': data}])})
    if upr.status_code not in (httplib.OK, httplib.CREATED):
        raise StepCreationFailure('%s - %s' % (upr.status_code, upr.json()))


class GenericEventFailure(Exception):
    """
    Raise if UP generic_event API doesn't return a 201.
    """
    pass


class SleepCreationFailure(Exception):
    """
    Raise if UP sleep API doesn't return a 200/201.
    """
    pass


class StepCreationFailure(Exception):
    """
    Raise if UP timeseries API doesn't return a 200/201.
    """
    pass