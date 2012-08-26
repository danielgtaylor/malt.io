import webapp2

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.db import Key
from models.recipe import Recipe
from models.useraction import UserAction
from models.userprefs import UserPrefs
from util import render


class MainHandler(webapp2.RequestHandler):
    """
    Handle requests to the index page, i.e. http://www.malt.io/
    """

    def get(self):
        """
        Render the index page. Currently this renders a 'Coming soon' landing
        page that will eventually be replaced with a proper home page.
        """
        user = UserPrefs.get()

        if user:
            # Try to get rendered output from memcache
            rendered = memcache.get('dashboard-' + user.user_id)
            if rendered:
                return self.response.out.write(rendered)

            # Fetch following users
            following = user.following_users\
                            .order('name')\
                            .fetch(100)

            user_keys = [user.key()] + [u.key() for u in following]

            # Start async fetch of top recipes
            top_recipes = Recipe.all()\
                                .filter('owner IN', user_keys)\
                                .order('-likes_count')\
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

            # Setup a map of recipe id -> recipe for easy lookups
            recipe_map = {}

            for r in recipes.get_result():
                recipe_map[r.key().id()] = r

            # Render and cache for 1 minute
            memcache.set('dashboard-' + user.user_id, render(self, 'dashboard.html', {
                'following': following,
                'user_map': user_map,
                'recipe_map': recipe_map,
                'top_recipes': top_recipes,
                'interesting_events': interesting_events
            }), 60)
        else:
            # Try to get rendered output from memcache
            rendered = memcache.get('index')
            if rendered:
                return self.response.out.write(rendered)

            recipes = Recipe.all()\
                            .order('-likes_count')\
                            .fetch(15)

            # Render and cache for 15 minutes
            memcache.set('index', render(self, 'index.html', {
                'recipes': recipes
            }), 900)
