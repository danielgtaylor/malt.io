# Initialize various things on page load
$(document).ready(->
    # Setup tooltips
    $('[title]').tooltip({
        delay: {
            show: 500,
            hide: 100
        }
    })
)
