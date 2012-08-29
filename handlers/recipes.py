import cgi
import json
import webapp2

from models.recipe import Recipe
from models.useraction import UserAction
from models.userprefs import UserPrefs
from util import render, render_json, slugify
from webapp2_extras.appengine.users import login_required


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

        render(self, 'recipe.html', {
            'publicuser': publicuser,
            'recipe': recipe
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
