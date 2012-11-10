import cgi
import settings
import webapp2

from contrib import stripe
from handlers.base import BaseHandler
from models.useraction import UserAction
from models.userprefs import UserPrefs


class DonateHandler(BaseHandler):
    """
    Handle requests to the donation page, accessible via the URLs:

        /donate

    This uses [Stripe](http://www.stripe.com/)
    """
    def get(self):
        """
        Render the donation page. This includes a form to process a credit
        card and show the top donating users.
        """
        # Get a list of the top 10 users who donated
        top_users = UserPrefs.all()\
                             .filter('donated >', 0)\
                             .order('-donated')\
                             .fetch(10)

        self.render('donate.html', {
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
            'top_users': top_users,
            'success': self.request.get('success')
        })

    def post(self):
        """
        Process a donation payment given a Stripe single-use token.
        """
        user = self.user
        stripe.api_key = settings.STRIPE_PRIVATE_KEY

        amount = int(cgi.escape(self.request.get('amount')))
        token = cgi.escape(self.request.get('stripeToken'))

        # Charge the amount (in cents) to the customer's card
        charge = stripe.Charge.create(**{
            'amount': amount * 100,
            'currency': 'usd',
            'card': token,
            'description': 'Donation from ' + (user and user.name or 'Anonymous')
        })

        if user:
            # Add an award to this user for donating
            if user and 'donated' not in user.awards:
                user.awards.append('donated')
                user.put()

            # Log action
            action = UserAction()
            action.owner = user
            action.type = action.TYPE_USER_DONATED
            action.put()

        self.redirect('/donate?success=true')
