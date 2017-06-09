#!/usr/bin/env python3

import os

from peewee import *
from config import DATABASE_FILENAME

dir_path = os.path.dirname(os.path.realpath(__file__))
db = SqliteDatabase(os.path.join(dir_path, DATABASE_FILENAME))


class BaseModel(Model):
    class Meta:
        database = db

class Person(BaseModel):
    ion_id = PrimaryKeyField()
    tj_username = CharField(unique=True)

    # name
    full_name = CharField()
    first_name = CharField()
    middle_name = CharField()
    last_name = CharField()
    nickname = CharField(default='')

    # facebook
    facebook_link = CharField(default='')


class Staffer(BaseModel):
    username = CharField(unique=True)
    person = ForeignKeyField(Person)


class Known(BaseModel):
    staffer = ForeignKeyField(Staffer)
    person = ForeignKeyField(Person, related_name='known_by')
    status = IntegerField(default=0)

    class Meta:
        indexes = (
                (('staffer', 'person'), True),
        )


class Comment(BaseModel):
    author = ForeignKeyField(Person, related_name='comments_authored')
    recipient = ForeignKeyField(Person, related_name='comments_received')
    title = CharField()
    content = TextField()


def clear_tables():
    table_list = [Person, Staffer, Known, Comment]
    db.connect()
    db.drop_tables(table_list, safe=True)
    db.create_tables(table_list)

