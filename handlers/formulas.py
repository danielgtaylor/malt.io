from handlers.base import BaseHandler


class FormulasHandler(BaseHandler):
    """
    Handle requests to the formulas page, accessible via the URLs:

        /homebrew-formulas

    """
    def get(self):
        """
        Render the formulas page. This describes various homebrewing
        formulas that are used by Malt.io
        """
        self.render('formulas.html')
