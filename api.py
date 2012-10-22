from contrib import endpoints
from google.appengine.api import oauth
from protorpc import remote

import apimessages
import util

from models.recipe import Recipe
from models.userprefs import UserPrefs


# Oauth scope for checking authenticated requests
EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'

USER_NOT_FOUND = 'Invalid user name.'
RECIPE_NOT_FOUND = 'Invalid recipe slug.'


def oauth_required(func):
    """
    Decorator to require OAuth to be used for an API method. Use like:

        @endpoint.method(...)
        @oauth_required
        def mymethod(self, request, auth):
            ...
    """
    def decorated(*args, **kwargs):
        try:
            args += (oauth.get_current_user(EMAIL_SCOPE),)
        except oauth.Error:
            msg = 'Not authorized / invalid token'
            raise endpoints.UnauthorizedException(msg)

        return func(*args, **kwargs)

    return decorated


def user_to_response(user):
    """
    Get a user object as a ProtoRPC message response.
    """
    return apimessages.UserGetResponse(**{
        'user_name': user.name,
        'joined_date': str(user.joined),
        'awards': user.awards,
        'avatar_small': user.gravatar_tiny,
        'avatar': user.gravatar_small
    })


def recipe_to_response(recipe):
    """
    Get a recipe object as a ProtoRPC message response.
    """
    fermentables = []

    for fermentable in recipe.ingredients['fermentables']:
        if 'late' not in fermentable:
            fermentable['late'] = False

        fermentables.append(apimessages.FermentableResponse(**{
            'weight_kg': fermentable['weight'] * util.LB_TO_KG,
            'description': fermentable['description'],
            'late': fermentable['late'] and True or False,
            'color': float(fermentable['color']),
            'yield_ratio': fermentable['ppg'] / 46.214
        }))

    return apimessages.RecipeGetResponse(**{
        'name': recipe.name,
        'slug': recipe.slug,
        'description': recipe.description,
        'batch_liters': recipe.batch_size * util.GAL_TO_LITERS,
        'boil_liters': recipe.boil_size * util.GAL_TO_LITERS,
        'fermentables': fermentables
    })


@endpoints.api(name='maltio', version='v1', description='Malt.io API')
class MaltioApi(remote.Service):
    """
    Malt.io Public API
    ------------------
    This provides a ProtoRPC interface for the Endpoints API that allows
    Google's infrastructure to be used for serving API calls for our app.
    Methods are provided such that fully-featured external apps and mash-
    ups can be created, e.g. mobile apps and interesting third party
    sites.
    """
    @endpoints.method(apimessages.UserListRequest,
                      apimessages.UserListResponse,
                      path="users", http_method="GET",
                      name="users.list")
    def get_users(self, request):
        """
        Get a list of all users.
        """
        users = UserPrefs.all()

        items = []
        for user in UserPrefs.all():
            items.append(user_to_response(user))

        return apimessages.UserListResponse(**{
            'items': items
        })

    @endpoints.method(apimessages.UserGetRequest,
                      apimessages.UserGetResponse,
                      path='users/{user_name}', http_method='GET',
                      name='users.get')
    def get_user(self, request):
        """
        Get a user by name.
        """
        publicuser = UserPrefs.all().filter('name =', request.user_name).get()

        if not publicuser:
            raise endpoints.NotFoundException(USER_NOT_FOUND)

        return user_to_response(publicuser)

    @endpoints.method(apimessages.RecipeListRequest,
                      apimessages.RecipeListResponse,
                      path='recipes/{user_name}',
                      http_method='GET',
                      name='users.recipes.list')
    def get_recipes(self, request):
        """
        Get a list of recipes for a user name. Specify 'all' as the user name to get a list of recipes from all users.
        """
        if request.user_name != 'all':
            publicuser = UserPrefs.all().filter('name =', request.user_name).get()

            if not publicuser:
                raise endpoints.NotFoundException(USER_NOT_FOUND)

            recipes = Recipe.all()\
                            .filter('owner =', publicuser)
        else:
            recipes = Recipe.all()

        items = []
        for recipe in recipes:
            items.append(recipe_to_response(recipe))

        return apimessages.RecipeListResponse(**{
            'items': items
        })


    @endpoints.method(apimessages.RecipeGetRequest,
                      apimessages.RecipeGetResponse,
                      path='recipes/{user_name}/{slug}',
                      http_method='GET',
                      name='users.recipes.get')
    def get_recipe(self, request):
        """
        Get a recipe by user name and recipe slug.
        """
        publicuser = UserPrefs.all().filter('name =', request.user_name).get()

        if not publicuser:
            raise endpoints.NotFoundException(USER_NOT_FOUND)

        recipe = Recipe.all()\
                       .filter('owner =', publicuser)\
                       .filter('slug =', request.slug)\
                       .get()

        if not recipe:
            raise endpoints.NotFoundException(RECIPE_NOT_FOUND)

        return recipe_to_response(recipe)
