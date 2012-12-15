import hashlib
import json
import logging
import settings
import urlparse
import uuid

from google.appengine.api import urlfetch
from handlers.base import BaseHandler
from models.userprefs import UserPrefs
from urllib import urlencode


# URLs to authorize and get a token using OAuth2
AUTH_URLS = {
    'google': [
        'https://accounts.google.com/o/oauth2/auth?{0}',
        'https://accounts.google.com/o/oauth2/token'
    ],
    'facebook': [
        'https://www.facebook.com/dialog/oauth?{0}',
        'https://graph.facebook.com/oauth/access_token'
    ],
    'windows_live': [
        'https://login.live.com/oauth20_authorize.srf?{0}',
        'https://login.live.com/oauth20_token.srf'
    ]
}


class LoginHandler(BaseHandler):
    """
    Log into the site. Show the user a list of login options and let her
    initiate the OAuth 2 process.
    """
    def get(self):
        self.render('login.html')


class LogoutHandler(BaseHandler):
    """
    Log out of the site. This clears the session and redirects
    the user to the main page.
    """
    def get(self):
        if 'auth_id' in self.session:
            del self.session['auth_id']

        self.redirect('/')


class AuthError(Exception):
    """Generic base authentication error"""
    pass


class AuthProviderResponseError(AuthError):
    """Error coming from a provider"""
    pass


class BaseAuthHandler(BaseHandler):
    def callback_url(self, provider):
        return self.request.host_url + '/auth/' + provider + '/callback'


class AuthHandler(BaseAuthHandler):
    def get(self, provider=None):
        """
        Handle login initiation via a known OAuth 2 provider.
        """
        if settings.DEBUG and provider == "dummy":
            # Handle test dev login
            auth_id = 'dummy:test'
            u = UserPrefs.create_or_update(auth_id, {
                'id': '1234',
                'name': 'Test User',
                'email': 'test@example.com',
                'avatar': 'http://www.gravatar.com/avatar/55502f40dc8b7c769880b10874abc9d0?s={0}&d=identicon'
            }, {})

            # Give dev admin
            if not u.awards:
                u.awards.append('admin')

            u.put()

            # Update session
            self.session['auth_id'] = auth_id

            return self.redirect(self.session.pop('next', '/dashboard'))

        auth_url = AUTH_URLS[provider][0]

        key = getattr(settings, provider.upper() + '_OAUTH_KEY')
        scope = getattr(settings, provider.upper() + '_OAUTH_SCOPE')

        # Generate a random state parameter to prevent CSRF attacks
        # This is both stored in the session and sent to the authorizing
        # server, relayed back and then checked to make sure it matches
        # up. If not, then the request likely did not originate from
        # this site and it can be ignored.
        csrf_state = hashlib.md5(uuid.uuid4().hex).hexdigest()

        self.session['login_csrf'] = csrf_state

        params = {
            'response_type': 'code',
            'client_id': key,
            'redirect_uri': self.callback_url(provider),
            'state': csrf_state
        }

        if scope:
            params.update(scope=scope)

        target_url = auth_url.format(urlencode(params))
        logging.info('Redirecting user to %s', target_url)

        self.redirect(target_url)


class AuthCallbackHandler(BaseAuthHandler):
    def get(self, provider):
        # Did we get an error?
        error = self.request.get('error')
        if error:
            raise AuthProviderResponseError(error, provider)

        # At this point the user is successfully logged in, but we need to
        # get an access token in order to call the API which gets user
        # information like id, name, avatar, email, etc. Then we need
        # to actually call that API, and use the response to create a
        # user object within our data store.

        # Get the access code so we can exchange it for a token
        code = self.request.get('code')

        # Get the CSRF state
        state = self.request.get('state')

        if self.session['login_csrf'] != state:
            logging.warning("Login aborted due to possible CSRF!")
            return self.abort()

        # Get the access token using the access code
        key = getattr(settings, provider.upper() + '_OAUTH_KEY')
        secret = getattr(settings, provider.upper() + '_OAUTH_SECRET')

        payload = {
            'code': code,
            'client_id': key,
            'client_secret': secret,
            'redirect_uri': self.callback_url(provider),
            'grant_type': 'authorization_code'
        }

        resp = urlfetch.fetch(
            url=AUTH_URLS[provider][1],
            payload=urlencode(payload),
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if provider in ['google', 'windows_live']:
            auth_info = json.loads(resp.content)
        elif provider in ['facebook']:
            auth_info = dict(urlparse.parse_qsl(resp.content))
        else:
            raise NotImplementedError('Not sure how to parse access token response for ' + provider)

        logging.info(str(auth_info))

        # Use access token to make an API call to get user info
        user_info = getattr(self, '_' + provider + '_user_info')(auth_info)

        # Create or update a user object in the data store
        auth_id = provider + ":" + str(user_info['id'])

        UserPrefs.create_or_update(auth_id, user_info, auth_info)

        # Update session
        self.session['auth_id'] = auth_id

        self.redirect(self.session.pop('next', '/dashboard'))

    def _oauth2_request(self, url, token):
        """Perform an OAuth2 API request"""
        url = url.format(urlencode({
            'access_token': token
        }))
        response = json.loads(urlfetch.fetch(url).content)
        logging.info(response)
        return response

    def _google_user_info(self, auth_info):
        url = 'https://www.googleapis.com/oauth2/v1/userinfo?{0}'
        info = self._oauth2_request(url, auth_info['access_token'])
        return {
            'id': info['id'],
            'name': info['name'],
            'email': info['email'],
            'avatar': 'https://plus.google.com/s2/photos/profile/{0}?sz={{0}}'.format(info['id'])
        }

    def _facebook_user_info(self, auth_info):
        url = 'https://graph.facebook.com/me?{0}'
        info = self._oauth2_request(url, auth_info['access_token'])
        return {
            'id': info['id'],
            'name': info['name'],
            'email': info['email'],
            'avatar': 'http://graph.facebook.com/{0}/picture?width={{0}}&height={{0}}'.format(info['id'])
        }

    def _windows_live_user_info(self, auth_info):
        url = 'https://apis.live.net/v5.0/me?{0}'
        info = self._oauth2_request(url, auth_info['access_token'])
        return {
            'id': info['id'],
            'name': info['name'],
            'email': info['emails']['preferred'],
            'avatar': 'https://apis.live.net/v5.0/{0}/picture'.format(info['id'])
        }
