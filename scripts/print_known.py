#!/usr/bin/env python3

from models import *
from collections import OrderedDict

query = (Known.select(Known, Person, Staffer)
        .join(Staffer).switch(Known)
        .join(Person).order_by(Person.last_name))

people = OrderedDict()
for known in query:
    person = known.person
    if person not in people:
        people[person] = []
    people[person].append(known)

for person, known_list in people.items():
    print('{:25}: '.format(person.full_name), end='')
    for known in known_list:
        print('\t{}({})'.format(known.staffer.username, known.status), end='')
    print()

