import datetime
import jinja2
import random
import re
import settings

from contrib.unidecode import unidecode
from google.appengine.api import users
from math import floor
from xml.sax.saxutils import escape
from operator import itemgetter

from models.userprefs import UserPrefs

GAL_TO_LITERS = 3.78541
LB_TO_KG = 0.45359
OZ_TO_KG = LB_TO_KG / 16.0

# Setup the Jinja2 template environment
JINJA_ENV = jinja2.Environment(**{
    'loader': jinja2.FileSystemLoader(settings.TEMPLATE_PATH)
})

# The logout url, if a user is currently logged in
try:
    LOGOUT_URL = users.create_logout_url('/')
except:
    LOGOUT_URL = '/'

# A mapping of award names to icon, description pairs
AWARDS = {
    'admin': ['cog', 'Administrator'],
    'donated': ['gift', 'Donated'],
    'liked15': ['heart', 'Liked 15 brews'],
    'created10': ['book', 'Created 10 brews']
}

template_cache = {}


def login_required(handler_method, awards=None):
    """
    A decorator to require that a user be logged in to access a handler.

    To use it, decorate your get() method like this::

        @login_required
        def get(self):
            self.render('foo.html', {
                user: self.user
            })

    If the user is not logged in, they will be redirected to /login
    """
    def check_login(self, *args, **kwargs):
        if self.request.method != 'GET':
            self.abort(400, detail='The login_required decorator '
                'can only be used for GET requests.')

        success = False
        user = self.user
        if user:
            if awards:
                for award in awards:
                    if award in user.awards:
                        # User is logged in and award found
                        success = True
                        break
                else:
                    # User is logged in, but no reward found
                    success = False
            else:
                # User is logged in, no awards required
                success = True

        if not success:
            self.session['next'] = str(self.request.path_qs)
            return self.redirect('/login')
        else:
            handler_method(self, *args, **kwargs)

    return check_login


def admin_required(handler_method):
    """
    A decorator to require that a user be logged in and an admin
    to access a handler.
    """
    return login_required(handler_method, awards=['admin'])


def get_template(name):
    """
    Get a Jinja2 template by name. This method caches templates in memory
    and tries to fetch from memory when possible.
    """
    t = template_cache.get(name, None)
    if t is None:
        # Get from disk
        t = JINJA_ENV.get_template(name)

        # Update the cache unless we are in developer mode
        if not settings.DEBUG:
            template_cache[name] = t

    return t


def render(handler, template, params=None, write_to_stream=True):
    """
    Render a page through Jinja2, passing in optional parameters.
    """
    p = params and params.copy() or {}
    p.update({
        'debug': settings.DEBUG,
        'user': handler.user,
        'base_url': handler.request.host_url,
    })

    t = get_template(template)

    rendered = t.render(p)
    
    if write_to_stream:
        handler.response.out.write(rendered)
    
    return rendered


def render_json(handler, value):
    """Render JSON output, including proper headers"""
    handler.response.headers['Content-Type'] = 'application/json'
    handler.response.out.write(json.dumps(value))


def xmlescape(value):
    """
    Convert a value to a string and escape it for inclusion in XML
    """
    return escape(unicode(value))


def time_to_min(value):
    """
    Convert a value into minutes. Can take in integers, floats,
    strings of those, strings appended with 'min', 'm', 'h', etc.

        >>> time_to_min('5min')
        5.0
        >>> time_to_min('2hr')
        120.0
        >>> time_to_min('5sec')
        0.08333333333333333

    """
    conversions = {
        'd': 60 * 24,
        'day': 60 * 24,
        'days': 60 * 24,
        'h': 60,
        'hr': 60,
        'hrs': 60,
        'hour': 60,
        'hours': 60,
        'm': 1,
        'min': 1,
        'mins': 1,
        's': 1 / 60.0,
        'sec': 1 / 60.0,
        'seconds': 1 / 60.0
    }

    if type(value) in [str, unicode]:
        for unit, factor in conversions.items():
            if unit in value:
                value = float(value.split(unit)[0]) * factor
                break

    return float(value)


def slugify(value):
    """
    Return a slugified version of a string, removing strange
    unicode characters and replacing whitespace with dashes.

        >>> slugify('This is a test')
        'this-is-a-test'
        >>> slugify('aB   xY   Zw')
        'ab-xy-zw'

    """
    return re.sub(r'\W+', '-', unidecode(value).lower())

JINJA_ENV.filters['slugify'] = slugify


def render_fermentable_template(values):
    """
    Render a fermentable template list item for the buttons which add a
    new fermentable item to the recipe.
    """
    return '<li data-description="%(description)s" data-ppg="%(ppg)d" data-srm="%(srm)d" onclick="Recipe.addFermentableRowTemplate(this);"><a><span class="srm" data-srm="%(srm)d"></span> %(description)s</a></li>' % {
        'description': values[0],
        'ppg': values[1],
        'srm': values[2]
    }

JINJA_ENV.filters['render_fermentable_template'] = render_fermentable_template


def render_hops_template(values):
    """
    Render a hop or spice template list item for the buttons which add
    a new hop or spice item to the recipe.
    """
    rating = ''

    # Only show rating information for hops
    if values[1]:
        for i in range(3):
            rating += '<i class="icon-asterisk icon-white"'
            if i >= values[1] / 5.0:
                rating += ' style="opacity: 0.2"'
            rating += '></i>'

    return '<li data-description="%(description)s" data-aa="%(aa)s" onclick="Recipe.addHopRowTemplate(this);"><a>%(rating)s %(description)s</a></li>' % {
        'description': values[0],
        'aa': values[1],
        'rating': rating
    }

JINJA_ENV.filters['render_hops_template'] = render_hops_template


def render_yeast_template(values):
    """
    Render a yeast or bug template list item for the buttons which add a
    new yeast or bug item to the recipe.
    """
    return '<li data-description="%(description)s" data-type="%(type)s" data-form="%(form)s" data-attenuation="%(attenuation)s" onclick="Recipe.addYeastRowTemplate(this);"><a>%(description)s</a></li>' % {
        'description': values[0],
        'type': values[1],
        'form': values[2],
        'attenuation': values[3]
    }

JINJA_ENV.filters['render_yeast_template'] = render_yeast_template


def weight_whole(value):
    """
    Get the whole part of a weight. E.g. for a weight of 8.6, this would
    return 8.

        >>> weight_whole(1.0)
        1
        >>> weight_whole(1.1)
        1
        >>> weight_whole(1.9)
        1

    """
    return int(floor(value))

JINJA_ENV.filters['weight_whole'] = weight_whole


def weight_fractional(value, parts):
    """
    Get the fractional part of a weight, given a number of parts. E.g. for
    8.6 and 16 parts, this would return 10.

        >>> weight_fractional(8.0, 10)
        0
        >>> weight_fractional(8.6, 10)
        6
        >>> weight_fractional(8.6, 16)
        10

    """
    return int(round((value - floor(value)) * parts))

JINJA_ENV.filters['weight_fractional'] = weight_fractional


def render_awards(values):
    """
    Render a list of awards for a user, or if the user has none display the
    message 'No Awards!'.
    """
    return ' '.join(['<i class="icon-%(image)s" title="%(title)s"></i>' % {
        'image': AWARDS[item][0],
        'title': AWARDS[item][1]
    } for item in values]) or ''

JINJA_ENV.filters['render_awards'] = render_awards


def format_date(value, format="%d %b %Y"):
    """
    Format a date by a given strftime format string. This defaults to looking
    like:

        16 Jun 2012

    """
    return value and value.strftime(format) or ''

JINJA_ENV.filters['format_date'] = format_date


def ungettext(a, b, count):
    if count != 1:
        return b
    return a


def ugettext(a):
    return a


def timesince(d, now=None):
    """
    Takes two datetime objects and returns the time between d and now
    as a nicely formatted string, e.g. "10 minutes".  If d occurs after now,
    then "0 minutes" is returned.

    Units used are years, months, weeks, days, hours, and minutes.
    Seconds and microseconds are ignored.  Up to two adjacent units will be
    displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
    possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.

    Adapted from http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    chunks = (
      (60 * 60 * 24 * 365, lambda n: ungettext('year', 'years', n)),
      (60 * 60 * 24 * 30, lambda n: ungettext('month', 'months', n)),
      (60 * 60 * 24 * 7, lambda n : ungettext('week', 'weeks', n)),
      (60 * 60 * 24, lambda n : ungettext('day', 'days', n)),
      (60 * 60, lambda n: ungettext('hour', 'hours', n)),
      (60, lambda n: ungettext('minute', 'minutes', n))
    )
    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime.datetime):
        d = datetime.datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime(now.year, now.month, now.day)

    if not now:
        if d.tzinfo:
            now = datetime.datetime.now(LocalTimezone(d))
        else:
            now = datetime.datetime.now()

    # ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u'0 ' + ugettext('minutes')
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    s = ugettext('%(number)d %(type)s') % {'number': count, 'type': name(count)}
    if i + 1 < len(chunks):
        # Now get the second item
        seconds2, name2 = chunks[i + 1]
        count2 = (since - (seconds * count)) // seconds2
        if count2 != 0:
            s += ugettext(', %(number)d %(type)s') % {'number': count2, 'type': name2(count2)}
    return s

JINJA_ENV.filters['timesince'] = timesince


def recipe_snippet(value, show_owner=False):
    return JINJA_ENV.get_template('recipe_snippet.html').render({
        'recipe': value,
        'show_owner': show_owner
    })

JINJA_ENV.filters['recipe_snippet'] = recipe_snippet


def render_history_diff(value):
    """
    Render a history diff. This will produce a formatted list of changes found
    in value, which must be formatted like the output by
    models.recipe.RecipeBase.

    This function attempts to order the history in a 'most interesting' order,
    defined as follows:
        1. Additions and deletions
        2. Changes that affect the recipe snippet
            a. Title, Description
            b. Color, IBU, Alcohol (affected by ingredients and sizes)
        3. Other
    """
    difflist = []

    additions = value[0]
    deletions = value[1]
    modifications = value[2]

    if len(additions) == len(deletions) == len(modifications) == 0:
        return '<p>Nothing\'s changed.</p>'

    for key in additions:
        if key == 'ingredients':
            for type in additions['ingredients']:
                for ingredient in additions['ingredients'][type]:
                    difflist.append('<li>' + render_history_addition(type, ingredient, True) + '</li>')
        else:
            difflist.append('<li>' + render_history_addition(key, additions[key]) + '</li>')

    for key in deletions:
        if key == 'ingredients':
            for type in deletions['ingredients']:
                for ingredient in deletions['ingredients'][type]:
                    difflist.append('<li>' + render_history_deletion(type, ingredient, True) + '</li>')
        else:
            difflist.append('<li>' + render_history_deletion(key, deletions[key]) + '</li>')

    # Generate a list of modifications and assign them a score
    scoredlist = []
    # We don't care about these being modified, since they're calculated properties
    ignorelist = ('color', 'ibu', 'alcohol')
    # Properties that will affect the recipe snippet, assigned a higher score
    highimpact = ('batch_size', 'boil_size')
    # Properties that will affect the recipe snippet, but we want to avoid
    # showing redundant info, so these will be penalized
    lowimpact = ('title', 'description')
    for key in modifications:
        if key in ignorelist:
            continue
        elif key == 'ingredients':
            for type in modifications['ingredients']:
                for ingredient in modifications['ingredients'][type]:
                    # Start with a high score
                    score = 30
                    scoredlist.append((score, '<li>' + render_history_ingredient_mod(type,
                        ingredient,
                        modifications['ingredients'][type][ingredient]) + '</li>'))
        else:
            if key in highimpact:
                # Start with a high score
                score = 20
            elif key in lowimpact:
                # Start with a low score
                score = 0
            else:
                # Start with a normal score
                score = 10
            scoredlist.append((score, '<li>' + render_history_modification(key, modifications[key][1]) + '</li>'))

    if len(scoredlist) > 0:
        # Sort based on score
        scoredlist.sort(key=itemgetter(0), reverse=True)

        # Append the sorted items to the difflist
        difflist.extend([diff for score, diff in scoredlist])

    return '<ul>' + ''.join(difflist) + '</ul>'

JINJA_ENV.filters['render_history_diff'] = render_history_diff

def render_history_addition(key, value, ingredient=False):
    """
    Render an addition in the history diff.
    """
    return 'Added %(key)s%(extra)s <code>%(value)s</code>' % {
        'key': key_for_display(key),
        'extra': ingredient and ' ingredient' or '',
        'value': value
    }


def render_history_deletion(key, value, ingredient=False):
    """
    Render a deletion in the history diff.
    """
    return 'Removed %(key)s%(extra)s <code>%(value)s</code>' % {
        'key': key_for_display(key),
        'extra': ingredient and ' ingredient' or '',
        'value': value
    }


def render_history_modification(key, value):
    """
    Render a modification in the history diff.
    """
    return 'Changed %(key)s to <code>%(value)s</code>' % {
        'key': key_for_display(key),
        'value': value
    }


def render_history_ingredient_mod(key, name, value):
    """
    Render an ingredient modification in the history diff. This provides more
    info than a regular modification.
    """
    return 'Changed properties on %(key)s ingredient <strong>%(value)s</strong><ul>' % {
        'key': key_for_display(key),
        'value': name
    } + \
    ''.join(['<li>Changed %(key)s from <code>%(from)s</code> to <code>%(to)s</code></li>' % {
        'key': key_for_display(subkey),
        'from': value[subkey][0],
        'to': value[subkey][1]
    } for subkey in value]) + '</ul>'


def key_for_display(key):
    """
    Return a human-friendly version of a given key string.
    """
    if key == 'aa':
        return 'AA%'
    elif key == 'ppg':
        return 'PPG'
    elif key == 'color':
        return '&deg;L'
    elif key == 'oz':
        return 'weight'
    else:
        return key.replace('_', ' ')

def render_rating(brew):
    """
    Render a rating out of 5 with stars.
    """
    slug = brew.slug + '-' + str(random.randint(0, 1000))
    rating_str = ''

    for x in range(1, 6):
        if x != brew.rating:
            rating_str += '<input name="%s" type="radio" class="star" value="%s" disabled="disabled" title="%s / 5"/>' % (slug, x, brew.rating)
        else:
            rating_str += '<input name="%s" type="radio" class="star" value="%s" disabled="disabled" checked="checked"/>' % (slug, x)

    return rating_str

JINJA_ENV.filters['render_rating'] = render_rating

def fixed3(value):
    """
    Render a floating point value to 3 decimal places
    """
    return '%.3f' % value

JINJA_ENV.filters['fixed3'] = fixed3
