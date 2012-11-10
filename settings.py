import os

from os.path import dirname, join

try:
    from secrets import *
except ImportError:
    raise SystemExit('Please create a secrets.py based on secrets.py.template')

# Whether or not to show stack traces on errors
# By default this is automaticly true when running locally
# and false when in production
DEBUG = 'HTTP_HOST' in os.environ and os.environ['HTTP_HOST'].startswith('localhost') or False

# The physical root directory of this project
PROJECT_ROOT = dirname(__file__)

# The physical path to the HTML templates
TEMPLATE_PATH = join(PROJECT_ROOT, 'templates')

# Usernames that are not allowed
RESERVED_USERNAMES = [
    'admin',
    'administrator',
    'root',
    'super'
]

# A list of enabled providers. Possible options are defined in
# handlers/auth.py:AuthHandler.AUTH_URLS
AUTH_PROVIDERS = [
    'google',
    'facebook',
    'windows_live'
]
