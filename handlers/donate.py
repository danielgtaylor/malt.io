import cgi
import settings
import webapp2

from contrib import stripe
from models.userprefs import UserPrefs
from util import render


class DonateHandler(webapp2.RequestHandler):
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

        render(self, 'donate.html', {
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
            'top_users': top_users,
            'success': self.request.get('success')
        })

    def post(self):
        """
        Process a donation payment given a Stripe single-use token.
        """
        user = UserPrefs.get()
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

        # Add an award to this user for donating
        user = UserPrefs.get()
        if user and 'donated' not in user.awards:
            user.awards.append('donated')
            user.put()

        return webapp2.redirect('/donate?success=true')
