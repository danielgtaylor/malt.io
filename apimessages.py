from protorpc import messages


class UserGetRequest(messages.Message):
    user_name = messages.StringField(1, required=True)


class UserGetResponse(messages.Message):
    user_id = messages.StringField(1)
    user_name = messages.StringField(2)
    joined_date = messages.StringField(3)
    awards = messages.StringField(4, repeated=True)
    avatar_small = messages.StringField(5)
    avatar = messages.StringField(6)


class UserListRequest(messages.Message):
    pass


class UserListResponse(messages.Message):
    items = messages.MessageField(UserGetResponse, 1, repeated=True)


class RecipeGetRequest(messages.Message):
    user_name = messages.StringField(1, required=True)
    slug = messages.StringField(2, required=True)


class RecipeGetResponse(messages.Message):
    name = messages.StringField(1)
    description = messages.StringField(2)
