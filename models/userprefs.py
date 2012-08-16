import hashlib
import settings

from contrib.paodate import Date
from datetime import datetime
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db


class UserPrefs(db.Model):
    """
    A data model to store per-user preferences. This stores things such as
    the username, email, when the user joined, earned awards, etc and links
    them all to a global Google account ID.
    """
    # Unique ID, user-chosen name and email
    user_id = db.StringProperty()
    name = db.StringProperty()
    email = db.StringProperty()

    # The date when the user joined
    joined = db.DateProperty()

    # A list of award names given to this user
    awards = db.StringListProperty()

    # The amount this user has donated
    donated = db.FloatProperty(default=0.0)

    # Cached number of unread messages, used to display a tag by the
    # user's name when logged in.
    unread_messages = db.IntegerProperty(default=0)

    # List of user IDs that this user is following
    following = db.StringListProperty()

    @staticmethod
    def get():
        """
        Get or create the preferences database value for the
        currently logged in user. First try to get the object via
        memcache, falling back to the database and then updating
        memcache for the next time the object is needed.
        """
        from models.useraction import UserAction

        user = users.get_current_user()

        prefs = None
        if user:
            # Attempt to fetch from memcache
            prefs = memcache.get('userprefs-' + str(user.user_id()))

            # Attempt to fetch from data store
            if not prefs:
                prefs = UserPrefs.all()\
                                 .filter('user_id =', user.user_id()).get()
                memcache.add('userprefs-' + str(user.user_id()), prefs, 3600)

            # Not found yet... time to create a new one!
            if not prefs:
                # Generate a nice username from the email
                username = user.email().split('@')[0].lower().replace(' ', '')
                count = 0

                while True:
                    check_name = count and username + str(count) or username
                    if not UserPrefs.all()\
                                    .filter('name =', check_name)\
                                    .count() and check_name not in settings.RESERVED_USERNAMES:
                        if count:
                            username = username + str(count)
                        break

                    count += 1

                # Create the preferences object and store it
                prefs = UserPrefs(**{
                    'user_id': user.user_id(),
                    'name': username,
                    'email': user.email(),
                    'joined': Date().date
                })
                prefs.put()

                action = UserAction()
                action.owner = prefs
                action.type = action.TYPE_USER_JOINED
                action.put()

        return prefs

    def __repr__(self):
        """
        Return a friendly representation of this object.
        """
        return "<UserPrefs for %(name)s (%(email)s)>" % {
            'name': self.name,
            'email': self.email
        }

    def put(self, *args):
        """
        Save this object to the database, updating the memcache data as
        we do so to prevent cache misses on subsequent requests by this
        user.
        """
        super(UserPrefs, self).put(*args)

        # Update the cache, invalidating old data
        memcache.set('userprefs-' + str(self.user_id), self, 3600)

    def gravatar(self, size):
        """
        Get an avatar image link with a particular size.
        """
        hash = hashlib.md5(self.email.strip().lower()).hexdigest()
        return 'http://www.gravatar.com/avatar/%(hash)s?s=%(size)d&d=identicon' % locals()

    @property
    def gravatar_large(self):
        """
        Get an avatar image link that is 80x80px.
        """
        return self.gravatar(80)

    @property
    def gravatar_small(self):
        """
        Get an avatar image link that is 40x40px.
        """
        return self.gravatar(40)

    @property
    def gravatar_tiny(self):
        """
        Get an avatar image link that is 14x14, useful for menus.
        """
        return self.gravatar(14)

    @property
    def following_users(self):
        """
        Get a list of UserPref objects for the users that this user is
        currently following.
        """
        return UserPrefs.all()\
                        .filter('user_id IN', self.following)

    @property
    def top_interesting_recipes(self):
        """
        Get a list of the top recipes that are interesting for this user,
        meaning that either the recipes belong to this user or any user
        that she is following. The list is ranked by the number of likes
        that each recipe has.
        """
        from models.recipe import Recipe

        following = self.following_users.run(batch_size=100)

        return Recipe.all()\
                     .filter('owner IN', [self] + list(following))\
                     .order('-likes_count')\
                     .fetch(15)

    @property
    def top_interesting_events(self):
        """
        Get a list of interesting events ordered by date from most
        recent to least. Interesting events are events that either belong
        to this user or any user she is following.
        """
        from models.useraction import UserAction

        following = self.following_users.run(batch_size=100)

        return UserAction.all()\
                         .filter('owner IN', [self] + list(following))\
                         .order('-created')\
                         .fetch(50)

    @property
    def brewdays(self):
        """
        Get a query of brewday objects for this user.
        TODO: Implement this.
        """
        return []
