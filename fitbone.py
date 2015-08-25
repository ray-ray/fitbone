"""
Flask app to connect Fitbit to UP.
"""
__author__ = 'rcourtney'


import boto.sqs
import boto.sqs.jsonmessage
import flask
import flask.ext.sqlalchemy
import httplib
import json
import keys
import requests_oauthlib
import services.fitbit
import services.up


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
conn = boto.sqs.connect_to_region(
    "us-east-1",
    aws_access_key_id=keys.aws_key,
    aws_secret_access_key=keys.aws_secret)
fbq = conn.get_queue(keys.queue_name)


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
    'scope': ['generic_event_write', 'move_write', 'sleep_write'],
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

    :return: render the UP login
    """
    uid = flask.session['uid']
    print 'UID: %s' % uid
    temp_user = services.user.get_user(uid)
    print 'TEMP_USER %s' % temp_user
    temp_tokens = temp_user.fitbit_tokens
    print 'TEMP_TOKENS %s' % temp_tokens
    verifier = flask.request.args.get('oauth_verifier')
    print 'VERIFIER %s' % verifier

    #
    # Finish the handshake with the verifier and the temp tokens.
    #
    oauth = requests_oauthlib.OAuth1Session(
        FITBIT['client_key'],
        client_secret=FITBIT['client_secret'],
        resource_owner_key=temp_tokens['oauth_token'],
        resource_owner_secret=temp_tokens['oauth_token_secret'],
        verifier=verifier)
    print 'OAUTH %s' % oauth
    oauth_tokens = oauth.fetch_access_token(FITBIT['access_token_url'])
    print 'OAUTH TOKENS %s' % oauth_tokens

    #
    # Update the user record with the permanent Fitbit tokens and id. Re-set the
    # session uid in case we were updating a pre-existing user. Then start the
    # UP oauth flow.
    #
    fitbit_user = services.user.update_fitbit_creds(
        temp_user,
        oauth_tokens)
    print 'FITBIT USER %s' % fitbit_user
    flask.session['uid'] = fitbit_user.id
    print 'UID %s' % flask.session['uid']
    up_auth_url =  get_up_auth()
    print 'UP AUTH URL %s' % up_auth_url
    return flask.redirect(up_auth_url)


@app.route('/up_login')
def up_login():
    up_auth_url = get_up_auth()
    return flask.redirect(up_auth_url)


def get_up_auth():
    """
    Get the UP oauth URL.

    :return: UP oauth authorization URL
    """
    oauth = requests_oauthlib.OAuth2Session(
        UP['client_id'],
        redirect_uri=UP['redirect_uri'],
        scope=UP['scope'])
    print 'UP OAUTH %s' % oauth
    authorization_url, state = oauth.authorization_url(
        UP['authorization_url'])
    print 'AUTH URL %s' % authorization_url
    print 'STATE %s' % state
    return authorization_url


@app.route('/up_authorized')
def up_authorized():
    """
    Callback from UP to finish oauth handshake

    :return: Print out connected
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

    #
    # Update the user's creds and subscribe to Fitbit pubsub.
    #
    fitbone_user = services.user.get_user(flask.session['uid'])
    services.user.update_up_creds(fitbone_user, tokens)
    services.fitbit.subscribe(fitbone_user)
    return 'Your Fitbit is now connected to UP!'


@app.route('/updates', methods=['POST'])
def updates():
    """
    Enqueue the pubsub records.

    :return: 204 response
    """
    msg = boto.sqs.jsonmessage.JSONMessage(body=flask.request.get_json())
    fbq.write(msg)
    return '', httplib.NO_CONTENT


@app.route('/translate', methods=['POST'])
def translate():
    """
    Translate fitbit pubsubs into UP data.

    :return: 200 response
    """
    if keys.debug:
        events = flask.request.json
    else:
        jmsg = boto.sqs.jsonmessage.JSONMessage(body=flask.request.get_data())
        events = jmsg.decode(jmsg.get_body())
    for event in events:
        fitbone_user = services.user.get_fitbit_user(event['ownerId'])
        if event['collectionType'] == 'sleep':
            fitbit_sleep = services.fitbit.get_sleep(
                fitbone_user,
                event['date'])
            services.up.make_sleep(fitbone_user, fitbit_sleep)
        elif event['collectionType'] == 'activities':
            fitbit_steps = services.fitbit.get_steps(
                fitbone_user,
                event['date'])
            services.up.make_steps(fitbone_user, fitbit_steps)
        elif keys.debug:
            #
            # Got an unrecognized collection, if debugging just send the JSON to
            # the app.
            #
            message = json.dumps(event)
            services.up.generic(fitbone_user, message)
    return ''


@app.route("/")
def hello():
    """
    App homepage

    :return: Hello World
    """
    return "Hello World!"


if __name__ == "__main__":
    app.run(debug=keys.debug)