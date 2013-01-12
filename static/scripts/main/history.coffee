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

                    # Use the new height to find an adjustment for either the
                    # next element beneath the current element or for the
                    # parent. This could be a following <ul> or the parent
                    # <li>.
                    adjust = element.height() - lineheight + 3
                    if element.next().length > 0
                        element.next().css('margin-top', '+=' + adjust)
                    else
                        element.parent().height('+=' + adjust)

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

        # Add the visibility flag for details
        @visible = true

        # Setup for expanding and collapsing long entries
        # We'll only add collapsing if the details as shown are taller than
        # ten times the line height (completely arbitrary, but looks good)
        details = $('.entry .details')
        height = 10 * parseInt(details.css('line-height'))
        for detail in details
            detail = $(detail)
            # Compare height to see if we need to make this detail collapse
            if height > detail.height()
                continue
            # Now that we know the details are too tall, we need to find
            # a good point to cut off the list. We don't want to cut off
            # only a single item, nor do we want to cut subitems away from
            # their parent.
            listitems = detail.children('ul').children('li')
            if listitems.length < 2
                continue
            # Find the first item that puts us over the height limit
            for i in [0 ... listitems.length]
                if listitems[i].offsetTop > height
                    break
            # Check if we ended on the last item
            if i >= listitems.length - 1
                continue
            # Create the "more changes" link
            detail.append($(document.createElement('a'))
                            .addClass('more')
                            .attr('href', '#')
                            .click(@toggleExpand)
                            .text("Show #{listitems.length - i} more changes"))
            # Perform cutting!
            for j in [i ... listitems.length]
                listitems.eq(j).toggle()

            # Set some data so we don't need to do these calculations again
            detail.data({
                'ci': i,
                'es': false,
                'ot': "Show #{listitems.length - i} more changes",
                'at': "Show #{listitems.length - i} fewer changes"
            })

        # Adjust the look of the line so it doesn't pop out the bottom of the
        # first history element
        line = $('div.line')
        uparrow = $('div.uparrow').last()
        line.css('bottom', '+=' + (line.offset().top + line.height() - uparrow.offset().top - 10))

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
        elements = $('.entry li ul')

        # Toggle visibility
        @visible = !@visible
        elements.toggle(@visible)

        # Need to check if each element we're about to show or hide has special
        # margins set to apply those margins to surrounding elements when this
        # element gets shown or hidden
        for element in elements
            element = $(element)
            margin = parseInt(element.css('margin-top'))
            if margin != 0
                # Adjust the height of the parent <li>
                if @visible
                    element.parent().css('height', 'auto')
                else
                    element.parent().height('+=' + margin)

        # Update the text to reflect the new state
        if @visible
            $(event.currentTarget).text('Hide Details')
        else
            $(event.currentTarget).text('Show Details')
        event.preventDefault()

    # Toggle expanding / collapsing details for a single entry
    @toggleExpand: (event) =>
        # Get the detail div so we can perform the transitions we need
        a = $(event.currentTarget)
        detail = $(a).parent()
        data = detail.data()

        # Update the displayed text depending on whether we're currently
        # showing (true) or hiding (false)
        a.text(if data['es'] then data['ot'] else data['at'])

        # Toggle visibility for the listitems
        listitems = detail.children('ul').children('li')
        for i in [data['ci'] ... listitems.length]
            listitems.eq(i).toggle()

        detail.data('es', !data['es'])
        event.preventDefault()
