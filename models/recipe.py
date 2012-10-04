import json

from google.appengine.ext import db
from models.userprefs import UserPrefs
from util import time_to_min, xmlescape


GAL_TO_LITERS = 3.78541


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

    # The BJCP category / style that this recipe is matching, if any
    category = db.StringProperty(default='')
    style = db.StringProperty(default='')

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

    @property
    def style_display(self):
        if self.category and self.style:
            return self.category + ' - ' + self.style

        return 'No style'

    @property
    def beerxml(self):
        """
        Return a BeerXML 1.0 representation of this recipe.
        """
        xml = u'<?xml version="1.0" encoding="utf-8"?><RECIPES><RECIPE>'

        xml += '<VERSION>1</VERSION>'
        xml += '<NAME>' + xmlescape(self.name) + '</NAME>'
        xml += '<TYPE>Extract</TYPE>'
        xml += '<STYLE></STYLE>'
        xml += '<BREWER>' + xmlescape(self.owner.name) + '</BREWER>'
        xml += '<BATCH_SIZE>' + xmlescape(self.batch_size * GAL_TO_LITERS) + '</BATCH_SIZE>'
        xml += '<BOIL_SIZE>' + xmlescape(self.boil_size * GAL_TO_LITERS) + '</BOIL_SIZE>'
        xml += '<EFFICIENCY>75.0</EFFICIENCY>'
        
        xml += '<HOPS>'
        for hop in [spice for spice in self.ingredients['spices'] if spice['aa'] > 0]:
            xml += '<HOP>'
            xml += '<VERSION>1</VERSION>'
            xml += '<NAME>' + xmlescape(hop['description']) + '</NAME>'
            xml += '<ALPHA>' + xmlescape(hop['aa']) + '</ALPHA>'
            xml += '<AMOUNT>' + xmlescape(hop['oz'] / 35.275) + '</AMOUNT>'
            xml += '<AMOUNT_IS_WEIGHT>TRUE</AMOUNT_IS_WEIGHT>'
            xml += '<USE>' + xmlescape(hop['use'].capitalize()) + '</USE>'
            xml += '<TIME>' + xmlescape(int(time_to_min(hop['time']))) + '</TIME>'
            xml += '<FORM>' + xmlescape(hop['form'].capitalize()) + '</FORM>'
            xml += '</HOP>'
        xml += '</HOPS>'

        xml += '<FERMENTABLES>'
        for fermentable in self.ingredients['fermentables']:
            xml += '<FERMENTABLE>'
            xml += '<VERSION>1</VERSION>'
            xml += '<NAME>' + xmlescape(fermentable['description']) + '</NAME>'
            xml += '<AMOUNT>' + xmlescape(fermentable['weight'] / 2.20462) + '</AMOUNT>'
            xml += '<YIELD>' + xmlescape(fermentable['ppg'] / 46.214 / 0.01) + '</YIELD>'
            xml += '<COLOR>' + xmlescape(fermentable['color']) + '</COLOR>'
            xml += '<ADD_AFTER_BOIL>' + (fermentable['late'] and 'TRUE' or 'FALSE') + '</ADD_AFTER_BOIL>'
            xml += '</FERMENTABLE>'
        xml += '</FERMENTABLES>'

        xml += '<MISCS>'
        for misc in [spice for spice in self.ingredients['spices'] if spice['aa'] is 0]:
            xml += '<MISC>'
            xml += '<VERSION>1</VERSION>'
            xml += '<NAME>' + xmlescape(misc['description']) + '</NAME>'
            xml += '<AMOUNT>' + xmlescape(misc['oz'] / 35.275) + '</AMOUNT>'
            xml += '<AMOUNT_IS_WEIGHT>TRUE</AMOUNT_IS_WEIGHT>'
            xml += '<USE>' + xmlescape(misc['use'].capitalize()) + '</USE>'
            xml += '<TIME>' + xmlescape(int(time_to_min(misc['time']))) + '</TIME>'
            xml += '</MISC>'
        xml += '</MISCS>'

        xml += '<YEASTS>'
        for yeast in self.ingredients['yeast']:
            xml += '<YEAST>'
            xml += '<VERSION>1</VERSION>'
            xml += '<NAME>' + xmlescape(yeast['description']) + '</NAME>'
            xml += '<TYPE>' + xmlescape(yeast['type']).capitalize() + '</TYPE>'
            xml += '<FORM>' + xmlescape(yeast['form']).capitalize() + '</FORM>'
            xml += '<ATTENUATION>' + xmlescape(yeast['attenuation']) + '</ATTENUATION>'
            xml += '</YEAST>'
        xml += '</YEASTS>'

        xml += '</RECIPE></RECIPES>'

        return xml


class Recipe(RecipeBase):
    # URL-friendly name by which this recipe can be referenced
    slug = db.StringProperty()

    # The user who owns this recipe
    owner = db.ReferenceProperty(UserPrefs, collection_name='recipes')

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
    likes_count = db.IntegerProperty(default=0)

    @property
    def owner_key(self):
        return Recipe.owner.get_value_for_datastore(self)

    @property
    def url(self):
        return '/users/%(username)s/recipes/%(slug)s' % {
            'username': self.owner.name,
            'slug': self.slug
        }

    def put(self, *args):
        """
        Save this recipe, updating any caches as needed before writing
        to the data store.
        """
        # Update the cached number of likes so we can sort on this field
        # later for displaying the most popular recipes
        self.likes_count = len(self.likes)

        return super(Recipe, self).put(*args)

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
