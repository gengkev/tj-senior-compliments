#!/usr/bin/env python3

import datetime
import os

from peewee import *
from config import DATABASE_FILENAME

dir_path = os.path.dirname(os.path.realpath(__file__))
db = SqliteDatabase(os.path.join(dir_path, DATABASE_FILENAME))


class BaseModel(Model):
    class Meta:
        database = db


class Senior(BaseModel):
    ion_id = PrimaryKeyField()
    tj_username = CharField(unique=True)

    # Name fields from Ion
    first_name = CharField()
    last_name = CharField()
    full_name = CharField()

    # Nickname is manually curated
    nickname = CharField(null=True)

    # Prefers nickname over first_name
    display_name = CharField()

    # Pulled from script / manually curated
    facebook_id = CharField(null=True)
    facebook_name = CharField(null=True)
    facebook_picture = TextField(null=True)


class User(BaseModel):
    ion_id = PrimaryKeyField()
    tj_username = CharField(unique=True)

    # info pulled from ion
    full_name = CharField()
    user_type = CharField()
    graduation_year = IntegerField(null=True)

    # ugh
    senior = ForeignKeyField(Senior, null=True)

    # for record keeping
    created = DateTimeField(default=datetime.datetime.now)
    last_login = DateTimeField(default=datetime.datetime.now)

    def get_display_name(self):
        if self.senior is not None:
            return self.senior.display_name
        else:
            return self.full_name

class Staffer(BaseModel):
    username = CharField(unique=True)
    person = ForeignKeyField(Senior)


class Known(BaseModel):
    staffer = ForeignKeyField(Staffer)
    person = ForeignKeyField(Senior, related_name='known_by')
    status = IntegerField(default=0)

    class Meta:
        indexes = (
                (('staffer', 'person'), True),
        )


class Comment(BaseModel):
    author = ForeignKeyField(User, related_name='comments_authored')
    recipient = ForeignKeyField(Senior, related_name='comments_received')
    title = CharField()
    content = TextField()
    created = DateTimeField(default=datetime.datetime.now)
    last_modified = DateTimeField(default=datetime.datetime.now)


def clear_tables():
    table_list = [Senior, User, Staffer, Known, Comment]
    db.connect()
    db.drop_tables(table_list, safe=True)
    db.create_tables(table_list)

