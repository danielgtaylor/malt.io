# A class for the intro slideshow
class Slideshow
    @timeout: null

    @init: =>
        jmpressOpts =
            fullscreen: false
            animation:
                transitionDuration: '0.8s'
            viewPort:
                width: 480
                height: 250
                maxScale: 1
            hash:
                use: false
            mouse:
                clickSelects: false

        slideshow = $ '.jmpress-wrapper'

        # Initialize slideshow
        slideshow.jmpress jmpressOpts

        # Setup background color fading
        slideshow.jmpress 'setActive', (slide, eventData) ->
            this.removeClass 'plain lightblue blue yellow green red orange pink purple dark'
            this.addClass slide.data('color')

            if slide.data 'seconds'
                if Slideshow.timeout
                    clearTimeout Slideshow.timeout

                Slideshow.timeout = Util.setTimeout parseFloat(slide.data 'seconds' ) * 1000, ->
                    $('.jmpress-wrapper').jmpress 'next'

        slideshow.addClass slideshow.jmpress('active').data('color')

        $('#learnMoreButton').click (event) =>
            @show()
            event.preventDefault()

        $('#startSlidesButton').click (event) =>
            @start()
            event.preventDefault()

    # Show the slideshow and hide other elements
    @show: =>
        $('#screenshotsContainer').hide()
        $('#jmpress').fadeIn();

    @start: =>
        @next()

    @next: =>
        $('.jmpress-wrapper').jmpress 'next'
