import json

from google.appengine.ext import db
from models.userprefs import UserPrefs


class RecipeBase(db.Model):
    """
    A data model to store information about a single recipe. This stores
    things like the owner, creation date, name, size, ingredients, etc.

    The ingredients themselves are stored as a serialized JSON string.
    A property handler converts this to Python objects behind the
    scenes to make working with the recipe ingredients easier.

    This class is a common base for both the latest version of recipe
    data and hitorical versions, which are stored in a separate table.
    """
    # Possible recipe types, which can be useful to filter on because
    # they require different equipment.
    TYPE_EXTRACT = 0
    TYPE_PARTIAL_MASH = 1
    TYPE_ALL_GRAIN = 3

    # The recipe name and description
    name = db.StringProperty(default='Untitled Brew')
    description = db.StringProperty(default='No description')

    # The recipe type, one of the constants above like TYPE_EXTRACT
    type = db.IntegerProperty()

    # The BJCP Style that this recipe is matching, if any
    style = db.StringProperty(default='None')

    # Batch and average boil sizes in gallons
    batch_size = db.FloatProperty(default=5.0)
    boil_size = db.FloatProperty(default=5.5)

    # Bottling temperature in F and pressure in volumes
    bottling_temp = db.FloatProperty(default=70.0)
    bottling_pressure = db.FloatProperty(default=2.5)

    # Serialized JSON data for the ingredients
    _ingredients = db.TextProperty(default=json.dumps({
        'fermentables': [],
        'spices': [],
        'yeast': []
    }))

    @property
    def ingredients(self):
        """
        Get a deserialized object from the recipe ingredient JSON.
        """
        if not hasattr(self, '_ingredients_decoded'):
            self._ingredients_decoded = json.loads(self._ingredients)

        return self._ingredients_decoded

    @ingredients.setter
    def ingredients(self, value):
        """
        Automatically serialize an ingredients object to JSON.
        """
        self._ingredients = json.dumps(value)
        self._ingredients_decoded = value


class Recipe(RecipeBase):
    # URL-friendly name by which this recipe can be referenced
    slug = db.StringProperty()

    # The user who owns this recipe
    owner = db.ReferenceProperty(UserPrefs)

    # Created and edited date/time, automatically populated
    created = db.DateTimeProperty(auto_now_add=True)
    edited = db.DateTimeProperty(auto_now=True)

    # A parent recipe if this one was cloned from another recipe
    cloned_from = db.SelfReferenceProperty()

    # Cached data about color, bitterness, and alcohol to make searching
    # and displaying stats easier
    color = db.IntegerProperty(default=1)
    ibu = db.FloatProperty(default=0.0)
    alcohol = db.FloatProperty(default=0.0)

    # Users who have liked tihs recipe
    likes = db.StringListProperty()

    @property
    def url(self):
        return '/users/%(username)s/recipes/%(slug)s' % {
            'username': self.owner.name,
            'slug': self.slug
        }

    def put_historic_version(self):
        """
        Save a historic version of this recipe in the data store. The contents
        of this recipe are copied to the RecipeHistory store with a link back
        to this recipe.
        """
        history = RecipeHistory(**{
            'parent_recipe': self,
            'created': self.created,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'style': self.style,
            'batch_size': self.batch_size,
            'boil_size': self.boil_size,
            'bottling_temp': self.bottling_temp,
            'bottling_pressure': self.bottling_pressure,
            '_ingredients': self._ingredients
        })
        history.put()


class RecipeHistory(RecipeBase):
    # The parent recipe that this is a historic version of
    parent_recipe = db.ReferenceProperty(Recipe)

    created = db.DateTimeProperty()
