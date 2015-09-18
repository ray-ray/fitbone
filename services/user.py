"""
APIs to interact with user data, specifically oauth tokens
"""
__author__ = 'rcourtney'


import data.user
import decorator
import sqlalchemy.exc
import traceback

import fitbone
db = fitbone.db

#
# Maximum number of times to retry the database connection.
#
MAX_RETRIES = 3


@decorator.decorator
def retry_connection(func, *args, **kwargs):
    """
    Decorator to retry a failed DB connection.

    :param func: function to retry
    :param args: args passed to the function
    :param kwargs: kwargs passed to the function
    :return: return value of the function
    """
    attempts = 0
    while attempts < MAX_RETRIES:
        print 'ATTEMPT %s' % attempts
        try:
            return func(*args, **kwargs)
        except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.StatementError):
            traceback.print_exc()
            db.session.rollback()
            attempts += 1
            if attempts >= MAX_RETRIES:
                raise


@retry_connection
def create_or_update_user(fitbit_tokens, up_tokens):
    """
    Upsert a new/existing user.

    :param fitbit_tokens: fitbit api oauth tokens
    :param up_tokens: up api oauth tokens

    :return: User object
    """
    fitbit_uid = fitbit_tokens['encoded_user_id']
    fitbone_user = get_fitbit_user(fitbit_uid)
    if fitbone_user is None:
        fitbone_user = data.user.User(fitbit_tokens, up_tokens=up_tokens)
    else:
        fitbone_user.fitbit_tokens = fitbit_tokens
        fitbone_user.up_tokens = up_tokens
    db.session.add(fitbone_user)
    db.session.commit()
    return fitbone_user


@retry_connection
def get_fitbit_user(fitbit_id):
    """
    Get a user by fitbit_id.

    :param fitbit_id: fitbit user id
    :return: User object
    """
    return data.user.User.query.filter_by(fitbit_id=fitbit_id).first()
