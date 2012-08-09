class Messages
    # Initialize the messages class by attaching to message click events
    # to setup message rendering and making the latest message selected
    @init: =>
        $('.messageList').on('click', 'tr', (event) =>
            # Update the live message preview by parsing the message body
            # with marked, a Markdown implementation for javascript
            $('#messagePreview').html(marked(event.currentTarget.dataset.body))

            $('.messageList td').removeClass('active')
            $(event.currentTarget).children().addClass('active')
        )

        # Set first received message as active and show preview
        $('.messageList tr:first').slice(0, 1).click()
