import cgi
import logging
import settings
import webapp2

from google.appengine.api import memcache
from handlers.base import BaseHandler
from models.brew import Brew
from models.recipe import Recipe
from models.useraction import UserAction
from models.userprefs import UserPrefs
from util import render, render_json


class UsersHandler(BaseHandler):
    """
    Public user list handler. This handler renders the list of public
    users via the URLs:

        /users

    """
    # Time in seconds to cache parts of the page
    CACHE_TIME = 60 * 60
    def get(self):
        """
        Render the public users list.
        """
        # Try to get users list from memcache instead of datastore
        users_html = memcache.get('users-content')
        if not users_html or settings.DEBUG:
            users_html = self.render('users-content.html', {
                'users': UserPrefs.all()
            }, write_to_stream=False)
            memcache.set('users-content', users_html, self.CACHE_TIME)

        self.render('users.html', {
            'users_content': users_html
        })


class UserHandler(BaseHandler):
    """
    Public user profile page handler. This handler renders information
    about a single user via the URLs:

        /users/USERNAME

    """
    def get(self, username):
        """
        Render a user page.
        """
        publicuser = UserPrefs.all().filter('name =', username).get()

        if not publicuser:
            self.abort(404)

        recipes = Recipe.all()\
                        .filter('owner =', publicuser)\
                        .order('name')\
                        .run(limit=25)

        actions = UserAction.all()\
                            .filter('owner =', publicuser)\
                            .order('-created')\
                            .fetch(15)

        object_ids = UserAction.gather_object_ids(actions)

        user_map = {
            publicuser.key().id(): publicuser
        }

        for user in UserPrefs.get_by_id(object_ids['users']):
            user_map[user.key().id()] = user

        recipes = [r for r in recipes]
        recipe_ids = [recipe.key().id() for recipe in recipes]
        object_ids['recipes'] = [id for id in object_ids['recipes'] if id not in recipe_ids]

        recipe_map = {}

        for recipe in recipes:
            recipe.owner = publicuser
            recipe_map[recipe.key().id()] = recipe

        for recipe in Recipe.get_by_id(object_ids['recipes']):
            recipe_map[recipe.key().id()] = recipe

        brew_map = {}

        for brew in Brew.get_by_id(object_ids['brews']):
            brew_map[brew.key().id()] = brew

        self.render('user.html', {
            'publicuser': publicuser,
            'recipes': recipes,
            'actions': actions,
            'user_map': user_map,
            'recipe_map': recipe_map,
            'brew_map': brew_map
        })


class UserFollowHandler(BaseHandler):
    """
    Follow another user to see when they create or like recipes, etc via
    the following URLs:

        /users/USERNAME/follow

    """
    def post(self, username):
        self.process(username, 'post')

    def delete(self, username):
        self.process(username, 'delete')

    def process(self, username, action):
        """
        Follow the given user.
        """
        user = self.user
        publicuser = UserPrefs.all().filter('name =', username).get()

        if not user or not publicuser:
            return self.render_json({
                'status': 'error',
                'error': 'User not found'
            })

        if action == 'post':
            if publicuser.user_id in user.following:
                return self.render_json({
                    'status': 'error',
                    'error': 'Already following user'
                })

            user.following.append(publicuser.user_id)

            existing = UserAction.all()\
                                 .filter('owner =', user)\
                                 .filter('type =', UserAction.TYPE_USER_FOLLOWED)\
                                 .filter('object_id =', publicuser.key().id())\
                                 .count()

            if not existing:
                user_action = UserAction()
                user_action.owner = user
                user_action.type = user_action.TYPE_USER_FOLLOWED
                user_action.object_id = publicuser.key().id()
                user_action.put()
        else:
            if publicuser.user_id not in user.following:
                return self.render_json({
                    'status': 'error',
                    'error': 'User not being followed'
                })

            user.following.remove(publicuser.user_id)

            existing = UserAction.all()\
                                 .filter('owner =', user)\
                                 .filter('type =', UserAction.TYPE_USER_FOLLOWED)\
                                 .filter('object_id =', publicuser.key().id())\
                                 .get()

            if existing:
                existing.delete()

        # Save updated following list
        user.put()

        self.render_json({
            'status': 'ok'
        })


class UsernameCheckHandler(BaseHandler):
    """
    This handler checks a proposed username and returns information on
    whether it is valid or not. A valid username has the following rules:

     * More than three characters
     * All lowercase
     * No spaces
     * Not one of the disallowed names in settings.RESERVED_USERNAMES

    This handler is available via the URLs:

        /username

    This handler is used by the profile settings page to determine if a
    requested username can be used. Scripts on that page disable form
    submission until this call returns successful.
    """
    def post(self):
        """
        Get a proposed username and test to see whether it is valid. If so,
        return that it is available, otherwise return that it is not via a
        simple JSON response.
        """
        user = self.user

        if not user:
            self.abort(404)

        username = cgi.escape(self.request.get('username'))
        count = 0

        # Does an existing user have that username?
        if not user.name == username:
            count = UserPrefs.all().filter('name =', username).count()

        # Is the name too short or one of the disallowed names?
        if not username or len(username) < 4 \
                or username in settings.RESERVED_USERNAMES:
            count = 1

        self.render_json({
            'username': username,
            'available': count == 0
        })
