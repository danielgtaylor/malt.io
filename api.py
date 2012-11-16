import logging

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


def get_limits(request):
    """
    Check and get the starting offset and limit for a request that returns
    many items in a list.
    """
    offset = request.offset

    if offset < 0:
        msg = 'Invalid start offset number %d, should be greater or equal to zero' % offset
        raise endpoints.BadRequestException(msg)

    limit = request.limit

    if limit < 1 or limit > 100:
        msg = 'Invalid limit %d, should be between 1 and 100 inclusive' % limit
        raise endpoints.BadRequestException(msg)

    return [offset, limit]


def user_to_response(user):
    """
    Get a user object as a ProtoRPC message response.
    """
    return apimessages.UserGetResponse(**{
        'user_name': user.name,
        'joined_date': str(user.joined),
        'awards': user.awards,
        'avatar_small': user.avatar_tiny,
        'avatar': user.avatar_small,
        'url': 'http://www.malt.io/users/%s' % user.name
    })


def recipe_to_response(recipe):
    """
    Get a recipe object as a ProtoRPC message response.
    """
    fermentables = []
    spices = []
    yeasts = []

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

    for spice in recipe.ingredients['spices']:
        spices.append(apimessages.SpiceResponse(**{
            'use': spice['use'],
            'time': int(util.time_to_min(spice['time']) * 60),
            'weight_kg': float(spice['oz'] * util.OZ_TO_KG),
            'description': spice['description'],
            'form': spice['form'],
            'aa_ratio':  spice['aa'] / 100.0
        }))

    for yeast in recipe.ingredients['yeast']:
        yeasts.append(apimessages.YeastResponse(**{
            'description': yeast['description'],
            'form': yeast['form'],
            'type': yeast['type'],
            'attenuation_ratio': yeast['attenuation'] / 100.0
        }))

    owner = recipe.owner

    try:
        parent = recipe.cloned_from
    except:
        parent = None

    parent_owner = parent and parent.owner or None

    return apimessages.RecipeGetResponse(**{
        'owner': owner.name,
        'name': recipe.name,
        'slug': recipe.slug,
        'description': recipe.description,
        'batch_liters': recipe.batch_size * util.GAL_TO_LITERS,
        'boil_liters': recipe.boil_size * util.GAL_TO_LITERS,
        'color': recipe.color,
        'ibu': recipe.ibu,
        'abv': recipe.alcohol,
        'fermentables': fermentables,
        'spices': spices,
        'yeast': yeasts,
        'bottling_temp': (recipe.bottling_temp - 32) * 5.0 / 9.0,
        'bottling_pressure': recipe.bottling_pressure,
        'likes': recipe.likes_count,
        'url': 'http://www.malt.io/users/%s/recipes/%s' % (owner.name, recipe.slug),
        'parent_owner': parent_owner and parent_owner.name or '',
        'parent_slug': parent and parent.slug or '',
        'parent_url': parent and 'http://www.malt.io/users/%s/recipes/%s' % (parent_owner.name, parent.slug) or ''
    })


@endpoints.api(name='maltio', version='v1',
               description='Malt.io Public API - users, recipes, brews, etc')
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
        Get a list of users.
        """
        offset, limit = get_limits(request)

        query = UserPrefs.all()

        if request.order == apimessages.UserOrder.NAME:
            query = query.order('name')
        elif request.order == apimessages.UserOrder.JOINED:
            query = query.order('-joined')

        users = query.fetch(limit, offset=offset)

        items = []
        for user in users:
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
                      path='recipes',
                      http_method='GET',
                      name='recipes.list')
    def get_recipes(self, request):
        """
        Get a list of recipes, optionally filtered by user name.
        """
        offset, limit = get_limits(request)

        if request.user_name:
            publicuser = UserPrefs.all().filter('name =', request.user_name).get()

            if not publicuser:
                raise endpoints.NotFoundException(USER_NOT_FOUND)

            query = Recipe.all()\
                            .filter('owner =', publicuser)
        else:
            query = Recipe.all()

        if request.order == apimessages.RecipeOrder.NAME:
            query = query.order('name')
        elif request.order == apimessages.RecipeOrder.CREATED:
            query = query.order('-created')
        elif request.order == apimessages.RecipeOrder.EDITED:
            query = query.order('-edited')
        elif request.order == apimessages.RecipeOrder.LIKES:
            query = query.order('-likes_count')

        recipes = query.fetch(limit, offset=offset)

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
                      name='recipes.get')
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
