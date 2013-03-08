import json
import logging
import math
import re
import xml.etree.ElementTree as et

from google.appengine.ext import db
from models.userprefs import UserPrefs
from util import time_to_min, xmlescape, GAL_TO_LITERS, LB_TO_KG


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
    RE_STEEP = re.compile(r'biscuit|black|cara|chocolate|crystal|munich|roast|special ?b|toast|victory|vienna|steep', re.I)
    RE_BOIL = re.compile(r'candi|candy|dme|dry|extract|honey|lme|liquid|sugar|syrup|turbinado|boil', re.I)

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

    # Efficiencies
    mash_efficiency = db.IntegerProperty(default=75)
    steep_efficiency = db.IntegerProperty(default=50)

    # Mash, ferment, and aging info
    _mash = db.TextProperty(default=json.dumps({
        'type': 'singleinfusion',
        'water_ratio': 1.25,
        'steps': [
            {
                'name': 'Starch conversion rest',
                'duration': 60,
                'temperature': 154
            }
        ],
        'mashout': 170,
        'sparge': 0.5
    }))
    primary_days = db.IntegerProperty(default=14)
    primary_temp = db.FloatProperty(default=68.0)
    secondary_days = db.IntegerProperty(default=0)
    secondary_temp = db.FloatProperty(default=32.0)
    tertiary_days = db.IntegerProperty(default=0)
    tertiary_temp = db.FloatProperty(default=32.0)
    aging_days = db.IntegerProperty(default=14)

    # Serialized JSON data for the ingredients
    _ingredients = db.TextProperty(default=json.dumps({
        'fermentables': [],
        'spices': [],
        'yeast': []
    }))

    @property
    def mash(self):
        """
        Get deserialized object from the recipe mash JSON.
        """
        if not hasattr(self, '_mash_decoded'):
            self._mash_decoded = json.loads(self._mash)

        return self._mash_decoded

    @mash.setter
    def mash(self, value):
        """
        Automatically serialize a mash object to JSON.
        """
        self._mash = json.dumps(value)
        self._mash_decoded = value

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
        xml += '<EFFICIENCY>' + xmlescape(self.mash_efficiency) + '</EFFICIENCY>'
        
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
            if 'late' not in fermentable:
                fermentable['late'] = False

            xml += '<FERMENTABLE>'
            xml += '<VERSION>1</VERSION>'
            xml += '<NAME>' + xmlescape(fermentable['description']) + '</NAME>'
            xml += '<AMOUNT>' + xmlescape(fermentable['weight'] * LB_TO_KG) + '</AMOUNT>'
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

    def update_cache(self):
        """
        Update the recipe's cache of color, bitterness, alcohol, etc.
        This is a reimplementation of static/scripts/main/recipe.coffee and
        should not be modified without also modifying that file!

            >>> r = Recipe()
            >>> r.ingredients['fermentables'] += [{'weight': 6.0, 'description': 'Extra pale liquid extract', 'late': '', 'ppg': 37, 'color': 2}, {'weight': 0.5, 'description': 'Caramel 40L', 'late': '', 'ppg': 34, 'color': 40}]
            >>> r.ingredients['spices'] += [{'use': 'boil', 'time': '60', 'oz': 1.0, 'description': '', 'form': 'pellet', 'aa': 4.0}, {'use': 'boil', 'time': '15', 'oz': 0.5, 'description': '', 'form': 'pellet', 'aa': 3.5}]
            >>> r.ingredients['yeast'].append({'description': '', 'form': 'pellet', 'attenuation': 80})
            >>> r.update_cache()
            >>> r.alcohol
            4.9
            >>> r.ibu
            18.2
            >>> r.color
            5

        """
        mashing = False
        for fermentable in self.ingredients['fermentables']:
            desc = fermentable['description']
            if 'mash' in desc or not ((self.RE_STEEP.search(desc) or self.RE_BOIL.search(desc))):
                mashing = True
                break

        gu, early_gu, mcu = 0, 0, 0

        for fermentable in self.ingredients['fermentables']:
            weight = fermentable['weight']
            mcu += fermentable['color'] * weight / self.batch_size
            gravity = fermentable['ppg'] * weight / self.batch_size

            forced = False
            if 'mashed' in fermentable['description']:
                forced = True
                addition = 'mash'
            elif 'steep' in fermentable['description']:
                forced = True
                addition = 'steep'
            elif 'boil' in fermentable['description']:
                forced = True
                addition = 'boil'
            elif self.RE_BOIL.search(fermentable['description']):
                addition = 'boil'
            elif self.RE_STEEP.search(fermentable['description']):
                addition = 'steep'
            else:
                addition = 'mash'

            if mashing and addition == 'steep' and not forced:
                addition = 'mash'

            if addition == 'steep':
                gravity *= (self.steep_efficiency / 100.0)
            elif addition == 'mash':
                gravity *= (self.mash_efficiency / 100.0)

            if 'late' not in fermentable or fermentable['late'] not in ['y', 'yes', 'x']:
                early_gu += gravity

            gu += gravity

        gu = 1.0 + (gu / 1000.0)
        early_gu = 1.0 + (early_gu / 1000.0)

        attenuation = 0
        for yeast in self.ingredients['yeast']:
            if yeast['attenuation'] > attenuation:
                attenuation = yeast['attenuation']

        if not attenuation:
            attenuation = 75

        fg = gu - ((gu - 1.0) * attenuation / 100.0)
        abv = ((1.05 * (gu - fg)) / fg) / 0.79 * 100.0

        bottle = 3.55 # 355 ml, aka standard 12oz bottle
        gu_plato = (-463.37) + (668.72 * gu) - (205.35 * (gu * gu))
        fg_plato = (-463.37) + (668.72 * fg) - (205.35 * (fg * fg))
        real_extract = (0.1808 * gu_plato) + (0.8192 * fg_plato)
        abw = 0.79 * abv / fg
        calories = max(0, ((6.9 * abw) + 4.0 * (real_extract - 0.10)) * fg * bottle)

        ibu = 0
        for hop in self.ingredients['spices']:
            if not hop['aa'] or hop['use'].lower() != 'boil':
                continue

            utilization_factor = 1.0
            if hop['form'] == 'pellet':
                utilization_factor = 1.15

            time = int(''.join([char for char in hop['time'] if char.isdigit()]))
            b = 1.65 * pow(0.000125, early_gu - 1.0) * ((1.0 - pow(2.718, -0.04 * time)) / 4.15) * ((hop['aa'] / 100.0 * hop['oz'] * 7490.0) / self.boil_size) * utilization_factor
            ibu += b

        self.color = int(round(1.4922 * pow(mcu, 0.6859)))
        self.ibu = round(ibu, 1)
        self.alcohol = round(abv, 1)
        self.calories = int(round(calories))

    def diff(self, other, full=True):
        """
        Return the differences between this version of a recipe and another.
        The other recipe will be considered the older version for the purpose
        of reporting additions and deletions. Three dictionaries will be
        returned: additions, deletions, and modifications. Each dictionary key
        corresponds to a field name, and the value depends on the type of
        field. For the modifications dictionary, all values are tuples of
        (from, to) pairs.

        An example return value is as follows:

        additions: {
            ingredients: {
                fermentables: ['Flaked wheat', 'Acidulated malt'],
                spices: ['Orange peel']
            }
        },

        deletions: {
            ingredients: {
                spices: ['Coriander']
            }
        },

        modifications: {
            ingredients: {
                yeast: {
                    'Wyeast 3944 - Belgian Witbier\u2122': {'attenuation': (70, 74)}
                }
            },
            name: ('Biere Blanche a l'Orange', 'Biere Blanche a l'Oranges'),
            batch_size: (3.0, 3.5)
        }
        """
        additions = {}
        deletions  = {}
        modifications = {}

        # First check the overall properties
        properties = ('name', 'description', 'type', 'category', 'style', 'batch_size',
                      'boil_size', 'bottling_temp', 'bottling_pressure', 'mash_efficiency',
                      'steep_efficiency', 'primary_days', 'primary_temp', 'secondary_days',
                      'secondary_temp', 'tertiary_days', 'tertiary_temp', 'aging_days')
        for p in properties:
            oldVal = getattr(other, p, None)
            newVal = getattr(self, p, None)
            if oldVal != newVal:
                if oldVal is None:
                    additions[p] = newVal
                elif newVal is None:
                    deletions[p] = oldVal
                else:
                   modifications[p] = (oldVal, newVal)

        # Now that the easy checks are over, time to check the ingredients
        newIngredientSet = set(key for key in self.ingredients)
        oldIngredientSet = set(key for key in other.ingredients)

        # Ingredient types found in both recipes (e.g. fermentables)
        for type in newIngredientSet.intersection(oldIngredientSet):
            # Create dictionaries using the ingredient description as the key
            # for easier processing later
            newIngredients = {ingredient['description']: ingredient for ingredient in self.ingredients[type]}
            oldIngredients = {ingredient['description']: ingredient for ingredient in other.ingredients[type]}

            # Create new and old sets to find what changed
            newSet = set(newIngredients.keys())
            oldSet = set(oldIngredients.keys())

            # Ingredients found in both recipes
            for ingredient in newSet.intersection(oldSet):
                # If we're doing a full compare, find exactly which ingredients
                # were modified. Otherwise, just return the ingredient
                # description, since that's all that matters.
                if full:
                    # Compare all values of the ingredients, yay another loop!
                    for prop in newIngredients[ingredient]:
                        if prop not in oldIngredients[ingredient]:
                            oldIngredients[ingredient][prop] = ''
                        if newIngredients[ingredient][prop] != oldIngredients[ingredient][prop]:
                            # Make the dictionary chain if necessary
                            if not 'ingredients' in modifications:
                                modifications['ingredients'] = {}

                            if not type in modifications['ingredients']:
                                modifications['ingredients'][type] = {}

                            if not ingredient in modifications['ingredients'][type]:
                                modifications['ingredients'][type][ingredient] = {}

                            # Finally set the value
                            modifications['ingredients'][type][ingredient][prop] = (
                                oldIngredients[ingredient][prop],
                                newIngredients[ingredient][prop]
                            )
                elif newIngredients[ingredient] != oldIngredients[ingredient]:
                    # Make the dictionary chain if necessary
                    if not 'ingredients' in modifications:
                        modifications['ingredients'] = {}

                    if not type in modifications['ingredients']:
                        modifications['ingredients'][type] = []

                    modifications['ingredients'][type].append(ingredient)

            # Ingredients found only in the new recipe
            for ingredient in newSet.difference(oldSet):
                # Make the dictionary chain if necessary
                if not 'ingredients' in additions:
                    additions['ingredients'] = {}

                if not type in additions['ingredients']:
                    additions['ingredients'][type] = []

                # Finally set the value
                additions['ingredients'][type].append(ingredient)

            # Ingredients found only in the old recipe
            for ingredient in oldSet.difference(newSet):
                # Make the dictionary chain if necessary
                if not 'ingredients' in deletions:
                    deletions['ingredients'] = {}

                if not type in deletions['ingredients']:
                    deletions['ingredients'][type] = []

                # Finally set the value
                deletions['ingredients'][type].append(ingredient)

        # Ingredient sets found only in the new recipe
        for type in newIngredientSet.difference(oldIngredientSet):
            # Make the dictionary chain if necessary
            if not 'ingredients' in additions:
                additions['ingredients'] = {}

            if not type in additions['ingredients']:
                additions['ingredients'][type] = []

            for ingredient in self.ingredients[type]:
                # Finally set the value
                additions['ingredients'][type].append(ingredient['description'])

        # Ingredient sets found only in the old recipe
        for type in oldIngredientSet.difference(newIngredientSet):
            # Make the dictionary chain if necessary
            if not 'ingredients' in deletions:
                deletions['ingredients'] = {}

            if not type in deletions['ingredients']:
                deletions['ingredients'][type] = []

            for ingredient in self.ingredients[type]:
                # Finally set the value
                deletions['ingredients'][type].append(ingredient['description'])

        # Only compare color, ibu, and alcohol if we suspect they might be
        # different. They are affected by batch_size, boil_size, and ingedients.
        if 'batch_size' in additions or \
           'boil_size' in additions or \
           'ingredients' in additions or \
           'batch_size' in deletions or \
           'boil_size' in deletions or \
           'ingredients' in deletions or \
           'batch_size' in modifications or \
           'boil_size' in modifications or \
           'ingredients' in modifications or \
           'mash_efficiency' in modifications or \
           'steep_efficiency' in modifications:

            # Update the caches if needed
            if not hasattr(self, 'color'):
                self.update_cache()
            if not hasattr(other, 'color'):
                other.update_cache()

            # Compare color, ibu, and alcohol
            properties = ('color', 'ibu', 'alcohol')
            for p in properties:
                oldVal = getattr(other, p, None)
                newVal = getattr(self, p, None)
                if oldVal != newVal:
                    modifications[p] = (oldVal, newVal)


        return additions, deletions, modifications


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
    calories = db.IntegerProperty(default=0)

    # Grade: a generated rating for this recipe, see update_grade()
    grade = db.FloatProperty(default=0.0)

    review_count = db.IntegerProperty(default=0)
    avg_review = db.FloatProperty(default=0.0)

    @staticmethod
    def new_from_beerxml(data):
        """
        Get a list of new recipe objects from BeerXML input.
        """
        new_recipes = []
        recipes = et.fromstring(data)

        for recipe in recipes.iter('RECIPE'):
            r = Recipe()
            ingredients = r.ingredients

            for recipe_member in recipe:
                tag = recipe_member.tag.strip().lower()
                logging.info(tag)
                if tag == 'name':
                    r.name = recipe_member.text.replace('\n', ' ')
                elif tag == 'batch_size':
                    r.batch_size = round(float(recipe_member.text) / GAL_TO_LITERS, 2)
                elif tag == 'boil_size':
                    r.boil_size = round(float(recipe_member.text) / GAL_TO_LITERS, 2)
                elif tag in ['hops', 'miscs']:
                    for hop in recipe_member:
                        h = {
                            'description': '',
                            'oz': 0.0,
                            'aa': 0.0,
                            'use': 'boil',
                            'time': '0',
                            'form': 'pellet'
                        }
                        for hop_member in hop:
                            tag = hop_member.tag.lower()
                            if tag == 'name':
                                h['description'] = hop_member.text
                            elif tag == 'amount':
                                h['oz'] = round(float(hop_member.text) * 2.20462 * 16, 2)
                            elif tag == 'alpha':
                                h['aa'] = round(float(hop_member.text), 1)
                            elif tag == 'use':
                                h['use'] = hop_member.text
                            elif tag == 'time':
                                h['time'] = hop_member.text
                            elif tag == 'form':
                                h['form'] = hop_member.text

                        ingredients['spices'].append(h)

                elif tag == 'fermentables':
                    for fermentable in recipe_member:
                        f = {
                            'description': '',
                            'weight': 0.0,
                            'late': '',
                            'ppg': 0.0,
                            'color': 0
                        }
                        for fermentable_member in fermentable:
                            tag = fermentable_member.tag.lower()
                            if tag == 'name':
                                f['description'] = fermentable_member.text
                            elif tag == 'amount':
                                f['weight'] = float(fermentable_member.text) * 2.20462
                            elif tag == 'yield':
                                f['ppg'] = round(float(fermentable_member.text) * 46.214 * 0.01)
                            elif tag == 'color':
                                f['color'] = float(fermentable_member.text)
                            elif tag == 'add_after_boil':
                                f['late'] = fermentable_member.text.lower() == 'true' and 'y' or ''

                        ingredients['fermentables'].append(f)
                elif tag == 'yeasts':
                    for yeast in recipe_member:
                        y = {
                            'description': '',
                            'type': '',
                            'form': '',
                            'attenuation': 75
                        }
                        for yeast_member in yeast:
                            tag = yeast_member.tag.lower()
                            if tag == 'name':
                                y['description'] = yeast_member.text
                            elif tag =='type':
                                y['type'] = yeast_member.text
                            elif tag == 'form':
                                y['form'] = yeast_member.text
                            elif tag == 'attenuation':
                                y['attenuation'] = float(yeast_member.text)

                        ingredients['yeast'].append(y)

            r.ingredients = ingredients
            new_recipes.append(r)

        return new_recipes

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
        return super(Recipe, self).put(*args)

    def create_historic_version(self):
        """
        Create a historic version of this recipe. The contents of this recipe
        are copied to the RecipeHistory with a link back to this recipe. The
        history is not yet commited to the datastore.
        """
        return RecipeHistory(self, **{
            'created': self.edited,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'category': self.category,
            'style': self.style,
            'batch_size': self.batch_size,
            'boil_size': self.boil_size,
            'bottling_temp': self.bottling_temp,
            'bottling_pressure': self.bottling_pressure,
            'mash_efficiency': self.mash_efficiency,
            'steep_efficiency': self.steep_efficiency,
            'primary_days': self.primary_days,
            'secondary_days': self.secondary_days,
            'tertiary_days': self.tertiary_days,
            'aging_days': self.aging_days,
            '_ingredients': self._ingredients
        })

    def update_grade(self):
        """
        Grade a recipe based on several factors:

          * Recipe completeness (title, description, ingredients)
          * Average brew rating weighted inverse temporally
          * Average completeness of brews (measurements, rating, notes)
          * Total number of clones, brews and unique brewers

        The calculated grade is used to rank recipes - those with the highest
        grade will move toward the front of the list. This should hopefully
        mean that recipes that are very popular, that many people like, that
        have many clones or reviews, and that have many positive reviews
        should be shown before others.

        What actions can someone take to increase the grade of a recipe?
        The owner can make sure it has a proper title, description, and at
        least one of each type of ingredient. A normal user can clone and/or
        brew the recipe, making sure to fill in as much as possible for the
        brew.
        """
        from models.brew import Brew

        grade = 0.0

        clone_count = Recipe.all().filter('cloned_from =', self).count()
        logging.info('clone count ' + str(clone_count))
        brew_count = Brew.all().filter('recipe =', self).count()
        brews = Brew.all().filter('recipe =', self).order('-started').fetch(25)

        # Grade completeness
        if self.name.lower() not in ['', 'untitled', 'untitled brew', 'no name']:
            grade += 1.0

        if self.description.lower() not in ['', 'no description', 'none']:
            grade += 1.0

        if len(self.ingredients['fermentables']) and len(self.ingredients['spices']) and len(self.ingredients['yeast']):
            grade += 1.0

        if clone_count and brew_count:
            grade += 1.0

        # Grade average weighted reviews
        count = 0
        brewers = set()
        avg_review = 0.0
        for i, brew in enumerate(brews):
            brew_grade = 0.0

            brewers.add(brew.owner_key)

            # Completeness of brew
            if brew.started:
                brew_grade += 1.0

            if brew.og and brew.fg:
                brew_grade += 1.0

            if brew.notes:
                brew_grade += 1.0

            # Brew rating
            if brew.rating:
                brew_grade += brew.rating
                avg_review += brew.rating
                count += 1

            # Weighted average (0.5, 0.25, 0.125, ...)
            grade += brew_grade * (0.5 / (i + 1))

        # Total unique brewers
        grade += math.ceil(math.log(len(brewers) + 1, 3))

        # Total clones and brews
        grade += math.ceil(math.log(clone_count + 1, 3))
        grade += math.ceil(math.log(brew_count + 1, 3))

        # Update values on this recipe
        self.grade = grade

        self.review_count = brew_count
        if count:
            self.avg_review = avg_review / count
        else:
            self.avg_review = 0.0


class RecipeHistory(RecipeBase):
    # The parent recipe that this is a historic version of
    #parent_recipe = db.ReferenceProperty(Recipe)

    created = db.DateTimeProperty()
