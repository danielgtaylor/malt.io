import logging

from google.appengine.ext import db
from models.recipe import Recipe
from models.userprefs import UserPrefs


class Brew(db.Model):
    """
    An instance of a particular recipe, brewed on a specific day.
    """
    # The user who owns this recipe, and any cobrewers
    owner = db.ReferenceProperty(UserPrefs, collection_name='brews')

    # The recipe from which this brew was created
    recipe = db.ReferenceProperty(Recipe, collection_name='brews')

    # Unique URL-friendly identifier
    slug = db.StringProperty()

    # The date / time this brew was created, finished, etc
    started = db.DateTimeProperty()
    bottled = db.DateTimeProperty()

    # Measurements
    og = db.FloatProperty()
    fg = db.FloatProperty()

    # Rating and notes
    rating = db.IntegerProperty()
    notes = db.TextProperty()

    @property
    def owner_key(self):
        return Brew.owner.get_value_for_datastore(self)

    @property
    def recipe_key(self):
        return Brew.recipe.get_value_for_datastore(self)

    @property
    def notes_safe(self):
        """Return a safe version of the notes for use in javascript"""
        return self.notes.replace('\n', '\\n').replace('\'', '\\\'').replace('"', '&quot;')
