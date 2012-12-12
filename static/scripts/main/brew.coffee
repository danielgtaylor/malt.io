# A class to handle brews of beer recipes
class Brew
    # Initialize brew data and handlers
    @init: =>
        $('#brew-button').click (event) =>
            @save @getFromPage()

    # Get brew information from the new brew form
    @getFromPage: =>
        started: $('#brewStartTime').val() + ' ' + $('#brewStartDate').val()
        bottled: $('#brewBottleTime').val() + ' ' + $('#brewBottleDate').val()
        og: parseFloat $('#brewOg').val() or 0
        fg: parseFloat $('#brewFg').val() or 0
        rating: parseInt $('input[name=brewRating]:checked').val() or 0
        notes: $('#brewNotes').val()

    # Save a brew to the data store
    @save: (brew) =>
        $.ajax
            url: location.href + '/brew'
            type: 'post'
            data:
                brew: JSON.stringify brew
            success: (data, status, xhr) =>
                location.reload()
