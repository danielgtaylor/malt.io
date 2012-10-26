# Class to tweak history display (some CSS adjustments) and add various fun
# features. Note the name is not History to avoid clashing with access to
# browser history functionality.
class RecipeHistory
    # Initialize click handlers for options buttons and perform CSS tweaks
    # for nicer display of oversized <code> and <strong> tags.
    @init: ->
        # Adjust the look of <code> and <strong> tags to make them appear
        # to be block-inline by giving them absolute position and adjusting
        # the margin or padding of surrounding elements to adjust for their
        # size. This gives us a nice floating block instead of wrapping text.
        # The reason regular block-inline won't work is because it requires
        # specifying a fixed width, which we don't know until we're rendered in
        # an actual browser.
        # Ignore code tags that are in the sub-list of a recipe change, since
        # there are more than one per line and we can't use this simple
        # positioning logic there.
        spans = $('.entry strong, .entry code').not('li li code')
        if spans.length > 0
            # Use the line-height of the elements to help size and position the
            # content. This will break if the CSS is changed so the code and
            # strong lineheights are different.
            lineheight = parseInt(spans.css('line-height'))

            # Go through each element and perform adjustments
            for element in spans
                element = $(element)
                # Only perform adjustments on content rendered as more than one
                # line, since that's what the fix is all about
                if element.height() > lineheight
                    # Code tags have different padding from strong tags, so
                    # treat each slightly differently
                    if element.prop('tagName').toLowerCase() == 'code'
                        # The margin changes are needed to align the baseline
                        # of the code tag's content with the surrounding text,
                        # which isn't required for the strong tag
                        element.css({
                            'position': 'absolute',
                            'margin-left': '5px',
                            'margin-top': '-2px'
                            })
                        element.parent().css('margin-top', '+=2px')
                    else
                        element.css({
                            'position': 'absolute',
                            'margin-left': '5px'
                            })

                    # Use the new height to find an adjustment for the next
                    # element beneath the current element. This could be a
                    # following <ul>, the <li> following the parent <li>, or
                    # the element's grandparent (the containing <div>)
                    adjust = element.height() - lineheight + 3
                    if element.next().length > 0
                        element.next().css('margin-top', '+=' + adjust)
                    else if element.parent().next().length > 0
                        element.parent().next().css('margin-top', '+=' + adjust)
                    else
                        element.parent().parent().css('padding-bottom', '+=' + (adjust - 7))

        # A list of elements that represent changes in the recipe snippets,
        # allowing easier toggling of highlights
        @highlighter = $()
        # The recipe titles to compare
        titles = $('div.recipe > .title')
        # The recipe descriptions to compare
        descriptions = titles.siblings('span')
        # The recipe buttons (collected as groups) to compare
        buttongroups = $('div.recipe > .btn-group')

        # Look for changes in titles and descriptions compared to previous
        # versions
        for set in [titles, descriptions]
            # Loop through the actual titles or descriptions, ignoring the last
            # element because it has nothing to compare to
            for i in [0 ... set.length - 1]
                # Compare the text with the next element in the list (previous
                # recipe, since the order is descending)
                if $.trim($(set[i]).text()) != $.trim($(set[i + 1]).text())
                    # If not equal, add to the list of highlight elements
                    @highlighter = @highlighter.add(set[i])

        # Look for changes in the buttons compared to previous versions
        # Again ignore the last element
        for i in [0 ... buttongroups.length - 1]
            # Get the actual buttons in this group and the next group to
            # compare corresponding buttons across groups
            buttons = $(buttongroups[i]).children()
            siblings = $(buttongroups[i + 1]).children()

            # Include the last element this time since there's a 1-to-1 mapping
            # of buttons between groups
            for j in [0 ... buttons.length]
                # Compare each button with its counterpart
                if $.trim($(buttons[j]).text()) != $.trim($(siblings[j]).text())
                    # If not equal, add to the list of highlight elements
                    @highlighter = @highlighter.add(buttons[j])

        # Wrap the highlight elements with a span so we can highlight their
        # contents by adding the highlight class to the inner span. Since it's
        # visually jarring, highlights are disabled by default.
        @highlighter.wrapInner('<span></span>')

        # Add click handlers for options buttons
        $('#highlightbtn').click(@toggleHighlight)
        $('#tagsbtn').click(@toggleTags)
        $('#detailsbtn').click(@toggleDetails)

        # Add some text that will be displayed if tags are hidden. This gives
        # a nice alternative to the colorful tags. This is hidden by default.
        $('.entry .tags').after('<span style="display:none">Edited</span> ')

        # Display the options button. It's hidden by default because it's
        # useless without javascript
        $('#options').toggle()

    # Toggle difference highlights on recipes.
    @toggleHighlight: (event) =>
        # Toggle the highlight class on the spans we added
        @highlighter.children().toggleClass('highlight')
        event.preventDefault()

    # Toggle visibility of tags, showing or hiding the alternate text instead
    @toggleTags: (event) =>
        # Toggle the visibility of the tags, then move to the alternate text
        # and toggle that, then check the visibility of the alternate text to
        # determine whether the tags are showing or hidden
        if $('.entry .tags').toggle().next().toggle().is(':hidden')
            # Tags are showing
            $(event.currentTarget).text('Hide Tags')
        else
            # Tags are hidden
            $(event.currentTarget).text('Show Tags')
        event.preventDefault()

    # Toggle visibility of ingredient change details (sub-lists to changes)
    @toggleDetails: (event) =>
        # Need to check if each element we're about to show or hide has special
        # margins set to apply those margins to surrounding elements when this
        # element gets shown or hidden
        elements = $('.entry li ul')
        visible = elements.is(':visible')

        for element in elements
            element = $(element)
            margin = parseInt(element.css('margin-top'))
            if margin != 0
                # Adjust the height of the following element or container. This
                # could be the <li> following the parent <li>, or the element's
                # grandparent (the containing <div>)
                if element.parent().next().length > 0
                    element.parent().next().css('margin-top', if visible then '+=' + margin else '-=' + margin)
                else
                    element.parent().parent().css('padding-bottom', if visible then '+=' + (margin - 7) else '-=' + (margin - 7))

        # Toggle visibility
        elements.toggle()

        # visible is the old visibility, so visible === true means now hidden
        if not visible
            $(event.currentTarget).text('Hide Details')
        else
            $(event.currentTarget).text('Show Details')
        event.preventDefault();
