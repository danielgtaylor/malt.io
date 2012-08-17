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
)
