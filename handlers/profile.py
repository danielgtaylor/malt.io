import cgi
import settings

from google.appengine.api import memcache
from google.appengine.ext import db
from handlers.base import BaseHandler
from models.userprefs import UserPrefs
from util import render, login_required


class ProfileHandler(BaseHandler):
    """
    Profile settings request handler. This handles requests to view and modify
    the profile settings of a logged in user. It is invoked via URLs like:

        /profile

    """
    @login_required
    def get(self):
        """
        Render the profile settings page with the currently logged-in user's
        profile settings.
        """
        self.render('profile.html', {
            'success': self.request.get('success')
        })

    def post(self):
        """
        Update the currently logged-in user's profile settings, such as the
        username and email.
        """
        name = cgi.escape(self.request.get('name'))
        email = cgi.escape(self.request.get('email'))
        lat = cgi.escape(self.request.get('lat'))
        lng = cgi.escape(self.request.get('lng'))

        # Do not save unless validated - this should never happen
        # as validation happens on the page via javascript. If it does,
        # then just redirect to the profile URL
        if not name or len(name) < 4 or name in settings.RESERVED_USERNAMES:
            self.redirect('/profile')

        # Get the current user and ensure he/she exists
        user = self.user

        if not user:
            self.redirect('/profile')

        # Set the values and save to the data store
        user.name = name
        user.email = email

        if lat or lng:
            lat = float(lat)
            lng = float(lng)
            if not user.location:
                user.location = db.GeoPt(lat, lng)
            else:
                user.location.lat = lat
                user.location.lon = lng
        
        user.put()

        # Invalidate cached user list pages
        memcache.delete('users-content')

        # Redirect to show a success message to the user
        self.redirect('/profile?success=1')
