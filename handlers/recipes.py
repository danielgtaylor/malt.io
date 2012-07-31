import cgi
import json
import webapp2

from models.recipe import Recipe
from models.userprefs import UserPrefs
from util import render, render_json, slugify
from webapp2_extras.appengine.users import login_required


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
        publicuser = UserPrefs.all().filter('name =', username).get()

        if username:
            recipes = Recipe.all().filter('owner =', publicuser)
        else:
            recipes = Recipe.all()

        render(self, 'recipes.html', {
            'publicuser': publicuser,
            'recipes': recipes
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
        publicuser = UserPrefs.all().filter('name =', username).get()

        # Create a new recipe if we have no slug, otherwise query
        if not recipe_slug:
            recipe = Recipe()
        else:
            recipe = Recipe.all()\
                           .filter('owner =', publicuser)\
                           .filter('slug =', recipe_slug)\
                           .get()

        # TODO: return 404 if no recipe is found?

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

        # Load recipe from db
        if not recipe_slug:
            recipe = Recipe()
            recipe.owner = user
        else:
            recipe = Recipe.all()\
                           .filter('owner =', user)\
                           .filter('slug =', recipe_slug)\
                           .get()

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
        recipe.batch_size = float(recipe_data['batchSize'])
        recipe.boil_size = float(recipe_data['boilSize'])
        recipe.color = int(recipe_data['color'])
        recipe.ibu = float(recipe_data['ibu'])
        recipe.alcohol = float(recipe_data['alcohol'])
        recipe.bottling_temp = float(recipe_data['bottlingTemp'])
        recipe.bottling_pressure = float(recipe_data['bottlingPressure'])
        recipe.ingredients = recipe_data['ingredients']

        # Update slug
        # TODO: Make sure the slug is not already taken, and update with
        # increasing integers?
        recipe.slug = slugify(recipe.name)

        # Save recipe to database
        recipe.put()

        render_json(self, {
            'status': 'ok',
            'redirect': '/users/%(username)s/recipes/%(slug)s' % {
                'username': user.name,
                'slug': recipe.slug
            }
        })
