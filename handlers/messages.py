import cgi
import json

from handlers.base import BaseHandler
from models.message import Message
from models.userprefs import UserPrefs
from util import login_required


class MessagesHandler(BaseHandler):
    """
    Handle requests to the messages page, accessible via the URLs:

        /messages

    """
    @login_required
    def get(self):
        """
        Render the messages page. This includes all messages relevant
        to the currently logged in user.
        """
        self.render('messages.html')

    def post(self):
        """
        Send a new message to a user.
        """
        user = self.user

        if not user:
            return render_json(self, {
                'status': 'error',
                'error': 'User not logged in'
            })

        recipient_name = cgi.escape(self.request.get('recipient'))
        body = cgi.escape(self.request.get('body'))

        recipient = UserPrefs.all()\
                             .filter('name =', recipient_name)\
                             .get()

        if not recipient:
            return render_json(self, {
                'status': 'error',
                'error': 'Recipient %(recipient_name)s not found' % locals()
            })

        msg = Message()
        msg.user_from = user
        msg.user_to = recipient
        msg.body = body
        msg.put()

        # TODO: put this into a transaction
        recipient.unread_messages += 1
        recipient.put()

        self.render_json({
            'status': 'ok'
        })

    def put(self):
        """
        Update a message as read or unread.
        """
        message_json = cgi.escape(self.request.get('message'))

        # Parse the JSON into Python objects
        try:
            message_data = json.loads(message_json)
        except Exception, e:
            render_json(self, {
                'status': 'error',
                'error': str(e),
                'input': message_json
            })
            return

        msg = Message.get_by_id(message_data['id'])

        if not msg:
            return render_json(self, {
                'status': 'error',
                'error': 'Message %(id)s not found' % message_data
            })

        if msg.read == message_data['read']:
            return render_json(self, {
                'status': 'error',
                'error': 'Message already marked, no update needed'
            })

        # Update message read property
        msg.read = message_data['read']
        msg.put()

        # Update user unread message cache
        recipient = msg.user_to
        if msg.read:
            recipient.unread_messages -= 1
        else:
            recipient.unread_messages += 1
        recipient.put()

        self.render_json({
            'status': 'ok'
        })

    def delete(self):
        """
        Delete a message.
        """
        message_json = cgi.escape(self.request.get('message'))

        # Parse the JSON into Python objects
        try:
            message_data = json.loads(message_json)
        except Exception, e:
            render_json(self, {
                'status': 'error',
                'error': str(e),
                'input': message_json
            })
            return

        msg = Message.get_by_id(message_data['id'])

        if not msg:
            return render_json(self, {
                'status': 'error',
                'error': 'Message %(id)s not found' % message_data
            })

        # Update unread message cache if needed
        if not msg.read:
            recipient = msg.user_to
            recipient.unread_messages -= 1
            recipient.put()

        # Delete this message from the data store
        msg.delete()

        self.render_json({
            'status': 'ok'
        })
