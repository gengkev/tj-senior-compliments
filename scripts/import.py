#!/usr/bin/env python3

import csv
import os
import requests

from models import *
from config import ION_INFO_URL, COMPILED_INFO_URL, KNOWN_URL, HARDCODED_STAFFERS

person_info = {}

print('Processing: ion_info')
with db.atomic():
    r = requests.get(ION_INFO_URL)
    csvfile = csv.DictReader(r.text.splitlines())
    want_keys = ['ion_id', 'tj_username', 'first_name', 'middle_name', 'last_name', 'full_name']
    lst = [
        { key: line[key] for key in want_keys }
        for line in csvfile
        if line['tj_username']
    ]
    for i in range(0, len(lst), 100):
        Person.insert_many(lst[i:i+100]).execute()


print('Processing: Staffers (hardcoded)')
with db.atomic():
    for username, tj_username in HARDCODED_STAFFERS.items():
        try:
            s = Staffer.get(username=username)
        except DoesNotExist:
            s = Staffer.create(username=username,
                    person=Person.get(tj_username=tj_username))


print('Processing: compiled_info')
with db.atomic():
    r = requests.get(COMPILED_INFO_URL)
    csvfile = csv.DictReader(r.text.splitlines())
    for line in csvfile:
        if not line['tj_username']:
            continue
        p = Person.get(tj_username=line['tj_username'])
        p.facebook_link = line['facebook_link']
        p.nickname      = line['compiled_nickname']
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
        person = Person.get(tj_username=line['tj_username'])
        for username, staffer in staffers.items():
            lst.append({
                'person': person,
                'staffer': staffer,
                'status': 1 if line[username] == 'TRUE' else 0,
            })
    for i in range(0, len(lst), 100):
        Known.insert_many(lst[i:i+100]).execute()



print('done!')

