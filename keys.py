"""
ONLY CHECK THIS INTO YOUR DEPLOY BRANCH.

App keys
"""
__author__ = 'rcourtney'


import os
config = os.environ.get('FITBONE_CONFIG', 'DEV')

aws_key = 'AKIAJIAGYSYAVYPHREGA'
aws_secret = '9MA28MO8pG5PkEd3YrGACiig5j677yqaSJSvaw/d'

fitbit_key = '32c172b2fbf94492992f823ab15de74b'
fitbit_secret = '79c4ee3570ea4633b07f25e8f8c233b4'

up_id = '18pTH7S2vNw'
up_secret = '1bae5b035ebfd89e0cbaef096bd25459b3c40734'

if config == 'LIVE':
    SQLALCHEMY_DATABASE_URI = 'mysql://fitbone:f1tb0n3@aa1y1bjk4eb68b6.cohn5k6lvgpq.us-east-1.rds.amazonaws.com/fitbone'
    debug = False
    queue_name = 'awseb-e-chb3x3zwin-stack-AWSEBWorkerQueue-ELG26ITCG7YS'
elif config == 'DEV':
    #
    # mysql> create user 'fitbone'@'localhost' identified by 'fitbone';
    # mysql> create database fitbone;
    # mysql> grant all on fitbone.* to 'fitbone'@'localhost';
    #
    SQLALCHEMY_DATABASE_URI = 'mysql://fitbone:fitbone@/fitbone'
    debug = True
    queue_name = 'fitbonetest'

secret_key = 'makethisbetterforliveRAY'