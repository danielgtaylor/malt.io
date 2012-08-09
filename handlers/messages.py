import webapp2

from models.message import Message
from models.userprefs import UserPrefs
from util import render


class MessagesHandler(webapp2.RequestHandler):
    """
    Handle requests to the messages page, accessible via the URLs:

        /messages

    """
    def get(self):
        """
        Render the messages page. This includes all messages relevant
        to the currently logged in user.
        """
        render(self, 'messages.html')
