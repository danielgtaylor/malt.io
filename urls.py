from handlers.auth import AuthHandler, AuthCallbackHandler, \
                          LoginHandler, LogoutHandler
from handlers.brew import BrewHandler
from handlers.donate import DonateHandler
from handlers.formulas import FormulasHandler
from handlers.index import AboutHandler, MainHandler, DashboardHandler
from handlers.messages import MessagesHandler
from handlers.privacy import PrivacyHandler
from handlers.profile import ProfileHandler
from handlers.recipes import RecipesHandler, RecipeEmbedHandler, \
                             RecipeCloneHandler, RecipeHandler, \
                             RecipeXmlHandler, RecipeHistoryHandler
from handlers.users import UsersHandler, UserHandler, UserFollowHandler, \
                           UsernameCheckHandler

# The following maps regular expressions to specific handlers.
# Matched groups become positional arguments to the handler's methods.
urls = [
    ('/users/(.+?)/recipes/(.+?)/clone/?', RecipeCloneHandler),
    ('/users/(.+?)/recipes/(.+?)/brew/?', BrewHandler),
    ('/users/(.+?)/recipes/(.+?)/brew/(.+?)/?', BrewHandler),
    ('/users/(.+?)/recipes/(.+?)/beerxml/?', RecipeXmlHandler),
    ('/users/(.+?)/recipes/(.+?)/history/?', RecipeHistoryHandler),
    ('/users/(.+?)/recipes/(.+?)/history/(.+?)/?', RecipeHandler),
    ('/users/(.+?)/recipes/(.+?)/?', RecipeHandler),
    ('/users/(.+?)/recipes/?', RecipesHandler),
    ('/users/(.+?)/follow/?', UserFollowHandler),
    ('/users/(.+?)/?', UserHandler),
    ('/users/?', UsersHandler),
    ('/username/?', UsernameCheckHandler),
    ('/recipes/?', RecipesHandler),
    ('/messages/?', MessagesHandler),
    ('/profile/?', ProfileHandler),
    ('/new/?', RecipeHandler),
    ('/embed/(.+?)/(.+?)/?', RecipeEmbedHandler),
    ('/homebrew-formulas/?', FormulasHandler),
    ('/donate/?', DonateHandler),
    ('/privacy-policy/?', PrivacyHandler),
    ('/auth/(.*?)/callback/?', AuthCallbackHandler),
    ('/auth/(.*?)/?', AuthHandler),
    ('/login/?', LoginHandler),
    ('/logout/?', LogoutHandler),
    ('/dashboard/?', DashboardHandler),
    ('/about/?', AboutHandler),
    ('/', MainHandler)
]
