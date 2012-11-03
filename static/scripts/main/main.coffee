# Initialize various things on page load
$(document).ready(->
    # Setup tooltips
    $('[title]').tooltip({
        delay: {
            show: 500,
            hide: 100
        }
    })

    # Setup search bar
    $('#searchForm').submit((event) =>
        event.preventDefault();
        window.location.href = 'http://www.google.com/search?q=' + $('#searchQuery').val() + '+site%3Awww.malt.io'
    )

    # Show any dialogs based on URL
    $(window.location.hash + 'Modal').modal('show');

    # Keyboard shortcuts
    Mousetrap.bindGlobal 'ctrl+m u', =>
        window.location.href = '/users'

    Mousetrap.bindGlobal 'ctrl+m r', =>
        window.location.href = '/recipes'

    Mousetrap.bindGlobal 'ctrl+m n', =>
        window.location.href = '/new'

    Mousetrap.bindGlobal 'ctrl+m p', =>
        window.location.href = '/users/' + user
)
