from handlers.donate import DonateHandler
from handlers.index import MainHandler
from handlers.profile import ProfileHandler
from handlers.recipes import RecipesHandler, RecipeLikeHandler, \
                             RecipeCloneHandler, RecipeHandler
from handlers.users import UsersHandler, UserHandler, UsernameCheckHandler

# The following maps regular expressions to specific handlers.
# Matched groups become positional arguments to the handler's methods.
urls = [
    ('/users/(.*?)/recipes/(.*?)/like', RecipeLikeHandler),
    ('/users/(.*?)/recipes/(.*?)/clone', RecipeCloneHandler),
    ('/users/(.*?)/recipes/(.*)', RecipeHandler),
    ('/users/(.*?)/recipes', RecipesHandler),
    ('/users/(.*)', UserHandler),
    ('/users', UsersHandler),
    ('/username', UsernameCheckHandler),
    ('/recipes', RecipesHandler),
    ('/profile', ProfileHandler),
    ('/new', RecipeHandler),
    ('/donate', DonateHandler),
    ('/', MainHandler)
]
