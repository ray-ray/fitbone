"""
Flask app to connect Fitbit to UP.
"""
__author__ = 'rcourtney'

import datetime
import flask
import httplib
import os.path
import requests_oauthlib
import time

app = flask.Flask(__name__)

FITBIT = {
    'client_key': '32c172b2fbf94492992f823ab15de74b',
    'client_secret': '79c4ee3570ea4633b07f25e8f8c233b4',
    'request_token_url': 'https://api.fitbit.com/oauth/request_token',
    'base_authorization_url': 'https://www.fitbit.com/oauth/authorize',
    'access_token_url': 'https://api.fitbit.com/oauth/access_token'
}
UP = {
    'client_id': '18pTH7S2vNw',
    'client_secret': '1bae5b035ebfd89e0cbaef096bd25459b3c40734',
    'redirect_uri': 'https://rayfitbone.herokuapp.com/up_authorized',
    'scope': ['move_write', 'sleep_write'],
    'authorization_url': 'https://jawbone.com/auth/oauth2/auth',
    'request_token_url': 'https://jawbone.com/auth/oauth2/token'
}

#
# Hard-code my creds for testing
#
RAY_FITBIT = {
    'resource_owner_key': 'af184e7a25a731392a8071ca1d40c5d1',
    'resource_owner_secret': '2bde71074c7df1027cbe1b95a18987d9'
}
RAYFB_UP = {
    'token_type': 'Bearer',
    'access_token': 'CHSvNoQb5om1wXUEYtBfcdbO3OUygiP0udWFIDk-HewbMlVM8Vmv6nFW8vF9AUYmGLjyAxLkQUT1jjKD0Abcg1ECdgRlo_GULMgGZS0EumxrKbZFiOmnmAPChBPDZ5JP',
    'refresh_token': 'fW0MDZjjlhPRF95VOI6bz3kPEBQGORaeluvuD44qR3XdL2WxNgQvKekaCy5aBtavNNWfJhnfRQwlAN2iCODyqw',
    'expires_in': 31536000,
    'expires_at': 1460329452.795321
}


@app.route('/fitbit_login')
def fitbit_login():
    """
    Redirect to Fitbit login screen for app approval.

    :return: Flask redirect response
    """
    oauth = requests_oauthlib.OAuth1Session(
        FITBIT['client_key'],
        client_secret=FITBIT['client_secret'])
    fetch_response = oauth.fetch_request_token(FITBIT['request_token_url'])

    #
    # Faking a session for testing.
    #
    FITBIT['resource_owner_key'] = fetch_response.get('oauth_token')
    FITBIT['resource_owner_secret'] = fetch_response.get('oauth_token_secret')

    base_authorization_url = FITBIT['base_authorization_url']
    authorization_url = oauth.authorization_url(base_authorization_url)
    return flask.redirect(authorization_url)


@app.route('/fitbit_authorized')
def fitbit_authorized():
    """
    Callback from Fitbit to finish the oauth handshake

    :return: Print out keys for now
    """
    verifier = flask.request.args.get('oauth_verifier')
    oauth = requests_oauthlib.OAuth1Session(
        FITBIT['client_key'],
        client_secret=FITBIT['client_secret'],
        resource_owner_key=FITBIT['resource_owner_key'],
        resource_owner_secret=FITBIT['resource_owner_secret'],
        verifier=verifier)
    oauth_tokens = oauth.fetch_access_token(FITBIT['access_token_url'])
    resource_owner_key = oauth_tokens.get('oauth_token')
    resource_owner_secret = oauth_tokens.get('oauth_token_secret')

    #
    # Dump the keys so I can hard code them for now.
    #
    return '%s<br/>%s' % (resource_owner_key, resource_owner_secret)


@app.route('/fitbit_profile')
def fitbit_profile():
    """
    Display profile data from Fitbit

    :return: print the JSON to verify
    """
    oauth = requests_oauthlib.OAuth1Session(
        FITBIT['client_key'],
        client_secret=FITBIT['client_secret'],
        resource_owner_key=RAY_FITBIT['resource_owner_key'],
        resource_owner_secret=RAY_FITBIT['resource_owner_secret'])
    r = oauth.get('https://api.fitbit.com/1/user/-/profile.json')
    return '%s' % r.json()


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

    token = oauth.fetch_token(
        UP['request_token_url'],
        authorization_response=url,
        client_secret=UP['client_secret'])

    #
    # Dump the token so I can hard code it for testing.
    #
    return '%s' % token


@app.route('/up_profile')
def up_profile():
    """
    Display profile data from UP

    :return: print the JSON to verify
    """
    oauth = requests_oauthlib.OAuth2Session(
        UP['client_id'],
        token=RAYFB_UP)
    r = oauth.get('https://jawbone.com/nudge/api/v.1.1/users/@me')
    return '%s' % r.json()


@app.route('/fb_subscribe')
def fb_subscribe():
    fb_oauth = requests_oauthlib.OAuth1Session(
        FITBIT['client_key'],
        client_secret=FITBIT['client_secret'],
        resource_owner_key=RAY_FITBIT['resource_owner_key'],
        resource_owner_secret=RAY_FITBIT['resource_owner_secret'])
    fbr = fb_oauth.post('https://api.fitbit.com/1/user/-/apiSubscriptions/1.json')
    return '%s<br>%s' % (fbr.status_code, fbr.json())


@app.route('/move/<day>')
def move(day):
    fb_oauth = requests_oauthlib.OAuth1Session(
        FITBIT['client_key'],
        client_secret=FITBIT['client_secret'],
        resource_owner_key=RAY_FITBIT['resource_owner_key'],
        resource_owner_secret=RAY_FITBIT['resource_owner_secret'])
    fbr = fb_oauth.get('https://api.fitbit.com/1/user/-/activities/tracker/steps/date/%s/1d.json' % day)

    up_oauth = requests_oauthlib.OAuth2Session(
        UP['client_id'],
        token=RAYFB_UP)
    upr = up_oauth.post('https://jawbone.com/nudge/api/v.1.1/moves')

    return '%s<br/>%s' % (fbr.json(), upr.json())


@app.route('/sleep/<day>')
def sleep(day):
    fb_oauth = requests_oauthlib.OAuth1Session(
        FITBIT['client_key'],
        client_secret=FITBIT['client_secret'],
        resource_owner_key=RAY_FITBIT['resource_owner_key'],
        resource_owner_secret=RAY_FITBIT['resource_owner_secret'])
    fbr = fb_oauth.get('https://api.fitbit.com/1/user/-/sleep/date/%s.json' % day)
    fb_sleeps = []
    for sleep in fbr.json()['sleep']:
        start = time.mktime(datetime.datetime.strptime(sleep['startTime'][:19], '%Y-%m-%dT%H:%M:%S').timetuple())
        inbed = sleep['timeInBed']
        end = start + (inbed * 60)
        fb_sleeps.append({'start': start, 'end': end})
    #fbout = '%s' % fb_sleeps
    #return fbout

    up_oauth = requests_oauthlib.OAuth2Session(
        UP['client_id'],
        token=RAYFB_UP)
    upout = ''
    for sleep in fb_sleeps:
        upr = up_oauth.post('https://jawbone.com/nudge/api/v.1.1/users/@me/sleeps', data={'time_created': sleep['start'], 'time_completed': sleep['end']})
        upout += '<br/>%s' % upr.json()
    return upout


@app.route('/updates', methods=['GET', 'POST'])
def updates():
    if flask.request.method == 'POST':
        # write the file
        with open('updates.txt', 'a') as ufile:
            ufile.write('<p>%s</p>\n' % flask.request.get_json())
        return ('', httplib.NO_CONTENT)
    else:
        #print the file
        if os.path.isfile('updates.txt'):
            with open('updates.txt', 'r') as ufile:
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
    app.run(debug=True)