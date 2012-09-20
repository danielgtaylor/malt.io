class Messages
    # Initialize the messages class by attaching to message click events
    # to setup message rendering and making the latest message selected
    @init: =>
        $('#sendMessage').click(@send)

        $('.messageList').on('click', 'tr', @selected)

        # Set first received message as active and show preview
        $('.messageList tr:first').slice(0, 1).click()

    # Handle user clicks on the message list
    @selected: (event) =>
        row = $(event.currentTarget)
        # Update the live message preview by parsing the message body
        # with marked, a Markdown implementation for javascript
        $('#messagePreview').html(marked(event.currentTarget.dataset.body))

        # Set this message as active
        $('.messageList td').removeClass('active')
        row.children().addClass('active')

        # Mark as read if needed
        if row.hasClass('unread')
            @mark(parseInt(row.attr('id').substr(7)), true)

    # Send a new message to a user
    @send: =>
        # Send this message via an AJAX call, then let the user know
        # whether it was properly sent or if there was an error.
        $.ajax(
            url: '/messages'
            type: 'post'
            data:
                recipient: $('#messageRecipient').val()
                body: $('#messageBody').val()
            success: (data, status, xhr) =>
                # TODO: handle errors
        )

    # Mark a message as read or unread
    @mark: (id, read) =>
        $('#message' + id).removeClass('unread')

        $.ajax(
            url: '/messages'
            type: 'put'
            data:
                message: JSON.stringify(
                    id: id
                    read: read
                )
            success: (data, status, xhr) =>
                # TODO: handle errors
        )

    # Delete a message
    @delete: (id) =>
        $('#message' + id).remove()

        $.ajax(
            url: '/messages'
            type: 'delete'
            data:
                message: JSON.stringify(
                    id: id
                )
            success: (data, status, xhr) =>
                # TODO: handle errors
        )
