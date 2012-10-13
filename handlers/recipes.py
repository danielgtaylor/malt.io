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

        # Start with the current version versus the previous
        entries.append({
            'recipe': recipe,
            'differences': self.order_differences(recipe.diff(history[0])),
            'edited': recipe.edited,
            'slug': recipe.slug
        })

        # Start going through the history looking at differences to decide how
        # we plan on displaying the info to the user (using a snippet or not)
        snippetItems = ('name', 'description', 'color', 'ibu', 'alcohol')
        for i in range(len(history) - 1):
            # Set some required properties for the snippet to work
            history[i].owner = recipe.owner
            history[i].slug = recipe.slug + '/' + str(history[i].key().id())

            # Create the entry
            entry = {}
            differences = history[i].diff(history[i + 1])

            # Check if the name, description, color, ibu, or alcohol changed
            # and we should show a snippet
            for snippetItem in snippetItems:
                for diffset in differences:
                    if snippetItem in diffset:
                        entry['recipe'] = history[i]
                        # Make sure the color, ibu, and alcohol were created
                        if not hasattr(history[i], 'color'):
                            history[i].update_cache()
                        break
                if 'recipe' in entry:
                    break

            entry['differences'] = self.order_differences(differences)
            entry['edited'] = history[i].created
            entry['slug'] = history[i].slug
            entries.append(entry)

        # Add the final entry
        entry = history[len(history) - 1]
        entry.owner = recipe.owner
        entry.slug = recipe.slug + '/' + str(entry.key().id())
        entries.append({
            'recipe': entry,
            'differences': None,
            'edited': entry.created,
            'slug': entry.slug
        })

        render(self, 'recipe-history.html', {
            'publicuser': publicuser,
            'recipe': recipe,
            'entries': entries
        })

    def order_differences(self, differences):
        """
        Convert a set of differences into a list of "most interesting" order.

        Most interesting is defined as:
            1. Additions and deletions
            2. Changes that affect the recipe snippet
                a. Title, Description
                b. Color, IBU, Alcohol (affected by ingredients and sizes)
            3. Other
        """
        difflist = []

        additions = differences[0]
        deletions = differences[1]
        modifications = differences[2]

        for key in additions:
            if key == 'ingredients':
                for type in additions['ingredients']:
                    for ingredient in additions['ingredients'][type]:
                        difflist.append(self.create_add_string(str(type) + ' ingredient', ingredient))
            else:
                difflist.append(self.create_add_string(key, additions[key]))

        for key in deletions:
            if key == 'ingredients':
                for type in deletions['ingredients']:
                    for ingredient in deletions['ingredients'][type]:
                        difflist.append(self.create_delete_string(str(type) + ' ingredient', ingredient))
            else:
                difflist.append(self.create_delete_string(key, deletions[key]))

        # Generate a list of modifications and assign them a score
        scoredlist = []
        # We don't care about these being modified, since they're calculated properties
        ignorelist = ('color', 'ibu', 'alcohol')
        # Properties that will affect the recipe snippet, assigned a higher score
        highimpact = ('batch_size', 'boil_size')
        # Properties that will affect the recipe snippet, but we want to avoid
        # showing redundant info, so these will be penalized
        lowimpact = ('title', 'description')
        for key in modifications:
            if key in ignorelist:
                continue
            elif key == 'ingredients':
                for type in modifications['ingredients']:
                    for ingredient in modifications['ingredients'][type]:
                        # Start with a high score
                        score = 20
                        for vals in modifications['ingredients'][type][ingredient].values():
                            # Add a modifier for the percent change of ever modification
                            try:
                                score += 5 * vals[1] / vals[0]
                            except:
                                pass
                        scoredlist.append((score, self.create_edit_ingredient_string(type, ingredient)))
            else:
                if key in highimpact:
                    # Start with a high score
                    score = 20
                elif key in lowimpact:
                    # Start with a low score
                    score = 0
                else:
                    # Start with a normal score
                    score = 10

                # Add a modifier for the percent change
                try:
                    score += 10 * modifications[key][1] / modifications[key][0]
                except:
                    pass

                scoredlist.append((score, self.create_edit_string(key, modifications[key][1])))

        if len(scoredlist) > 0:
            # Sort based on score
            scoredlist.sort(key=itemgetter(0), reverse=True)

            # Append the sorted items to the difflist
            difflist.extend([diff for score, diff in scoredlist])

        return difflist

    def create_add_string(self, key, value):
        """
        Create a display string for an addition.
        """
        return 'Added ' + self.key_for_display(key) + ': ' + self.value_for_display(value)

    def create_delete_string(self, key, value):
        """
        Create a display string for a deletion.
        """
        return 'Removed ' + self.key_for_display(key) + ': ' + self.value_for_display(value)

    def create_edit_string(self, key, value):
        """
        Create a display string for a modification.
        """
        return 'Changed ' + self.key_for_display(key) + ' to ' + self.value_for_display(value)

    def create_edit_ingredient_string(self, key, value):
        """
        Create a display string for an ingredient modification.
        """
        return 'Changed properties on ' + self.key_for_display(key) + ' ingredient: ' + self.value_for_display(value)

    def key_for_display(self, key):
        """
        Convert an object key, such as batch_size, to a display value.
        """
        return key.replace('_', ' ')

    def value_for_display(self, value):
        """
        Convert a user-entered value to a display value. This wraps strings
        in quotes and converts numbers to strings.
        """
        if isinstance(value, (str, unicode)):
            return '"' + value + '"'
        else:
            return str(value)
