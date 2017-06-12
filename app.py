#!/usr/bin/env python3

import urllib.parse
import os

from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, abort, session, jsonify, g
from requests_oauthlib import OAuth2Session

from models import *
from config import SECRET_KEY, OAUTH_CONFIG, ION_PROFILE_URL, SENIOR_GRAD_YEAR


app = Flask(__name__)
app.secret_key = SECRET_KEY


# oauth utils

def create_ion_session(state=None, token=None):
    return OAuth2Session(OAUTH_CONFIG['client_id'],
            scope=OAUTH_CONFIG['scope'],
            redirect_uri=url_for('authorized', _external=True),
            state=state,
            token=token)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'login_id' in session:
            ion_id = session['login_id']
            g.user = User.get(ion_id=ion_id)
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login', next=request.path))
    return decorated


@app.route('/')
@login_required
def home():
    return render_template('index.html', user=g.user)


@app.route('/seniors')
@login_required
def all_seniors():
    seniors = (Senior.select()
        .order_by(Senior.last_name, Senior.tj_username))
    return render_template('all_seniors.html',
            user=g.user,
            seniors=seniors)


@app.route('/all_comments')
@login_required
def all_comments():
    comments = Comment.select(Comment, Senior).join(Senior)
    return render_template('all_comments.html',
            user=g.user,
            comments=comments)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=g.user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('landing.html')

    # generate auth url
    ion = create_ion_session()
    authorization_url, state = ion.authorization_url(
            OAUTH_CONFIG['authorize_url'])

    # save state for csrf, next_url for redirect
    next_url = request.args.get('next', None)
    session['oauth_state'] = (state, next_url)
    return redirect(authorization_url)


@app.route('/logout')
def logout():
    session.pop('login_id', None)
    return redirect(url_for('home'))


@app.route('/login/authorized')
def authorized():
    # fetch access token
    code = request.args['code']
    state, next_url = session.pop('oauth_state')
    ion = create_ion_session(state=state)
    token = ion.fetch_token(
            OAUTH_CONFIG['access_token_url'],
            client_secret=OAUTH_CONFIG['client_secret'],
            code=code)
    print('oauth token:', token)

    # get profile information
    ion = create_ion_session(token=token)
    r = ion.get(ION_PROFILE_URL)
    r.raise_for_status()

    profile = r.json()
    ion_id = profile['id']

    # fields to set if creating
    # (won't be updated)
    new_fields = {
            'tj_username': profile['ion_username'],
            'full_name': profile['full_name'],
            'user_type': profile['user_type'],
            'graduation_year': profile['graduation_year']
    }

    # create user
    with db.atomic():
        user, created = User.get_or_create(
                ion_id=ion_id, defaults=new_fields)

        if created:
            print('created new user', ion_id)
            if user.graduation_year == SENIOR_GRAD_YEAR:
                user.senior = Senior.get(ion_id=ion_id)
                user.save()
        else:
            user.last_login = datetime.datetime.now()
            user.save()

    # mark in session
    session['login_id'] = ion_id

    # enforce relative url for redirect
    next_url_parsed = urllib.parse.urlparse(next_url)
    if not next_url or next_url_parsed.scheme or next_url_parsed.netloc:
        print('invalid next_url:', next_url)
        next_url = url_for('home')
    return redirect(next_url)


@app.route('/user/<string:username>')
@login_required
def get_user(username):
    user = None
    try: user = User.get(User.tj_username == username)
    except User.DoesNotExist: pass

    senior = None
    try: senior = Senior.get(Senior.tj_username == username)
    except Senior.DoesNotExist: pass

    if user is None and senior is None:
        abort(404)

    display_name = senior.display_name if senior else user.full_name
    return render_template('user.html',
            display_name=display_name,
            tj_username=username,
            user=user,
            senior=senior)


@app.route('/comment', methods=['POST'])
@login_required
def create_comment():
    recipient_id = request.form['recipient']
    title = request.form['title']
    content = request.form['content']

    try:
        recipient = Senior.get(Senior.ion_id == recipient_id)
    except Senior.DoesNotExist:
        abort(400)

    ret = Comment.create(author=g.user, recipient=recipient, title=title, content=content)
    print(ret)

    return redirect(url_for('home'))


@app.route('/debug')
def debug():
    return jsonify(session=repr(session))


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
            abort(403, 'Invalid CSRF token')

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = os.urandom(16).hex()
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

