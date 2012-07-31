"""
Malt.io
=======
This is the entry point for the Malt.io backend. It creates a new WSGI
application to serve requests.
"""

import settings
import webapp2

from urls import urls

app = webapp2.WSGIApplication(urls, debug=settings.DEBUG)
