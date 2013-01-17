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
    them all to a global account ID.

    Admin users will have an 'admin' award, which can be checked via the
    is_admin property.
    """
    # Unique ID, user-chosen name and email
    user_id = db.StringProperty()
    name = db.StringProperty()
    email = db.StringProperty()

    # URL to avatar image
    avatar = db.StringProperty()

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

    # User location
    location = db.GeoPtProperty()

    @staticmethod
    def get(auth_id):
        """
        Get or create the preferences database value for the
        currently logged in user. First try to get the object via
        memcache, falling back to the database and then updating
        memcache for the next time the object is needed.
        """
        # Attempt to fetch from memcache
        prefs = memcache.get('userprefs-' + auth_id)

        # Attempt to fetch from data store
        if not prefs:
            prefs = UserPrefs.all()\
                             .filter('user_id =', auth_id).get()

            if prefs:
                memcache.add('userprefs-' + str(auth_id), prefs)

        return prefs

    @staticmethod
    def create_or_update(auth_id, user_info, auth_info):
        """
        Create a new user or update an existing one with information such
        as id, name, email, avatar, etc.
        """
        prefs = UserPrefs.all()\
                         .filter('user_id =', auth_id)\
                         .get()

        # Backwards compatibility
        if not prefs:
            prefs = UserPrefs.all()\
                             .filter('email =', user_info['email'])\
                             .get()

            if prefs:
                if ':' not in prefs.user_id:
                    # Old-style user and the emails match, so update!
                    prefs.user_id = auth_id
                else:
                    # New-style user, ignore
                    prefs = None

        # Not found yet... time to create a new one!
        if not prefs:
            # Generate a nice username from the email
            username = user_info['email'].split('@')[0].lower().replace(' ', '')
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
                'user_id': auth_id,
                'name': username,
                'joined': Date().date,
            })

            # Write to the db so this user object gets a proper id, which
            # is required to reference it in the action created below
            prefs.put()

            from models.useraction import UserAction

            action = UserAction()
            action.owner = prefs
            action.type = action.TYPE_USER_JOINED
            action.put()

            # Invalidate cached user list pages
            memcache.delete('users-content')

        # Update fields based on latest user info
        prefs.email = user_info['email']

        # Update the avatar, except for special users
        if prefs.name not in ['examples']:
            prefs.avatar = user_info['avatar']

        prefs.put()

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

    def name_crop(self, length=18):
        name = self.name

        if len(name) > length:
            name = name[:length - 3] + u'\u2026'

        return name

    @property
    def is_admin(self):
        return 'admin' in self.awards

    def avatar_size(self, size):
        if self.avatar:
            return self.avatar.format(size)
        else:
            hash = hashlib.md5(self.email.strip().lower()).hexdigest()
            return 'http://www.gravatar.com/avatar/%(hash)s?s=%(size)d&d=identicon' % locals()

    @property
    def avatar_large(self):
        return self.avatar_size(80)

    @property
    def avatar_small(self):
        return self.avatar_size(40)

    @property
    def avatar_tiny(self):
        return self.avatar_size(14)

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
                         .fetch(25)

    @property
    def brewdays(self):
        """
        Get a query of brewday objects for this user.
        TODO: Implement this.
        """
        return []
