#!/usr/bin/env python3

from models import *

print('Seniors in database:', Senior.select().count())
print('Seniors with Facebook urls:', Senior.select().where(Senior.facebook_id != '').count())
print('Users in database:', User.select().count())
print('Comments in database:', Comment.select().count())

staffer_query = Staffer.select().join(Senior).order_by(Senior.tj_username.asc())
for staffer in staffer_query:
    q = Known.select().where(Known.staffer == staffer, Known.status == 1)
    print('Staffer {:12} ({:7}) knows {} people'.format(
        staffer.person.tj_username, staffer.username, q.count()))
