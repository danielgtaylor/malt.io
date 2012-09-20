# A class to handle user-related events and functionality, such as following
# another user.
class User
    # Initialize event handlers and setup
    @init: =>
        $('#followButton').click(@onFollow)

    # Handle clicks on the follow button, by either following or stopping
    # to follow another user.
    @onFollow: (event) =>
        if not user
            window.location.href = '/profile'
            return

        if $('#followButton').hasClass('active')
            action = 'delete'
        else
            action = 'post'

        $.ajax(
            url: location.href + '/follow'
            type: action
            success: (data, status, xhr) =>
                # TODO: handle errors here
        )
