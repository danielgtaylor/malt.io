from handlers.base import BaseHandler

class PrivacyHandler(BaseHandler):
    def get(self):
        self.render('privacy.html')
