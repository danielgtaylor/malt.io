import cgi
import settings
import webapp2

from models.recipe import Recipe
from models.userprefs import UserPrefs
from util import render, render_json


class UsersHandler(webapp2.RequestHandler):
    """
    Public user list handler. This handler renders the list of public
    users via the URLs:

        /users

    """
    def get(self):
        """
        Render the public users list.
        """
        render(self, 'users.html', {
            'users': UserPrefs.all()
        })


class UserHandler(webapp2.RequestHandler):
    """
    Public user profile page handler. This handler renders information
    about a single user via the URLs:

        /users/USERNAME

    """
    def get(self, username):
        """
        Render a user page.
        """
        user = UserPrefs.all().filter('name =', username).get()

        if not user:
            self.abort(404)

        recipes = Recipe.all()\
                        .filter('owner =', user)\
                        .order('-edited')\
                        .fetch(6)

        render(self, 'user.html', {
            'publicuser': user,
            'recipes': recipes
        })


class UserFollowHandler(webapp2.RequestHandler):
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
        user = UserPrefs.get()
        publicuser = UserPrefs.all().filter('name =', username).get()

        if not user or not publicuser:
            return render_json(self, {
                'status': 'error',
                'error': 'User not found'
            })

        if action == 'post':
            if publicuser.user_id in user.following:
                return render_json(self, {
                    'status': 'error',
                    'error': 'Already following user'
                })

            user.following.append(publicuser.user_id)
        else:
            if publicuser.user_id not in user.following:
                return render_json(self, {
                    'status': 'error',
                    'error': 'User not being followed'
                })

            user.following.remove(publicuser.user_id)

        # Save updated following list
        user.put()

        render_json(self, {
            'status': 'ok'
        })


class UsernameCheckHandler(webapp2.RequestHandler):
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
        user = UserPrefs.get()

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

        render_json(self, {
            'username': username,
            'available': count == 0
        })
