# content: utf-8

import cgi
import json
import logging
import webapp2

from models.recipe import Recipe, RecipeHistory
from models.useraction import UserAction
from models.userprefs import UserPrefs
from util import render, render_json, slugify
from webapp2 import redirect
from webapp2_extras.appengine.users import login_required
from operator import itemgetter


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


class RecipesHandler(webapp2.RequestHandler):
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
        if username:
            publicuser = UserPrefs.all().filter('name =', username).get()
            recipes = Recipe.all()\
                            .filter('owner =', publicuser)
        else:
            publicuser = None
            recipes = Recipe.all()

        render(self, 'recipes.html', {
            'publicuser': publicuser,
            'recipes': recipes
        })

    def post(self):
        """
        Import a new recipe or list of recipes from BeerXML to the
        currently logged in user's account.
        """
        user = UserPrefs.get()
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

        return redirect('/users/' + user.name + '/recipes')

class RecipeEmbedHandler(webapp2.RequestHandler):
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
            render(self, 'recipe-embed.html', {
                'publicuser': publicuser,
                'recipe': recipe,
                'width': width,
            })
        else:
            render(self, 'recipe-embed-404.html', {
                'publicuser': publicuser,
                'width': width,
            })


class RecipeXmlHandler(webapp2.RequestHandler):
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

        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write(recipe.beerxml)


class RecipeLikeHandler(webapp2.RequestHandler):
    """
    Recipe like request handler. Handles when a user likes a particular recipe
    by adding this user's id to the list of likes. This handler supports two
    methods: post and delete, which add or remove the user, respectively.
    It is invoked via URLs like:

        /users/USERNAME/recipes/RECIPE-SLUG/like

    """
    def post(self, username=None, recipe_slug=None):
        """
        Add a user to the list of likes for a recipe.
        """
        return self.process('post', username, recipe_slug)

    def delete(self, username=None, recipe_slug=None):
        """
        Remove a user from the list of likes for a recipe.
        """
        return self.process('delete', username, recipe_slug)

    def process(self, action, username=None, recipe_slug=None):
        """
        Process a request to add or remove a user from the liked list.
        """
        user = UserPrefs.get()
        publicuser = UserPrefs.all()\
                              .filter('name = ', username)\
                              .get()

        if not publicuser:
            render_json(self, {
                'status': 'error',
                'error': 'User not found'
            })
            return

        recipe = Recipe.all()\
                       .filter('owner =', publicuser)\
                       .filter('slug =', recipe_slug)\
                       .get()

        if not recipe:
            render_json(self, {
                'status': 'error',
                'error': 'Recipe not found'
            })
            return

        if action == 'post':
            if user.user_id not in recipe.likes:
                recipe.likes.append(user.user_id)
                recipe.put()

                existing = UserAction.all()\
                                     .filter('owner =', user)\
                                     .filter('type =', UserAction.TYPE_RECIPE_LIKED)\
                                     .filter('object_id =', recipe.key().id())\
                                     .count()

                if not existing:
                    user_action = UserAction()
                    user_action.owner = user
                    user_action.type = user_action.TYPE_RECIPE_LIKED
                    user_action.object_id = recipe.key().id()
                    user_action.put()

        elif action == 'delete':
            if user.user_id in recipe.likes:
                recipe.likes.remove(user.user_id)
                recipe.put()

                existing = UserAction.all()\
                                     .filter('owner =', user)\
                                     .filter('type =', UserAction.TYPE_RECIPE_LIKED)\
                                     .filter('object_id =', recipe.key().id())\
                                     .get()

                if existing:
                    existing.delete()

        return render_json(self, {
            'status': 'ok',
            'likes': len(recipe.likes)
        })


class RecipeCloneHandler(webapp2.RequestHandler):
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
            render_json(self, {
                'status': 'error',
                'error': 'User not found'
            })
            return

        recipe = Recipe.all()\
                       .filter('owner =', publicuser)\
                       .filter('slug =', recipe_slug)\
                       .get()

        if not recipe:
            render_json(self, {
                'status': 'error',
                'error': 'Recipe not found'
            })
            return

        new_recipe = Recipe(**{
            'owner': UserPrefs.get(),
            'cloned_from': recipe,
            'color': recipe.color,
            'ibu': recipe.ibu,
            'alcohol': recipe.alcohol,
            'name': recipe.name,
            'description': recipe.description,
            'type': recipe.type,
            'style': recipe.style,
            'batch_size': recipe.batch_size,
            'boil_size': recipe.boil_size,
            'bottling_temp': recipe.bottling_temp,
            'bottling_pressure': recipe.bottling_pressure,
            '_ingredients': recipe._ingredients
        })

        new_recipe.slug = generate_usable_slug(new_recipe)
        new_recipe.put()

        action = UserAction()
        action.owner = UserPrefs.get()
        action.type = action.TYPE_RECIPE_CLONED
        action.object_id = new_recipe.key().id()
        action.put()

        return render_json(self, {
            'status': 'ok',
            'redirect': new_recipe.url
        })


class RecipeHandler(webapp2.RequestHandler):
    """
    Recipe view handler. This handler renders a recipe and handles updating
    recipe data when a user saves a recipe in edit mode. It is invoked via
    URLs like:

        /new
        /users/USERNAME/recipes/RECIPE-SLUG

    """
    def get(self, username=None, recipe_slug=None):
        """
        Render the recipe view. If no slug is given then create a new recipe
        and render it in edit mode.
        """
        # Create a new recipe if we have no slug, otherwise query
        if not recipe_slug:
            publicuser = UserPrefs.get()
            recipe = Recipe()
            recipe.owner = publicuser
            recipe.new = True
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

        cloned_from = None
        try:
            cloned_from = recipe.cloned_from
        except Exception, e:
            pass

        render(self, 'recipe.html', {
            'publicuser': publicuser,
            'recipe': recipe,
            'cloned_from': cloned_from
        })

    def post(self, username=None, recipe_slug=None):
        """
        Handle recipe updates. This gets in a JSON object describing a
        recipe and saves the values to the data store. An error is returned
        if the current user does not have the proper rights to modify the
        recipe.
        """
        user = UserPrefs.get()
        recipe_json = cgi.escape(self.request.get('recipe'))

        # Parse the JSON into Python objects
        try:
            recipe_data = json.loads(recipe_json)
        except Exception, e:
            render_json(self, {
                'status': 'error',
                'error': str(e),
                'input': recipe_json
            })
            return

        # Load recipe from db or create a new one
        if not recipe_slug:
            recipe = Recipe()
            recipe.owner = user
        else:
            recipe = Recipe.all()\
                           .filter('owner =', user)\
                           .filter('slug =', recipe_slug)\
                           .get()

            if recipe:
                # Save a historic version of this recipe
                recipe.put_historic_version()
            else:
                render_json(self, {
                    'status': 'error',
                    'error': 'Recipe not found'
                })
                return

        # Ensure you own this recipe
        if not recipe or recipe.owner.name != user.name:
            render_json(self, {
                'status': 'error',
                'error': 'Permission denied: you are not the recipe owner!'
            })
            return

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
        recipe.ingredients = recipe_data['ingredients']

        # Update slug
        recipe.slug = generate_usable_slug(recipe)

        # Save recipe to database
        key = recipe.put()

        action = UserAction()
        action.owner = user
        action.object_id = key.id()

        if not recipe_slug:
            action.type = action.TYPE_RECIPE_CREATED
        else:
            action.type = action.TYPE_RECIPE_EDITED

        action.put()

        render_json(self, {
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
        user = UserPrefs.get()

        if not user:
            render_json(self, {
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

            render_json(self, {
                'status': 'ok',
                'redirect': '/users/%(username)s/recipes' % {
                    'username': user.name
                }
            })
        else:
            render_json(self, {
                'status': 'error',
                'error': 'Unable to delete recipe'
            })


class RecipeHistoryHandler(webapp2.RequestHandler):
    """
    Recipe history handler. This handler renders the recipe history tree for
    a specific recipe. It is invoked via URLs like:

        /users/USERNAME/recipes/RECIPE-SLUG/history
    """
    IGNORED_KEYS = ('color', 'ibu', 'alcohol')
    SNIPPET_ITEMS = IGNORED_KEYS + ('name', 'description')

    def get(self, username=None, recipe_slug=None):
        """
        Render the basic recipe history list for the given recipe.
        """
        if not username or not recipe_slug:
            self.abort(404)

        publicuser = UserPrefs.all().filter('name =', username).get()
        recipe = Recipe.all()\
                       .filter('slug = ', recipe_slug)\
                       .filter('owner =', publicuser)\
                       .get()

        history = RecipeHistory.all()\
                        .filter('parent_recipe =', recipe)\
                        .order('-created')\
                        .fetch(30)

        # The list of entries we'll use to populate the template
        entries = []

        # Check if there is any history to diff with
        if len(history) > 0:
            differences = self.delete_ignored_keys(recipe.diff(history[0]))
        else:
            differences = None

        # Start with the current version versus the previous
        entries.append({
            'recipe': recipe,
            'differences': differences,
            'edited': recipe.edited,
            'slug': recipe.slug,
            'customtag': 'Current'
        })

        # Start going through the history looking at differences to decide how
        # we plan on displaying the info to the user (using a snippet or not)
        for i in range(len(history) - 1):
            # Set some required properties for the snippet to work
            history[i].owner = recipe.owner
            history[i].slug = recipe.slug + '/' + str(history[i].key().id())

            # Create the entry
            entry = {}
            differences = history[i].diff(history[i + 1])

            # Check if the name, description, color, ibu, or alcohol changed
            # and we should show a snippet
            for snippetItem in RecipeHistoryHandler.SNIPPET_ITEMS:
                for diffset in differences:
                    if snippetItem in diffset:
                        entry['recipe'] = history[i]
                        # Make sure the color, ibu, and alcohol were created
                        if not hasattr(history[i], 'color'):
                            history[i].update_cache()
                        break
                if 'recipe' in entry:
                    break

            entry['differences'] = self.delete_ignored_keys(differences)
            entry['edited'] = history[i].created
            entry['slug'] = history[i].slug
            entries.append(entry)

        # Add the final entry
        if len(history) > 0:
            entry = history[len(history) - 1]
            entry.owner = recipe.owner
            entry.slug = recipe.slug + '/' + str(entry.key().id())
            entries.append({
                'recipe': entry,
                'differences': None,
                'edited': entry.created,
                'slug': entry.slug,
                'customtag': 'Original',
                'first': True
            })

        render(self, 'recipe-history.html', {
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