# A class to handle donation payments. This makes use of
# [Stripe](http://www.stripe.com/) to handle payment processing.
class Donate
    # Initialize the payments form and event handlers
    @init: (key) =>
        Stripe.setPublishableKey(key)

        $('#payment-form').submit((event) =>
            # Disable the submit button to prevent repeat clicks
            $('.submit-button').attr('disabled', 'disabled').addClass('disabled')

            Stripe.createToken(
                number: $('.card-number').val()
                cvc: $('.card-cvc').val()
                exp_month: $('.card-expiry-month').val()
                exp_year: $('.card-expiry-year').val()
            , @tokenCreated)

            # Prevent form from submitting
            return false
        )

        # Redirecto to paypal when clicked
        $('#donatePaypal').click((event) =>
            window.location.href = 'https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=AGZZE7H3LL442'
            return false
        )

    # A Stripe token has been created. Use it to post data to the server
    # and make the actual charge to the customer's card.
    @tokenCreated: (status, response) =>
        if response.error
            # Show errors on the form
            $('.payment-errors').text(response.error.message)
            $('.submit-button').removeAttr('disabled').removeClass('disabled')
        else
            form = $('#payment-form')
            form.append('<input type="hidden" name="stripeToken" value="' + response.id + '"/>')
            form.get(0).submit()
