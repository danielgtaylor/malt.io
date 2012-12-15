import json
import webapp2

from google.appengine.api import memcache
from models.userprefs import UserPrefs
from util import render, render_json
from webapp2_extras import sessions


class BaseHandler(webapp2.RequestHandler):
    """
    A base request handler to simplify various things, like rendering output
    via templates or as JSON, giving access to user information and
    setting up sessions via cookies.
    """
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            super(BaseHandler, self).dispatch()
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        """Returns a session using the default cookie key"""
        return self.session_store.get_session()

    @webapp2.cached_property
    def user(self):
        """Returns currently logged in user"""
        user = None
        auth_id = self.session.get('auth_id')

        # Do we have user session info set by auth handler?
        if auth_id:
            user = UserPrefs.get(auth_id)

            if not user:
                del self.session['auth_id']

        return user

    @webapp2.cached_property
    def logged_in(self):
        """Returns true if a user is currently logged in, false otherwise"""
        return self.session.get('auth_id') is not None

    def render(self, template, params=None, write_to_stream=True):
        """Render a template"""
        return render(self, template, params, write_to_stream)

    def render_json(self, value):
        """Render JSON output, including proper headers"""
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(value))

    def render_xml(self, value):
        """Render XML output, including proper headers"""
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write(value)
