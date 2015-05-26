"""
APIs to interact with user data, specifically oauth tokens
"""
__author__ = 'rcourtney'


import data.user
import datetime
import fitbone
db = fitbone.db


def create_temp_user(temp_tokens):
    """
    Create a user with temporary fitbit credentials.

    :param temp_tokens: fitbit api oauth temp tokens
    :return: User object
    """
    temp_user = data.user.User(temp_tokens)
    db.session.add(temp_user)
    db.session.commit()
    return temp_user


def get_user(uid):
    """
    Get a user by primary key.

    :param uid: User id
    :return: User object
    """
    return data.user.User.query.get(uid)


def get_fitbit_user(fitbit_id):
    """
    Get a user by fitbit_id.

    :param fitbit_id: fitbit user id
    :return: User object
    """
    print 'RAY2'
    return data.user.User.query.filter_by(fitbit_id=fitbit_id).first()


def update_fitbit_creds(fitbit_user, fitbit_tokens):
    """
    Update the fitbit id and tokens.

    :param fitbit_user: User object
    :param fitbit_tokens: fitbit api oauth tokens
    :return: user object
    """
    token_uid = fitbit_tokens['encoded_user_id']
    if fitbit_user.fitbit_id is None:
        #
        # Working with a temporary user object, so check if the Fitbit user
        # already exists.
        #
        existing_user = get_fitbit_user(token_uid)
        if existing_user is None:
            fitbit_user.fitbit_id = token_uid
        else:
            #
            # User already exists so remove the temporary one.
            #
            remove_user(fitbit_user)
            fitbit_user = existing_user
    else:
        #
        # Working with an existing user object, so make sure the fitbit ids
        # match
        #
        if fitbit_user.fitbit_id != token_uid:
            raise UserMismatchException

    fitbit_user.fitbit_tokens = fitbit_tokens
    db.session.commit()
    return fitbit_user


def update_up_creds(fitbone_user, up_tokens):
    """
    Update the UP tokens.

    :param fitbone_user: User object
    :param up_tokens: UP api oauth tokens
    :return: User object
    """
    fitbone_user.up_tokens = up_tokens
    db.session.commit()
    return fitbone_user


def remove_user(fitbone_user):
    """
    Soft delete a user.

    :param fitbone_user: User object
    :return: None
    """
    fitbone_user.time_removed = datetime.datetime.now()
    db.session.commit()


class UserMismatchException(Exception):
    """
    Exception to raise when trying to update the Fitbit credentials of the wrong
    Fitbit user.
    """
    pass
