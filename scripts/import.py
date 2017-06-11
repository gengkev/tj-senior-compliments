#!/usr/bin/env python3

import csv
import os

import peewee
import requests

from models import *
from config import ION_INFO_URL, COMPILED_INFO_URL, KNOWN_URL, HARDCODED_STAFFERS

person_info = {}

print('Processing: ion_info')
with db.atomic():
    r = requests.get(ION_INFO_URL)
    csvfile = csv.DictReader(r.text.splitlines())

    # parse spreadsheet data
    want_keys = ['ion_id', 'tj_username', 'first_name', 'last_name', 'full_name']
    lst = []
    for line in csvfile:
        if not line['tj_username']:
            continue
        obj = { key: line[key] for key in want_keys }
        obj['display_name'] = line['full_name']
        lst.append(obj)

    # insert everything
    try:
        for i in range(0, len(lst), 100):
            Senior.insert_many(lst[i:i+100]).execute()
    except peewee.IntegrityError as e:
        print(e)
        print('ion_info: May have already processed, skipping bulk insert')


print('Processing: staffers')
with db.atomic():
    for username, tj_username in HARDCODED_STAFFERS.items():
        try:
            s = Staffer.get(username=username)
        except DoesNotExist:
            s = Staffer.create(username=username,
                    person=Senior.get(tj_username=tj_username))


print('Processing: compiled_info')
with db.atomic():
    r = requests.get(COMPILED_INFO_URL)
    csvfile = csv.DictReader(r.text.splitlines())

    for line in csvfile:
        if not line['tj_username']:
            continue

        p = Senior.get(tj_username=line['tj_username'])
        p.facebook_id = line['facebook_id']
        p.facebook_name = line['facebook_name']
        p.facebook_picture = line['facebook_picture']

        if line['compiled_nickname']:
            p.nickname = line['compiled_nickname']
            p.display_name = '{} {}'.format(
                    p.nickname, p.last_name)

        else:
            # necessary for updates
            p.display_name = p.full_name

        p.save()


print('Processing: known')
with db.atomic():
    r = requests.get(KNOWN_URL)
    csvfile = csv.DictReader(r.text.splitlines())
    staffers = {s.username: s for s in Staffer.select()}
    lst = []
    for line in csvfile:
        if not line['tj_username']:
            continue
        person = Senior.get(tj_username=line['tj_username'])
        for username, staffer in staffers.items():
            lst.append({
                'person': person,
                'staffer': staffer,
                'status': 1 if line[username] == 'TRUE' else 0,
            })

    try:
        for i in range(0, len(lst), 100):
            Known.insert_many(lst[i:i+100]).execute()
    except peewee.IntegrityError as e:
        print(e)
        print('known: May have already inserted, skipping bulk insert')
        print('If this needs to be updated, drop Known table')

print('done!')

