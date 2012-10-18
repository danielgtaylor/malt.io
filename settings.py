import os

from os.path import dirname, join

# Whether or not to show stack traces on errors
# By default this is automaticly true when running locally
# and false when in production
DEBUG = "HTTP_HOST" in os.environ and os.environ['HTTP_HOST'].startswith('localhost') or False

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

if DEBUG:
    STRIPE_PUBLIC_KEY = 'pk_kcc1IpBOOfmRxztYYIEmX6d68jzrE'
    STRIPE_PRIVATE_KEY = 'PUT_KEY_HERE'
else:
    STRIPE_PUBLIC_KEY = 'pk_OmWGuFkwPneYHhQMu6yJ9YMQY74Sw'
    STRIPE_PRIVATE_KEY = 'PUT_KEY_HERE'
