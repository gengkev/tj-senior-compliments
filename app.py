#!/usr/bin/env python3

import urllib.parse
import os

from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, abort, session, jsonify, g, flash
from requests_oauthlib import OAuth2Session

from models import *
from config import SECRET_KEY, OAUTH_CONFIG, ION_PROFILE_URL, \
        SENIOR_GRAD_YEAR, URL_PRODUCTION

app = Flask(__name__)
app.secret_key = SECRET_KEY


# messing with urls is bad

if URL_PRODUCTION:
    from config import PROD_SCHEME, PROD_HOST, PROD_PATH
    class ReverseProxied(object):
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            environ['wsgi.url_scheme'] = PROD_SCHEME
            environ['HTTP_HOST'] = PROD_HOST
            environ['SCRIPT_NAME'] = PROD_PATH
            return self.app(environ, start_response)

    app.config['PREFERRED_URL_SCHEME'] = PROD_SCHEME
    app.config['SERVER_NAME'] = PROD_HOST
    app.config['APPLICATION_ROOT'] = PROD_PATH
    if PROD_SCHEME == 'https':
        app.config['SESSION_COOKIE_SECURE'] = True

    app.wsgi_app = ReverseProxied(app.wsgi_app)


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
            flash('Warning: this is under construction, and things will break. :(')
            ion_id = session['login_id']
            g.login_user = User.get(ion_id=ion_id)
            return f(*args, **kwargs)
        else:
            flash('You need to be logged in to access that page.')
            return redirect(url_for('login', next=request.path))
    return decorated


@app.route('/')
@login_required
def home():
    return render_template('index.html', login_user=g.login_user)


@app.route('/seniors')
@login_required
def all_seniors():
    seniors = (Senior.select()
        .order_by(Senior.last_name, Senior.tj_username))
    return render_template('all_seniors.html',
            login_user=g.login_user,
            seniors=seniors)


@app.route('/all_comments')
@login_required
def all_comments():
    comments = Comment.select(Comment, Senior).join(Senior)
    return render_template('all_comments.html',
            login_user=g.login_user,
            comments=comments)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html',
            login_user=g.login_user)


@app.route('/scoreboard')
@login_required
def scoreboard():
    return render_template('scoreboard.html',
            login_user=g.login_user)


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
    flash('You were successfully logged out.')
    return redirect(url_for('login'))


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
    flash('You were successfully logged in.')

    # enforce relative url for redirect
    next_url_parsed = urllib.parse.urlparse(next_url)
    if not next_url or next_url_parsed.scheme or next_url_parsed.netloc:
        print('invalid next_url:', next_url)
        next_url = url_for('home')
    else:
        # TODO: bad
        next_url = url_for('home') + next_url
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
            login_user=g.login_user,
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

    ret = Comment.create(
            author=g.login_user,
            recipient=recipient,
            title=title,
            content=content)

    flash('Successfully created comment!')

    # TODO: kinda bad
    return redirect(request.referrer)


@app.route('/debug')
def debug():
    return jsonify(session=repr(session), blah=repr(app.config),
            test1=url_for('authorized', _external=True),
            test2=url_for('home'))


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

