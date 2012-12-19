import cgi
import json
import logging

from contrib.paodate import Date
from handlers.base import BaseHandler
from models.brew import Brew
from models.recipe import Recipe
from models.useraction import UserAction
from models.userprefs import UserPrefs
from util import slugify


def generate_usable_slug(brew):
    """
    Generate a usable slug for a given brew. This method will try to slugify
    the brew date + owner and then append an integer if needed, increasing this
    integer until no existing brew would be overwritten.
    """
    base = brew.started.strftime('%d-%b-%Y') + '-' + brew.owner.name
    slug = slugify(base)

    # Reuse existing slug if we can
    if brew.slug and brew.slug == slug:
        return brew.slug

    append = 0
    while True:
        count = Brew.all()\
                    .filter('owner =', brew.owner)\
                    .filter('recipe =', brew.recipe)\
                    .filter('slug =', slug)\
                    .count()

        if not count:
            break

        append += 1
        slug = slugify(base) + str(append)

    return slug


class BrewHandler(BaseHandler):
    """
        Create a new brew.

        /users/USERNAME/recipes/RECIPE-SLUG/brew
        /users/USERNAME/recipes/RECIPE-SLUG/brew/BREW-SLUG
    """
    def process(self, username=None, recipe_slug=None, brew_slug=None):
        publicuser = UserPrefs.all()\
                              .filter('name =', username)\
                              .get()

        if not publicuser:
            return [None, None, None]

        recipe = Recipe.all()\
                       .filter('owner =', publicuser)\
                       .filter('slug = ', recipe_slug)\
                       .get()

        if not recipe:
            return [publicuser, None, None]

        if brew_slug is not None:
            brew = Brew.all()\
                       .filter('owner =', publicuser)\
                       .filter('recipe =', recipe)\
                       .filter('slug =', brew_slug)\
                       .get()

            if not brew:
                return [publicuser, recipe, None]
        else:
            brew = Brew()
            brew.owner = self.user
            brew.recipe = recipe

        return [publicuser, recipe, brew]

    def get(self, username=None, recipe_slug=None, brew_slug=None):
        publicuser, recipe, brew = self.process(username, recipe_slug, brew_slug)

        if not publicuser or not recipe or not brew:
            return self.abort(404)

        self.render('brew.html', {
            'publicuser': publicuser,
            'recipe': recipe,
            'brew': brew
        })

    def post(self, username=None, recipe_slug=None, brew_slug=None):
        publicuser, recipe, brew = self.process(username, recipe_slug, brew_slug)

        if not publicuser or not recipe or not brew:
            return self.abort(404)

        # Does the current user own this? If not, then fail
        if brew.owner.name != self.user.name:
            return self.abort(403)

        submitted = json.loads(cgi.escape(self.request.get('brew')))

        logging.info(submitted)

        started = submitted['started']
        bottled = submitted['bottled']

        for k, v in [('started', started), ('bottled', bottled)]:
            if v.strip():
                try:
                    d = Date(v, format="%H:%M %d %b %Y")
                except Exception, e:
                    return self.render_json({
                        'status': 'error',
                        'error': 'Could not process date "%s": %s' % (v, e)
                    })

                setattr(brew, k, d.datetime)

        brew.og = float(submitted['og'])
        brew.fg = float(submitted['fg'])
        brew.rating = submitted['rating']
        brew.notes = submitted['notes']

        brew.slug = generate_usable_slug(brew)
        key = brew.put()

        # Update recipe ranking information for sorting
        recipe.update_grade()
        recipe.put()

        # Add user action
        action = UserAction()
        action.owner = self.user
        action.object_id = key.id()

        if not brew_slug:
            action.type = action.TYPE_BREW_CREATED
        else:
            action.type = action.TYPE_BREW_UPDATED

        action.put()

        self.render_json({
            'status': 'ok'
        })
