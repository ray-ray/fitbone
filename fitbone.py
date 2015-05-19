"""
Flask app to connect Fitbit to UP.
"""
__author__ = 'rcourtney'

import boto.sqs
import boto.sqs.jsonmessage
import datetime
import flask
import flask.ext.sqlalchemy
import httplib
import keys
import os.path
import requests_oauthlib
import services.fitbit
import time

#
# AWS EB is dumB
#
application = flask.Flask(__name__)
app = application
app.config['SQLALCHEMY_DATABASE_URI'] = keys.SQLALCHEMY_DATABASE_URI
app.secret_key = keys.secret_key
db = flask.ext.sqlalchemy.SQLAlchemy(app)


#
# db must exist before these imports.
#
import services.user

#
# Connect to the SQS queue
#
# conn = boto.sqs.connect_to_region(
#     "us-west-1")
# q = conn.create_queue('fitbonetest')


FITBIT = {
    'client_key': keys.fitbit_key,
    'client_secret': keys.fitbit_secret,
    'request_token_url': 'https://api.fitbit.com/oauth/request_token',
    'base_authorization_url': 'https://www.fitbit.com/oauth/authorize',
    'access_token_url': 'https://api.fitbit.com/oauth/access_token'
}
UP = {
    'client_id': keys.up_id,
    'client_secret': keys.up_secret,
    'redirect_uri': 'http://fitbone.elasticbeanstalk.com/up_authorized',
    'scope': ['move_write', 'sleep_write'],
    'authorization_url': 'https://jawbone.com/auth/oauth2/auth',
    'request_token_url': 'https://jawbone.com/auth/oauth2/token'
}


@app.route('/fitbit_login')
def fitbit_login():
    """
    Get temp tokens and redirect to Fitbit login screen for app approval.

    :return: Flask redirect response
    """
    oauth = requests_oauthlib.OAuth1Session(
        FITBIT['client_key'],
        client_secret=FITBIT['client_secret'])
    fetch_response = oauth.fetch_request_token(FITBIT['request_token_url'])

    #
    # Store the temp tokens
    #
    temp_user = services.user.create_temp_user(fetch_response)
    flask.session['uid'] = temp_user.id

    #
    # Redirect to fitbit login
    #
    base_authorization_url = FITBIT['base_authorization_url']
    authorization_url = oauth.authorization_url(base_authorization_url)
    return flask.redirect(authorization_url)


@app.route('/fitbit_authorized')
def fitbit_authorized():
    """
    Callback from Fitbit to finish the oauth handshake

    :return: Print out keys for now
    """
    uid = flask.session['uid']
    temp_user = services.user.get_user(uid)
    temp_tokens = temp_user.fitbit_tokens
    verifier = flask.request.args.get('oauth_verifier')

    #
    # Finish the handshake with the verifier and the temp tokens.
    #
    oauth = requests_oauthlib.OAuth1Session(
        FITBIT['client_key'],
        client_secret=FITBIT['client_secret'],
        resource_owner_key=temp_tokens['oauth_token'],
        resource_owner_secret=temp_tokens['oauth_token_secret'],
        verifier=verifier)
    oauth_tokens = oauth.fetch_access_token(FITBIT['access_token_url'])

    #
    # Update the user record with the permanent Fitbit tokens and id. Re-set the
    # session uid in case we were updating a pre-existing user. Then start the
    # UP oauth flow.
    #
    fitbit_user = services.user.update_fitbit_creds(
        temp_user,
        oauth_tokens)
    flask.session['uid'] = fitbit_user.id
    return up_login()


# @app.route('/fitbit_profile')
# def fitbit_profile():
#     """
#     Display profile data from Fitbit
#
#     :return: print the JSON to verify
#     """
#     oauth = requests_oauthlib.OAuth1Session(
#         FITBIT['client_key'],
#         client_secret=FITBIT['client_secret'],
#         resource_owner_key=RAY_FITBIT['resource_owner_key'],
#         resource_owner_secret=RAY_FITBIT['resource_owner_secret'])
#     r = oauth.get('https://api.fitbit.com/1/user/-/profile.json')
#     return '%s' % r.json()


@app.route('/up_login')
def up_login():
    """
    Redirect to the UP login for approval

    :return: Flask redirect
    """
    oauth = requests_oauthlib.OAuth2Session(
        UP['client_id'],
        redirect_uri=UP['redirect_uri'],
        scope=UP['scope'])
    authorization_url, state = oauth.authorization_url(
        UP['authorization_url'])
    return flask.redirect(authorization_url)


@app.route('/up_authorized')
def up_authorized():
    """
    Callback from UP to finish oauth handshake

    :return: Print out token for now
    """
    oauth = requests_oauthlib.OAuth2Session(UP['client_id'])

    #
    # Super hack to fake https for test env
    #
    url = flask.request.url
    url = url[:4] + 's' + url[4:]

    tokens = oauth.fetch_token(
        UP['request_token_url'],
        authorization_response=url,
        client_secret=UP['client_secret'])

    fitbone_user = services.user.get_user(flask.session['uid'])
    services.user.update_up_creds(fitbone_user, tokens)
    return services.fitbit.subscribe(fitbone_user)
    #return '%s' % flask.session['uid']


# @app.route('/up_profile')
# def up_profile():
#     """
#     Display profile data from UP
#
#     :return: print the JSON to verify
#     """
#     oauth = requests_oauthlib.OAuth2Session(
#         UP['client_id'],
#         token=RAYFB_UP)
#     r = oauth.get('https://jawbone.com/nudge/api/v.1.1/users/@me')
#     return '%s' % r.json()


# @app.route('/move/<day>')
# def move(day):
#     fb_oauth = requests_oauthlib.OAuth1Session(
#         FITBIT['client_key'],
#         client_secret=FITBIT['client_secret'],
#         resource_owner_key=RAY_FITBIT['resource_owner_key'],
#         resource_owner_secret=RAY_FITBIT['resource_owner_secret'])
#     fbr = fb_oauth.get(
# 'https://api.fitbit.com/1/user/-/activities/tracker/steps/date/%s/1d.json' %
# day)
#
#     up_oauth = requests_oauthlib.OAuth2Session(
#         UP['client_id'],
#         token=RAYFB_UP)
#     upr = up_oauth.post('https://jawbone.com/nudge/api/v.1.1/moves')
#
#     return '%s<br/>%s' % (fbr.json(), upr.json())
#
#
# @app.route('/sleep/<day>')
# def sleep(day):
#     fb_oauth = requests_oauthlib.OAuth1Session(
#         FITBIT['client_key'],
#         client_secret=FITBIT['client_secret'],
#         resource_owner_key=RAY_FITBIT['resource_owner_key'],
#         resource_owner_secret=RAY_FITBIT['resource_owner_secret'])
#     fbr = fb_oauth.get(
# 'https://api.fitbit.com/1/user/-/sleep/date/%s.json' % day)
#     fb_sleeps = []
#     for sleep in fbr.json()['sleep']:
#         start = time.mktime(datetime.datetime.strptime(
# sleep['startTime'][:19], '%Y-%m-%dT%H:%M:%S').timetuple())
#         inbed = sleep['timeInBed']
#         end = start + (inbed * 60)
#         fb_sleeps.append({'start': start, 'end': end})
#     #fbout = '%s' % fb_sleeps
#     #return fbout
#
#     up_oauth = requests_oauthlib.OAuth2Session(
#         UP['client_id'],
#         token=RAYFB_UP)
#     upout = ''
#     for sleep in fb_sleeps:
#         upr = up_oauth.post(
# 'https://jawbone.com/nudge/api/v.1.1/users/@me/sleeps',
# data={'time_created': sleep['start'], 'time_completed': sleep['end']})
#         upout += '<br/>%s' % upr.json()
#     return upout


@app.route('/updates', methods=['GET', 'POST'])
def updates():
    """
    Record and display the pubsub records.

    :return: 204 on POST, the records on GET
    """
    if flask.request.method == 'POST':
        # write the file
        with open('updates.txt', 'a') as ufile:
            ufile.write('<p>%s</p>\n' % flask.request.get_json())

        # write the queue
        jmsg = boto.sqs.jsonmessage.JSONMessage()
        jmsg.set_body(flask.request.get_json())
        #q.write(jmsg)

        return '', httplib.NO_CONTENT
    else:
        #print the file
        if os.path.isfile('updates.txt'):
            with open('updates.txt') as ufile:
                return ufile.read()
        else:
            return 'no updates'


@app.route("/")
def hello():
    """
    App homepage

    :return: print text to verify server is running
    """
    return "Hello World!"


if __name__ == "__main__":
    app.run(debug=keys.debug)