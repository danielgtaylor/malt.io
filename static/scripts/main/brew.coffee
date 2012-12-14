# A class to handle brews of beer recipes
class Brew
    # Initialize brew data and handlers
    @init: =>
        $('#brew-button').click (event) =>
            @save @getFromPage()

    # Get brew information from the new brew form
    @getFromPage: =>
        id: $('#brewId').val()
        started: $('#brewStartTime').val() + ' ' + $('#brewStartDate').val()
        bottled: $('#brewBottleTime').val() + ' ' + $('#brewBottleDate').val()
        og: parseFloat $('#brewOg').val() or 0.0
        fg: parseFloat $('#brewFg').val() or 0.0
        rating: parseInt $('input[name=brewRating]:checked').val() or 0
        notes: $('#brewNotes').val()

    # Show the brew dialog with the given information
    @show: (id, startTime, startDate, bottleTime, bottleDate, og, fg, rating, notes) =>
        $('#brewId').val id
        $('#brewStartTime').val startTime
        $('#brewStartDate').val startDate
        $('#brewBottleTime').val bottleTime
        $('#brewBottleDate').val bottleDate
        $('#brewOg').val og or ''
        $('#brewFg').val fg or ''
        $('input[name=brewRating]').rating 'select', 3
        $('#brewNotes').val notes

        $('#brewModal').modal 'show'

    # Save a brew to the data store
    @save: (brew) =>
        loc = location.href + '/brew'
        if brew.id
            loc += '/' + brew.id

        $.ajax
            url: loc
            type: 'post'
            data:
                brew: JSON.stringify brew
            success: (data, status, xhr) =>
                location.reload()
