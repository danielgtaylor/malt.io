"""
Malt.io
=======
This is the entry point for the Malt.io backend. It creates a new WSGI
application to serve requests.
"""

import logging
import settings
import webapp2

from models.userprefs import UserPrefs
from urls import urls
from util import get_template
from webapp2_extras import sessions


config = {
    'webapp2_extras.sessions': {
        'secret_key': settings.COOKIE_SECRET
    }
}


def handle_error(request, response, exception, code, msg):
    """
    Render an error template with a code and message.
    """
    logging.exception(exception)

    # Try to get the current user
    session_store = sessions.get_store(request=request)
    session = session_store.get_session()
    auth_id = session.get('auth_id')
    user = None
    if auth_id:
        user = UserPrefs.get(auth_id)

    if user:
        logging.error('Currently logged in user is ' + user.name + ' (' + user.email + ')')

    # Render and error template
    template = get_template('error.html')
    response.status = code
    response.out.write(template.render({
        'user': user,
        'code': code,
        'message': msg
    }))


def handle_404(request, response, exception):
    handle_error(request, response, exception,
                 404, 'the page could not be found')


def handle_500(request, response, exception):
    handle_error(request, response, exception,
                 500, 'there was an internal server error')


app = webapp2.WSGIApplication(urls, config=config, debug=settings.DEBUG)

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500
