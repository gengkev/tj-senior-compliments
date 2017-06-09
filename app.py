#!/usr/bin/env python3

import os

from flask import Flask, render_template, request, redirect, url_for, abort, session, jsonify
from requests_oauthlib import OAuth2Session

from models import *
from config import SECRET_KEY, OAUTH_CONFIG


app = Flask(__name__)
app.secret_key = SECRET_KEY


def create_ion_session(state=None, token=None):
    return OAuth2Session(OAUTH_CONFIG['client_id'],
            scope=OAUTH_CONFIG['scope'],
            redirect_uri=url_for('authorized', _external=True),
            state=state,
            token=token)
 

@app.route('/')
def home():
    if 'oauth_token' not in session:
        return redirect(url_for('login'))

    users = Person.select().order_by(Person.last_name)
    comments = Comment.select(Comment, Person).join(Person)
    return render_template('index.html',
            users=users, comments=comments)


@app.route('/profile')
def profile():
    if 'oauth_token' in session:
        ion = create_ion_session(token=session['oauth_token'])
        r = ion.get('https://ion.tjhsst.edu/api/profile')
        print(r.json())
        return jsonify(r.json())

    abort(401)



@app.route('/login')
def login():
    # generate auth url
    ion = create_ion_session()
    authorization_url, state = ion.authorization_url(
            OAUTH_CONFIG['authorize_url'])

    # save state for csrf
    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route('/logout')
def logout():
    session.pop('oauth_token', None)
    return redirect(url_for('home'))


@app.route('/login/authorized')
def authorized():
    code = request.args['code']
    ion = create_ion_session(state=session.pop('oauth_state', None))
    token = ion.fetch_token(
            OAUTH_CONFIG['access_token_url'],
            client_secret=OAUTH_CONFIG['client_secret'],
            code=code)

    session['oauth_token'] = token
    print('oauth token:', token)
    return 'ok maybe you signed in'


@app.route('/user/<string:username>')
def get_user(username):
    try:
        person = Person.get(Person.tj_username == username)
    except Person.DoesNotExist:
        abort(404)
    return render_template('user.html',
            user=person,
            comments_authored=person.comments_authored,
            comments_received=person.comments_received)


@app.route('/comment', methods=['POST'])
def create_comment():
    author_username = request.form['author']
    recipient_username = request.form['recipient']
    title = request.form['title']
    content = request.form['content']

    try:
        author = Person.get(Person.tj_username == author_username)
        recipient = Person.get(Person.tj_username == recipient_username)
    except Person.DoesNotExist:
        abort(400)

    ret = Comment.create(author=author, recipient=recipient, title=title, content=content)
    print(ret)

    return redirect(url_for('home'))


# Database lifecycle

@app.before_request
def before_request():
    db.connect()

@app.teardown_request
def teardown_request(exc):
    db.close()


# CSRF protection

@app.before_request
def csrf_protect():
    if request.method == 'POST':
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = os.urandom(16).hex()
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

