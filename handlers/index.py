import logging
import settings

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.db import Key
from handlers.base import BaseHandler
from models.recipe import Recipe
from models.useraction import UserAction
from models.userprefs import UserPrefs
from util import login_required


class MainHandler(BaseHandler):
    """
    Handle requests to the index page, i.e. http://www.malt.io/
    """
    # Time in seconds to cache parts of the page
    CACHE_TIME = 2 * 60 * 60

    def get(self):
        """
        Render the index page. Currently this renders a 'Coming soon' landing
        page that will eventually be replaced with a proper home page.
        """
        # Try to get recipes list from memcache instead of datastore
        recipes_html = memcache.get('index-recipes')
        if not recipes_html or settings.DEBUG:
            # No such luck... query the data store
            recipes = Recipe.all()\
                            .order('-grade')\
                            .run(limit=15)
            recipes_html = self.render('index-recipes.html', {
                'recipes': recipes
            }, write_to_stream=False)
            memcache.set('index-recipes', recipes_html, self.CACHE_TIME)

        self.render('index.html', {
            'recipes_html': recipes_html
        })


class AboutHandler(BaseHandler):
    """A basic about page"""
    def get(self):
        self.render('about.html')


class DashboardHandler(BaseHandler):
    """
    Render the user's dashboard with info about her recipes, followers,
    actions, etc.
    """
    # Time in seconds to cache parts of the page
    CACHE_TIME = 60
    
    @login_required
    def get(self):
        user = self.user

        # Try to get rendered output from memcache
        rendered = memcache.get('dashboard-' + user.user_id)
        if rendered and not settings.DEBUG:
            return self.response.out.write(rendered)

        # Fetch following users
        following = user.following_users\
                        .order('name')\
                        .fetch(100)

        user_keys = [user.key()] + [u.key() for u in following]

        # Start async fetch of top recipes
        top_recipes = Recipe.all()\
                            .filter('owner IN', user_keys)\
                            .order('-grade')\
                            .run(limit=15)

        # Get and process interesting events
        interesting_events = UserAction.all()\
                                       .filter('owner IN', user_keys)\
                                       .order('-created')\
                                       .fetch(15)

        object_ids = UserAction.gather_object_ids(interesting_events)
        object_ids['users'] = [id for id in object_ids['users'] if id not in [user.key().id()] + user.following]

        # Start async fetch of relevant recipes
        recipes = db.get_async([Key.from_path('Recipe', id) for id in object_ids['recipes']])

        # Start async fetch of relevant brews
        brews = db.get_async([Key.from_path('Brew', id) for id in object_ids['brews']])

        # Convert iterators to  lists of items in memory and setup a map
        # of user id -> user for easy lookups
        following = list(following)
        top_recipes = list(top_recipes)

        user_map = {
            user.key().id(): user
        }

        for u in following:
            user_map[u.key().id()] = u

        if object_ids['users']:
            for u in UserPrefs.get_by_id(object_ids['users']):
                user_map[u.key().id()] = u

        # Setup a map of brew id -> brew for easy lookups
        brew_map = {}
        brew_recipe_ids = set()

        for b in brews.get_result():
            brew_recipe_ids.add(b.recipe_key.id())
            brew_map[b.key().id()] = b

        # Async fetch of any recipes brews reference that weren't
        # included in the recipe fetch above...
        brew_recipes = db.get_async([Key.from_path('Recipe', id) for id in brew_recipe_ids if id not in object_ids['recipes']])

        # Setup a map of recipe id -> recipe for easy lookups
        recipe_map = {}

        for r in recipes.get_result():
            recipe_map[r.key().id()] = r

        for r in brew_recipes.get_result():
            recipe_map[r.key().id()] = r

        # Render and cache for 1 minute
        memcache.set('dashboard-' + user.user_id, self.render('dashboard.html', {
            'following': following,
            'user_map': user_map,
            'recipe_map': recipe_map,
            'brew_map': brew_map,
            'top_recipes': top_recipes,
            'interesting_events': interesting_events
        }), self.CACHE_TIME)
