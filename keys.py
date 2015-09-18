"""
Set these keys up as environment variables.

App keys
"""
__author__ = 'rcourtney'


import os

aws_key = os.environ['AWS_KEY']
aws_secret = os.environ['AWS_SECRET']
aws_region = os.environ['AWS_REGION']
queue_name = os.environ['QUEUE_NAME']

fitbit_key = os.environ['FITBIT_KEY']
fitbit_secret = os.environ['FITBIT_SECRET']

up_id = os.environ['UP_ID']
up_secret = os.environ['UP_SECRET']

SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']

secret_key = os.environ['SECRET_KEY']

config = os.environ.get('FITBONE_CONFIG', 'DEV')
if config == 'DEV':
    debug = True
else:
    debug = False
