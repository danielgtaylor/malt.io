from protorpc import messages


class UserOrder(messages.Enum):
    # Sort alphabetically
    NAME = 1
    # Sort by date joined with newest first
    JOINED = 2


class RecipeOrder(messages.Enum):
    # Sort alphabetically
    NAME = 1
    # Sort by date created with newest first
    CREATED = 2
    # Sort by date edited with newest first
    EDITED = 3
    # Sort by likes with most likes first
    LIKES = 4


class UserGetRequest(messages.Message):
    """
    Request information about a user.

    user_name: The user's unique name
    """
    # The user's unique name
    user_name = messages.StringField(1, required=True)


class UserGetResponse(messages.Message):
    """
    A user object

    user_name: The user's unique name
    joined_date: The date the user joined Malt.io
    awards: A list of strings representing awards the user has earned
    avatar_small: A small avatar image URL
    avatar: A large avatar image URL
    url: The URL to this user's page
    """
    user_name = messages.StringField(1)
    joined_date = messages.StringField(2)
    awards = messages.StringField(3, repeated=True)
    avatar_small = messages.StringField(4)
    avatar = messages.StringField(5)
    url = messages.StringField(6)


class UserListRequest(messages.Message):
    """
    Get a list of users.

    offset: The starting offset of the query (0 or higher)
    limit: The maximum number of results to return (1 - 100)
    order: The order of returned items (NAME, JOINED)
    """
    offset = messages.IntegerField(1, default=0)
    limit = messages.IntegerField(2, default=25)
    order = messages.EnumField(UserOrder, 3, default=UserOrder.JOINED)


class UserListResponse(messages.Message):
    """
    A list of users.

    items: List of users
    """
    items = messages.MessageField(UserGetResponse, 1, repeated=True)


class RecipeGetRequest(messages.Message):
    """
    Request information about a recipe.

    user_name: The user's unique name
    slug: The recipe's unique slug
    """
    user_name = messages.StringField(1, required=True)
    slug = messages.StringField(2, required=True)


class FermentableResponse(messages.Message):
    """
    A fermentable ingredient (malt, sugar, etc).

    weight_kg: Weight in kilograms
    description: Item description
    late: Whether to add at the beginning or end of the boil
    color: Color in degrees SRM
    yield_ratio: Extration yield ratio to calculate fermentability
    """
    weight_kg = messages.FloatField(1)
    description = messages.StringField(2)
    late = messages.BooleanField(3)
    color = messages.FloatField(4)
    yield_ratio = messages.FloatField(5)


class SpiceResponse(messages.Message):
    """
    A spice ingredient (hops, herbs, spices, etc).

    use: When to use the item (mash, boil, primary, etc)
    time: When to add the item in seconds
    weight_kg: Weight in kilograms
    description: Item description
    form: The form of the item (pellet, whole, ground, etc)
    aa: The alpha acid ratio for bitterness calculation
    """
    use = messages.StringField(1)
    time = messages.IntegerField(2)
    weight_kg = messages.FloatField(3)
    description = messages.StringField(4)
    form = messages.StringField(5)
    aa_ratio = messages.FloatField(6)


class YeastResponse(messages.Message):
    """
    A yeast ingredient or other bug.

    description: Item description
    type: Yeast type (ale, lager, etc)
    form: Yeast form (liquid, dry)
    attenuation_ratio: Fermentable conversion potential
    """
    description = messages.StringField(1)
    type = messages.StringField(2)
    form = messages.StringField(3)
    attenuation_ratio = messages.FloatField(4)


class RecipeGetResponse(messages.Message):
    """
    A recipe.

    name: The name of the recipe
    slug: The recipe's unique slug
    description: Recipe description
    batch_liters: Batch size in liters (i.e. how much beer will this make?)
    boil_liters: Boil size in liters (i.e. how big of a pot do I need?)
    color: Color in degrees SRM
    ibu: Bitterness units
    abv: Alcohol content by volume
    fermentables: List of fermentables
    spices: List of spices (hops, herbs, spices)
    yeast: List of yeast and bugs
    bottling_temp: Temperature in C at bottling time
    bottling_pressure: Desired volumes of CO2 pressure
    likes: The number of likes this recipe has
    url: The URL to this recipe
    parent_owner: The owner of the parent recipe if this is a cloned recipe
    parent_slug: The slug of the parent recipe if this is a cloned recipe
    parent_url: The URL to the parent recipe if this is a cloned recipe
    """
    owner = messages.StringField(1)
    name = messages.StringField(2)
    slug = messages.StringField(3)
    description = messages.StringField(4)
    batch_liters = messages.FloatField(5)
    boil_liters = messages.FloatField(6)
    color = messages.IntegerField(7)
    ibu = messages.FloatField(8)
    abv = messages.FloatField(9)
    fermentables = messages.MessageField(FermentableResponse, 10, repeated=True)
    spices = messages.MessageField(SpiceResponse, 11, repeated=True)
    yeast = messages.MessageField(YeastResponse, 12, repeated=True)
    bottling_temp = messages.FloatField(13)
    bottling_pressure = messages.FloatField(14)
    likes = messages.IntegerField(15)
    url = messages.StringField(16)
    parent_owner = messages.StringField(17)
    parent_slug = messages.StringField(18)
    parent_url = messages.StringField(19)


class RecipeListRequest(messages.Message):
    """
    Get a list of recipes.

    user_name: The user's unique name
    offset: The starting offset of the query (0 or higher)
    limit: The maximum number of results to return (1 - 100)
    order: The order of returned items (NAME, CREATED, EDITED, LIKES)
    """
    user_name = messages.StringField(1)
    offset = messages.IntegerField(2, default=0)
    limit = messages.IntegerField(3, default=25)
    order = messages.EnumField(RecipeOrder, 4, default=RecipeOrder.NAME)


class RecipeListResponse(messages.Message):
    """
    A list of recipes.

    items: List of recipes
    """
    items = messages.MessageField(RecipeGetResponse, 1, repeated=True)
