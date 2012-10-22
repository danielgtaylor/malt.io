from protorpc import messages


class UserGetRequest(messages.Message):
    user_name = messages.StringField(1, required=True)


class UserGetResponse(messages.Message):
    user_name = messages.StringField(1)
    joined_date = messages.StringField(2)
    awards = messages.StringField(3, repeated=True)
    avatar_small = messages.StringField(4)
    avatar = messages.StringField(5)


class UserListRequest(messages.Message):
    pass


class UserListResponse(messages.Message):
    items = messages.MessageField(UserGetResponse, 1, repeated=True)


class RecipeGetRequest(messages.Message):
    user_name = messages.StringField(1, required=True)
    slug = messages.StringField(2, required=True)


class FermentableResponse(messages.Message):
    weight_kg = messages.FloatField(1)
    description = messages.StringField(2)
    late = messages.BooleanField(3)
    color = messages.FloatField(4)
    yield_ratio = messages.FloatField(5)


class RecipeGetResponse(messages.Message):
    name = messages.StringField(1)
    slug = messages.StringField(2)
    description = messages.StringField(3)
    batch_liters = messages.FloatField(4)
    boil_liters = messages.FloatField(5)
    fermentables = messages.MessageField(FermentableResponse, 6, repeated=True)


class RecipeListRequest(messages.Message):
    user_name = messages.StringField(1, required=True)


class RecipeListResponse(messages.Message):
    items = messages.MessageField(RecipeGetResponse, 1, repeated=True)
