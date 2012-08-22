import webapp2

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
            following = user.following_users.order('name')
            user_map = {
                user.key().id(): user
            }

            for u in following:
                user_map[u.key().id()] = u

            interesting_events = UserAction.all()\
                                           .filter('owner IN', [user] + list(following))\
                                           .order('-created')\
                                           .fetch(15)

            render(self, 'dashboard.html', {
                'following': following,
                'user_map': user_map,
                'interesting_events': interesting_events
            })
        else:
            recipes = Recipe.all()\
                            .order('-likes_count')\
                            .fetch(15)
            render(self, 'index.html', {
                'recipes': recipes
            })
