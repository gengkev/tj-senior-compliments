#!/usr/bin/env python3

from models import *

print('People in database:', Person.select().count())
print('People with Facebook urls:', Person.select().where(Person.facebook_link != '').count())

staffer_query = Staffer.select().join(Person).order_by(Person.tj_username.asc())
for staffer in staffer_query:
    q = Known.select().where(Known.staffer == staffer, Known.status == 1)
    print('Staffer {:12} ({:7}) knows {} people'.format(
        staffer.person.tj_username, staffer.username, q.count()))
