#!/usr/bin/env python3

# flask config
SECRET_KEY = b'\x1d|+\x8c\xee\\bW\xf5c\xcf\xf0{!f\xf4g\xa3\x953\xda\xa9)\xad\x99I%\x031)>\xb1'

# database config
DATABASE_FILENAME = 'database.db'

# spreadsheet urls
ION_INFO_URL = 'https://docs.google.com/spreadsheets/d/1l734RCiSI9LOnezrJjH84Kc3NIX2mpIRI14li7zKHgw/pub?gid=1178330091&single=true&output=csv'
COMPILED_INFO_URL = 'https://docs.google.com/spreadsheets/d/1l734RCiSI9LOnezrJjH84Kc3NIX2mpIRI14li7zKHgw/pub?gid=646316473&single=true&output=csv'
KNOWN_URL = 'https://docs.google.com/spreadsheets/d/1l734RCiSI9LOnezrJjH84Kc3NIX2mpIRI14li7zKHgw/pub?gid=974556717&single=true&output=csv'

# staffers
HARDCODED_STAFFERS = {
    'gengkev': '2017kgeng',
    'wxu'    : '2017wxu',
    'ayh'    : '2017ahuang',
    'As'     : '2017ashi',
}

# oauth config
OAUTH_CONFIG = dict(
        client_id='t8ES1Usb3O3WCPHLDIqqyGGmBBpjlzMlsehktkrQ',
        client_secret='WDQsfjruOQmw0OMX3jpSiPKfSWtDO06P8HCt2oL48hSsVD1a0uAPUFAq19kpZ9cGLcriqsrfw1vUjdZU5iEQCK3GPy1Ij6WdDaUq0q6JxQwI8d0vUzhROa7KteVaxC2g',
        scope='read',
        access_token_url='https://ion.tjhsst.edu/oauth/token/',
        authorize_url='https://ion.tjhsst.edu/oauth/authorize/',
)

