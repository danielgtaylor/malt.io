from google.appengine.ext import db
from models.userprefs import UserPrefs


class UserAction(db.Model):
    """
    A data model to store actions that users take on the site. Each action is
    logged with an owner, date/time, a type and a related object ID, where the
    type defines which object ID should be
    """
    # User-related actions
    TYPE_USER_JOINED = 0
    TYPE_USER_DONATED = 1
    TYPE_USER_FOLLOWED = 2

    # Recipe-related actions
    TYPE_RECIPE_CREATED = 10
    TYPE_RECIPE_EDITED = 11
    TYPE_RECIPE_CLONED = 12
    TYPE_RECIPE_LIKED = 13

    owner = db.ReferenceProperty(UserPrefs, collection_name='actions')
    created = db.DateTimeProperty(auto_now_add=True)
    type = db.IntegerProperty()
    object_id = db.IntegerProperty()

    @property
    def owner_key(self):
        return UserAction.owner.get_value_for_datastore(self)

    @property
    def object(self):
        if self.type in [self.TYPE_USER_FOLLOWED]:
            return UserPrefs.get_by_id(self.object_id)
        elif self.type in [self.TYPE_RECIPE_CREATED,
                           self.TYPE_RECIPE_EDITED,
                           self.TYPE_RECIPE_CLONED,
                           self.TYPE_RECIPE_LIKED]:
            from models.recipe import Recipe
            return Recipe.get_by_id(self.object_id)
