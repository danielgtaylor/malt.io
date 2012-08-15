import webapp2

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
            render(self, 'dashboard.html')
        else:
            render(self, 'index.html')
