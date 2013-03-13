# content: utf-8

import cgi
import json
import logging
import webapp2

from contrib.paodate import Date
from handlers.base import BaseHandler
from models.recipe import Recipe, RecipeHistory
from models.useraction import UserAction
from models.userprefs import UserPrefs
from util import render, render_json, slugify
from webapp2 import redirect
from webapp2_extras.appengine.users import login_required
from google.appengine.ext import db
from operator import itemgetter
from datetime import timedelta


def generate_usable_slug(recipe):
    """
    Generate a usable slug for a given recipe. This method will try to slugify
    the recipe name and then append an integer if needed, increasing this
    integer until no existing recipe would be overwritten.
    """
    slug = slugify(recipe.name)

    # Reuse existing slug if we can
    if recipe.slug and recipe.slug == slug:
        return recipe.slug

    append = 0
    while True:
        count = Recipe.all()\
                      .filter('owner =', recipe.owner)\
                      .filter('slug =', slug)\
                      .count()

        if not count:
            break

        append += 1
        slug = slugify(recipe.name) + str(append)

    return slug


class RecipesHandler(BaseHandler):
    """
    Recipe list view handler. This handler renders the public recipe list for
    a specific user and for all users. It is invoked via URLs like:

        /recipes
        /users/USERNAME/recipes

    """
    def get(self, username=None):
        """
        Render the public recipe list for a user or all users.
        """
        show_owners = False
        if username:
            publicuser = UserPrefs.all().filter('name =', username).get()
            recipes = Recipe.all()\
                            .filter('owner =', publicuser)\
                            .order('-grade')
            def setowner(recipe):
                recipe.owner = publicuser
                return recipe
            recipes = map(setowner, recipes)
        else:
            publicuser = None
            recipes = Recipe.all().order('-grade')
            recipes = [r for r in recipes]
            show_owners = True

        self.render('recipes.html', {
            'publicuser': publicuser,
            'recipes': recipes,
            'show_owners': show_owners
        })

    def post(self):
        """
        Import a new recipe or list of recipes from BeerXML to the
        currently logged in user's account.
        """
        user = self.user
        recipesxml = self.request.POST['file'].value

        for recipe in Recipe.new_from_beerxml(recipesxml):
            recipe.owner = user
            recipe.slug = generate_usable_slug(recipe)
            recipe.update_cache();
            key = recipe.put()

            action = UserAction()
            action.owner = user
            action.object_id = key.id()
            action.type = action.TYPE_RECIPE_CREATED
            action.put()

        self.redirect('/users/' + user.name + '/recipes')

class RecipeEmbedHandler(BaseHandler):
    """
    Handle recipe embeds on other sites. This returns a javascript
    which is used to render a small widget on another site with information
    about the recipe and owner.

        /embed/USERNAME/RECIPE-SLUG

    """
    def get(self, username, recipe_slug):
        publicuser = UserPrefs.all().filter('name = ', username).get()

        if publicuser:
            recipe = Recipe.all()\
                           .filter('owner =', publicuser)\
                           .filter('slug =', recipe_slug)\
                           .get()
        else:
            recipe = None

        width = 260
        try:
            width = int(self.request.get('width'))
        except: pass

        if publicuser and recipe:
            self.render('recipe-embed.html', {
                'publicuser': publicuser,
                'recipe': recipe,
                'width': width,
            })
        else:
            self.render('recipe-embed-404.html', {
                'publicuser': publicuser,
                'width': width,
            })


class RecipeXmlHandler(BaseHandler):
    """
    Handle recipe export via BeerXML. This renders a BeerXML representation
    of the recipe that can be imported into other beer software.

        /embed/USERNAME/RECIPE-SLUG/beerxml

    """
    def get(self, username, recipe_slug):
        publicuser = UserPrefs.all().filter('name = ', username).get()
        if not publicuser:
            self.abort(404)

        recipe = Recipe.all()\
                       .filter('owner =', publicuser)\
                       .filter('slug =', recipe_slug)\
                       .get()

        if not recipe:
            self.abort(404)

        self.render_xml(recipe.beerxml)


class RecipeCloneHandler(BaseHandler):
    """
    Recipe clone handler. This handler is responsible for cloning a recipe
    to a user's account, by creating a new recipe and copying over all
    attributes. It is invoked via URLs like:

        /users/USERNAME/recipes/RECIPE-SLUG/clone

    """
    def post(self, username=None, recipe_slug=None):
        publicuser = UserPrefs.all()\
                              .filter('name = ', username)\
                              .get()

        if not publicuser:
            self.render_json({
                'status': 'error',
                'error': 'User not found'
            })
            return

        recipe = Recipe.all()\
                       .filter('owner =', publicuser)\
                       .filter('slug =', recipe_slug)\
                       .get()

        if not recipe:
            self.render_json({
                'status': 'error',
                'error': 'Recipe not found'
            })
            return

        new_recipe = Recipe(**{
            'owner': self.user,
            'cloned_from': recipe,
            'color': recipe.color,
            'ibu': recipe.ibu,
            'alcohol': recipe.alcohol,
            'name': recipe.name,
            'description': recipe.description,
            'type': recipe.type,
            'category': recipe.category,
            'style': recipe.style,
            'batch_size': recipe.batch_size,
            'boil_size': recipe.boil_size,
            'bottling_temp': recipe.bottling_temp,
            'bottling_pressure': recipe.bottling_pressure,
            'steep_efficiency': recipe.steep_efficiency,
            'mash_efficiency': recipe.mash_efficiency,
            'primary_days': recipe.primary_days,
            'primary_temp': recipe.primary_temp,
            'secondary_days': recipe.secondary_days,
            'secondary_temp': recipe.secondary_temp,
            'tertiary_days': recipe.tertiary_days,
            'tertiary_temp': recipe.tertiary_temp,
            'aging_days': recipe.aging_days,
            '_ingredients': recipe._ingredients
        })

        new_recipe.slug = generate_usable_slug(new_recipe)
        new_recipe.put()
        new_recipe.update_grade()
        new_recipe.put()

        # Update recipe ranking for sorting
        recipe.update_grade()
        recipe.put()

        action = UserAction()
        action.owner = self.user
        action.type = action.TYPE_RECIPE_CLONED
        action.object_id = new_recipe.key().id()
        action.put()

        return self.render_json({
            'status': 'ok',
            'redirect': new_recipe.url
        })


class RecipeHandler(BaseHandler):
    """
    Recipe view handler. This handler renders a recipe and handles updating
    recipe data when a user saves a recipe in edit mode. It is invoked via
    URLs like:

        /new
        /users/USERNAME/recipes/RECIPE-SLUG
        /users/USERNAME/recipes/RECIPE-SLUG/VERSION

    """
    def get(self, username=None, recipe_slug=None, version=None):
        """
        Render the recipe view. If no slug is given then create a new recipe
        and render it in edit mode.
        """
        # Create a new recipe if we have no slug, otherwise query
        if not recipe_slug:
            publicuser = self.user
            recipe = Recipe()
            recipe.owner = publicuser
            recipe.new = True
            brews = []
        else:
            publicuser = UserPrefs.all().filter('name =', username).get()

            if not publicuser:
                self.abort(404)

            recipe = Recipe.all()\
                           .filter('owner =', publicuser)\
                           .filter('slug =', recipe_slug)\
                           .get()

            if not recipe:
                self.abort(404)

            brews = recipe.brews.order('-started').fetch(3)

            if version:
                try:
                    version = int(version)
                except:
                    self.abort(404)

                history = RecipeHistory.get_by_id(version, recipe)

                if not history:
                    self.abort(404)

                recipe.old = True
                recipe.oldname = history.name
                recipe.description = history.description
                recipe.type = history.type
                recipe.category = history.category
                recipe.style = history.style
                recipe.batch_size = history.batch_size
                recipe.boil_size = history.boil_size
                recipe.bottling_temp = history.bottling_temp
                recipe.bottling_pressure = history.bottling_pressure
                recipe.mash_efficiency = history.mash_efficiency
                recipe.steep_efficiency = history.steep_efficiency
                recipe.primary_days = history.primary_days
                recipe.secondary_days = history.secondary_days
                recipe.tertiary_days = history.tertiary_days
                recipe.aging_days = history.aging_days
                recipe._ingredients = history._ingredients

        cloned_from = None
        try:
            cloned_from = recipe.cloned_from
        except Exception, e:
            pass

        self.render('recipe.html', {
            'publicuser': publicuser,
            'recipe': recipe,
            'cloned_from': cloned_from,
            'brews': brews,
            'now': Date().datetime
        })

    def post(self, username=None, recipe_slug=None):
        """
        Handle recipe updates. This gets in a JSON object describing a
        recipe and saves the values to the data store. An error is returned
        if the current user does not have the proper rights to modify the
        recipe.
        """
        user = self.user
        recipe_json = cgi.escape(self.request.get('recipe'))

        # Parse the JSON into Python objects
        try:
            recipe_data = json.loads(recipe_json)
        except Exception, e:
            self.render_json({
                'status': 'error',
                'error': str(e),
                'input': recipe_json
            })
            return

        # Load recipe from db or create a new one
        new_recipe = False
        if not recipe_slug:
            recipe = Recipe()
            recipe.owner = user
            new_recipe = True
        else:
            recipe = Recipe.all()\
                           .filter('owner =', user)\
                           .filter('slug =', recipe_slug)\
                           .get()

            if not recipe:
                self.render_json({
                    'status': 'error',
                    'error': 'Recipe not found'
                })
                return

        # Ensure you own this recipe
        if not recipe or recipe.owner.name != user.name:
            self.render_json({
                'status': 'error',
                'error': 'Permission denied: you are not the recipe owner!'
            })
            return

        # Create a historic version to save
        historic = None
        if not new_recipe:
            historic = recipe.create_historic_version()

        # Update recipe
        recipe.name = recipe_data['name']
        recipe.description = recipe_data['description']
        recipe.category = recipe_data['category']
        recipe.style = recipe_data['style']
        recipe.batch_size = float(recipe_data['batchSize'])
        recipe.boil_size = float(recipe_data['boilSize'])
        recipe.color = int(recipe_data['color'])
        recipe.ibu = float(recipe_data['ibu'])
        recipe.alcohol = float(recipe_data['alcohol'])
        recipe.bottling_temp = float(recipe_data['bottlingTemp'])
        recipe.bottling_pressure = float(recipe_data['bottlingPressure'])
        recipe.mash_efficiency = int(recipe_data['mashEfficiency'])
        recipe.steep_efficiency = int(recipe_data['steepEfficiency'])
        recipe.primary_days = int(recipe_data['primaryDays'])
        recipe.primary_temp = float(recipe_data['primaryTemp'])
        recipe.secondary_days = int(recipe_data['secondaryDays'])
        recipe.secondary_temp = float(recipe_data['secondaryTemp'])
        recipe.tertiary_days = int(recipe_data['tertiaryDays'])
        recipe.tertiary_temp = float(recipe_data['tertiaryTemp'])
        recipe.aging_days = int(recipe_data['agingDays'])
        recipe.mash = recipe_data['mash']
        recipe.ingredients = recipe_data['ingredients']

        # Update slug
        recipe.slug = generate_usable_slug(recipe)

        changed = False
        if historic:
            # Perform a diff on the new and historic recipes to see if any actual
            # changes were made
            diff = recipe.diff(historic, False)

            # See if any changes were actually made
            if len(diff[0]) != 0 or \
               len(diff[1]) != 0 or \
               len(diff[2]) != 0:
                
                # Save recipe to database
                key = recipe.put()

                # Save the historic version to database
                historic.put()

                changed = True
        else:
            # Save recipe to database
            key = recipe.put()

        # Update grade now that we have a key
        recipe.update_grade()
        recipe.put()

        if not historic or changed:
            action = UserAction()
            action.owner = user
            action.object_id = key.id()

            if not recipe_slug:
                action.type = action.TYPE_RECIPE_CREATED
            else:
                action.type = action.TYPE_RECIPE_EDITED

            action.put()

        self.render_json({
            'status': 'ok',
            'redirect': '/users/%(username)s/recipes/%(slug)s' % {
                'username': user.name,
                'slug': recipe.slug
            }
        })

    def delete(self, username=None, recipe_slug=None):
        """
        Handle recipe delete. This will remove a recipe and return success
        or failure.
        """
        user = self.user

        if not user:
            self.render_json({
                'status': 'error',
                'error': 'User not logged in'
            })

        recipe = Recipe.all()\
                       .filter('slug = ', recipe_slug)\
                       .filter('owner =', user)\
                       .get()

        if recipe:
            # Delete all actions pointing to this recipe
            actions = UserAction.all()\
                                .filter('type IN', [UserAction.TYPE_RECIPE_CREATED,
                                                    UserAction.TYPE_RECIPE_EDITED,
                                                    UserAction.TYPE_RECIPE_CLONED,
                                                    UserAction.TYPE_RECIPE_LIKED])\
                                .filter('object_id =', recipe.key().id())\
                                .fetch(1000)

            for action in actions:
                action.delete()

            # Delete the actual recipe itself
            recipe.delete()

            self.render_json({
                'status': 'ok',
                'redirect': '/users/%(username)s/recipes' % {
                    'username': user.name
                }
            })
        else:
            self.render_json({
                'status': 'error',
                'error': 'Unable to delete recipe'
            })


class RecipeHistoryHandler(BaseHandler):
    """
    Recipe history handler. This handler renders the recipe history tree for
    a specific recipe. It is invoked via URLs like:

        /users/USERNAME/recipes/RECIPE-SLUG/history
    """
    IGNORED_KEYS = ('color', 'ibu', 'alcohol')
    SNIPPET_ITEMS = ('name', 'description')

    def get(self, username=None, recipe_slug=None):
        """
        Render the basic recipe history list for the given recipe.
        """
        if not username or not recipe_slug:
            self.abort(404)

        publicuser = UserPrefs.all().filter('name =', username).get()
        if not publicuser:
            self.abort(404)

        recipe = Recipe.all()\
                       .filter('slug = ', recipe_slug)\
                       .filter('owner =', publicuser)\
                       .get()
        if not recipe:
            self.abort(404)

        history = RecipeHistory.all()\
                        .ancestor(recipe)\
                        .order('-created')\
                        .fetch(20)

        # The list of entries we'll use to populate the template along with
        # the current recipe as the first entry
        entries = [{
            'recipe': recipe,
            'edited': recipe.edited,
            'slug': recipe.slug,
            'customtag': 'Most Recent',
            'show_snippet': True
        }]

        # Check if there is any history to diff with
        if len(history) > 0:
            entries[0]['differences'] = self.delete_ignored_keys(recipe.diff(history[0]))
        else:
            entries[0]['first'] = True

        # Get a list of differences in the history. Use reduce with a function
        # that returns the right operand to simply find pairwise differences.
        differences = []
        def diff(left, right):
            differences.append(left.diff(right))
            return right
        # Make sure reduce isn't called with no history (throws exception)
        reduce(diff, history) if len(history) > 0 else None

        # Start going through the history looking at differences to decide how
        # we plan on displaying the info to the user (using a snippet or not)
        for i in range(len(differences)):
            # Make sure this entry has differences before further processing
            if self.is_empty(differences[i]):
                continue

            # Set some required properties for the snippet to work
            history[i].owner = publicuser
            history[i].slug = recipe.slug + '/history/' + str(history[i].key().id())

            # Create the entry
            entry = {
                'recipe': history[i],
                'differences': self.delete_ignored_keys(differences[i]),
                'edited': history[i].created,
                'slug': history[i].slug,
                'show_snippet': False
            }

            # Check if the name or description changed and we should show
            # a snippet
            for snippetItem in RecipeHistoryHandler.SNIPPET_ITEMS:
                if snippetItem in differences[i][2]:
                    entry['show_snippet'] = True
                    # Make sure the color, ibu, and alcohol were created
                    if not hasattr(history[i], 'color'):
                        history[i].update_cache()
                    break

            # Save the entry
            entries.append(entry)

        # Add the final entry only if it's the original recipe, otherwise it
        # will be a version that should have diffs but we didn't generate any.
        if len(history) > 0:
            last = history[-1]
            delta = timedelta(seconds=1)
            if recipe.created - delta < last.created < recipe.created + delta:
                last.owner = publicuser
                last.slug = recipe.slug + '/history/' + str(last.key().id())
                if not hasattr(last, 'color'):
                    last.update_cache()
                entries.append({
                    'recipe': last,
                    'edited': last.created,
                    'slug': last.slug,
                    'customtag': 'Original',
                    'first': True
                })

        # Perform a second pass in reverse to check for large changes that
        # should show up as a snippet but were missed in the pairwise
        # checking above.
        entries[-1]['show_snippet'] = True
        for i in range(len(entries) - 1, 0, -1):
            # Check if the snippet is already showing
            if entries[i]['show_snippet']:
                last_snippet = entries[i]['recipe']
                continue

            # Check if the name, description, color, ibu, or alcohol changed
            # and we should show a snippet
            for snippetItem in RecipeHistoryHandler.IGNORED_KEYS:
                if not hasattr(entries[i]['recipe'], snippetItem):
                    continue 
                
                attr = getattr(entries[i]['recipe'], snippetItem)
                if type(attr) != int and type(attr) != float:
                    continue

                # See if the change was more than 10%, then show the
                # snippet, else show the orb
                try:
                    change = float(attr) / getattr(last_snippet, snippetItem)
                except:
                    change = 2
                logging.info(snippetItem)
                logging.info(change)
                if change < 0.9 or change > 1.1:
                    last_snippet = entries[i]['recipe']
                    entries[i]['show_snippet'] = True
                    break

        # Stop the template from performing another query for the username
        # when it tries to render the recipe
        recipe.owner = publicuser

        self.render('recipe-history.html', {
            'publicuser': publicuser,
            'recipe': recipe,
            'entries': entries
        })


    def delete_ignored_keys(self, differences):
        """
        Delete keys from the difference list we don't want passed to the
        templating system.
        """
        for key in RecipeHistoryHandler.IGNORED_KEYS:
            if key in differences[2]:
                del differences[2][key]

        return differences

    def is_empty(self, differences):
        """
        Check if the are no differences.
        """
        for diff in differences:
            if len(diff) > 0:
                return False
        return True
