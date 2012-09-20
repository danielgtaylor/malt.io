# A class to help process potential usernames and update the user interface
# to reflect whether a username is valid or not, used on the profile page.
class Username
    # A timeout to track when to do a new AJAX call to check the currently
    # typed username.
    @checkTimeout = null
    
    # Javascript spinner styling options
    @spinOpts =
        lines: 13
        length: 2
        width: 2
        radius: 4
        rotate: 0
        color: '#000'
        speed: 1
        trail: 56
        shadow: false
        hwaccel: false
        className: 'spinner'
        zIndex: 1000
        top: 'auto'
        left: 'auto'
    
    # The current spinner, if one exists
    @spinner = null
    
    # Initialize events
    @init: =>
        $('#username').keyup(->
            Username.fixUsername(this)
        )

        $('#username').keypress(->
            Username.fixUsername(this)
        )
    
    # Do an AJAX request to check a username to see if it is valid. This
    # disables the submit button until the check completes, and if the
    # name is valid the button is enabled again.
    @checkUsername: =>
        username = $('#username')[0].value
        element = $('#username-spinner')
        
        # Clear spinner or success/fail data
        element.html('')
        
        # Start spinner
        if @spinner
            @spinner.spin(element[0])
        else
            @spinner = new Spinner(@spinOpts).spin(element[0])
        
        # Do an AJAX call to find out if this name is valid and available
        $.ajax(
            url: '/username'
            type: 'post'
            data:
                username: username
            success: (data, status, xhr) =>
                # Stop the spinner
                @spinner.stop()
                
                # Update the UI, showing whether or not the name is valid
                parent = element.parent().parent().parent()
                if data.available
                    element.html('&#10003;')
                    parent.removeClass('error').addClass('success')
                    $('#profile-save').removeAttr('disabled').removeClass('disabled')
                else
                    element.html('&#8709;')
                    parent.removeClass('success').addClass('error')
        )
    
    # Fix potential issues with the username, such as making it all lowercase
    # and removing all spaces, then set the timeout to check to ensure it is
    # both valid and available.
    @fixUsername: (element) =>
        if @spinner
            @spinner.stop()
        
        element.value = element.value.replace(' ', '').toLowerCase()
        
        if @checkTimeout
            clearTimeout(@checkTimeout)
        
        $('#profile-save').attr('disabled', 'disabled').addClass('disabled')
        @checkTimeout = setTimeout(@checkUsername, 500)
