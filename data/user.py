"""
User model
"""
__author__ = 'rcourtney'


import datetime
import json
import sqlalchemy.ext.hybrid

import fitbone
db = fitbone.db


class User(db.Model):
    """
    SQLAlchemy model for User rows.
    """
    id = db.Column(db.Integer, primary_key=True)
    fitbit_id = db.Column(db.String(128), unique=True)
    fitbit_json = db.Column(db.String(256), nullable=False)
    up_json = db.Column(db.String(512))
    time_created = db.Column(
        db.DateTime(timezone=True),
        default=datetime.datetime.now,
        nullable=False)
    time_modified = db.Column(
        db.DateTime(timezone=True),
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        nullable=False)
    time_removed = db.Column(db.DateTime(timezone=True))

    def __init__(
            self,
            fitbit_tokens,
            fitbit_id=None,
            up_tokens=None):
        """
        User object with temporary fitbit credentials.

        :param fitbit_tokens: fitbit api oauth tokens
        :param fitbit_id: fitbit user id
        :param up_tokens: UP oauth tokens
        :return: User object
        """
        self.fitbit_tokens = fitbit_tokens
        if fitbit_id is not None:
            self.fitbit_id = fitbit_id
        if up_tokens is not None:
            self.up_tokens = up_tokens

    @sqlalchemy.ext.hybrid.hybrid_property
    def fitbit_tokens(self):
        """
        Convert JSON to tokens dict.

        :return: tokens dict
        """
        return json.loads(self.fitbit_json)

    @fitbit_tokens.setter
    def fitbit_tokens(self, tokens):
        """
        Convert tokens dict to JSON.

        :param tokens: tokens dict
        :return: None
        """
        self.fitbit_json = json.dumps(tokens)

    @sqlalchemy.ext.hybrid.hybrid_property
    def up_tokens(self):
        """
        Convert JSON to tokens dict.

        :return: tokens dict
        """
        return json.loads(self.up_json)

    @up_tokens.setter
    def up_tokens(self, tokens):
        """
        Convert tokens dict to JSON
        :param tokens:
        :return:
        """
        self.up_json = json.dumps(tokens)