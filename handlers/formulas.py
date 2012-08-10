import webapp2

from util import render


class FormulasHandler(webapp2.RequestHandler):
    """
    Handle requests to the formulas page, accessible via the URLs:

        /homebrew-formulas

    """
    def get(self):
        """
        Render the formulas page. This describes various homebrewing
        formulas that are used by Malt.io
        """
        render(self, 'formulas.html')
