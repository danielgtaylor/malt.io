from google.appengine.ext import db
from models.userprefs import UserPrefs


class Message(db.Model):
    """
    A data model to store messages between users. Store a from/to, creation
    date and message text.
    """
    # Sender and recipient
    user_from = db.ReferenceProperty(UserPrefs, collection_name='messages_sent')
    user_to = db.ReferenceProperty(UserPrefs, collection_name='messages')

    # When this message was created
    created = db.DateTimeProperty(auto_now_add=True)

    # True if the recipient has read the message
    read = db.BooleanProperty(default=False)

    # The message text body
    body = db.TextProperty()
