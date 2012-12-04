# Initialize various things on page load
$(document).ready(->
    # Setup tooltips
    $('[title]').tooltip({
        delay: {
            show: 500,
            hide: 100
        }
    })

    # Setup date / time pickers
    $('.datepicker').datepicker(
        format: 'd b yyyy'
    )

    $('.timepicker').timepicker(
        showMeridian: false
    )

    # Setup search bar
    $('#searchForm').submit((event) =>
        event.preventDefault();
        window.location.href = 'http://www.google.com/search?q=' + $('#searchQuery').val() + '+site%3Awww.malt.io'
    )

    # Show any dialogs based on URL
    $(window.location.hash + 'Modal').modal('show');

    # Keyboard shortcuts
    Mousetrap.bind ['/', '?'], =>
        $('#shortcutsModal').modal('show')

    Mousetrap.bindGlobal ['ctrl+m h', 'command+m h'], =>
        window.location.href = '/'

    Mousetrap.bindGlobal ['ctrl+m u', 'command+m u'], =>
        window.location.href = '/users'

    Mousetrap.bindGlobal ['ctrl+m r', 'command+m r'], =>
        window.location.href = '/recipes'

    Mousetrap.bindGlobal ['ctrl+m n', 'command+m n'], =>
        window.location.href = '/new'

    if user
        Mousetrap.bindGlobal ['ctrl+m p', 'command+m p'], =>
            window.location.href = '/users/' + user
)
