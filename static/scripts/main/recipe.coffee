# Recipe class to handle recipe-related functionality from rendering
# to editing of recipes on various pages.
class Recipe
    # Values used to estimate the next time for a hop or spice addition
    @NEXT_HOP_SCHEDULE:
        90: 60
        60: 15
        15: 5
        5: 1
        1: 1
    
    # Approximate prices for various malts per pound, used to calculate a
    # recipe price approximation and per-bottle cost.
    @MALT_PRICES: [
        [/dry|dme/i, 4.00],
        [/liquid|lme/i, 3.00],
        [/.*/i, 2.00]
    ]
    
    # Approximate prices for hops and spices per ounce, used to calculate a
    # recipe price approximation and per-bottle cost.
    @HOP_PRICES: [
        [/.*/i, 2.00]
    ]
    
    # Approximate prices for yeasts, used to calculate a recipe price
    # approximation and per-bottle cost.
    @YEAST_PRICES: [
        [/wyeast|white labs|wlp/i, 7.00],
        [/.*/i, 3.50]
    ]

    # Regular expressions to match for steeping grains, such as caramel malts.
    # This is used to create the recipe timeline.
    @STEEP_FERMENTABLES = /biscuit|black|cara|chocolate|crystal|munich|roast|special ?b|toast|victory|vienna|steep/i

    # Regular expressions to match for boiling sugars (DME, LME, etc).
    # This is used to create the recipe timeline.
    @BOIL_FERMENTABLES = /candi|candy|dme|dry|extract|honey|lme|liquid|sugar|syrup|turbinado|boil/i
    
    # Regular expressions to match for dry hopping vs. mash/boil additions
    @DRY_SPICE = /primary|secondary|dry/i

    # Initialize the recipe by rendering color swatches on the page and
    # setting up event delegates to handle editing if the recipe is put
    # into edit view.
    @init: =>
        # Setup color swatches
        $('.srm[data-srm]').each((index, element) =>
            element.style.backgroundColor = Util.srmToRgb(element.getAttribute('data-srm'))
        )

        # Setup action buttons
        if not @oldVersion
            $('#edit-button').click @enableEdit
            $('#delete-button').click @onDelete

        $('#clone-button').click @onCloned
        $('#scale-button').click @onScaled
        $('#widget-button').click @onWidget
        $('#ferment-button').click @onFerment
        
        # Setup editing delegates
        $('#fermentables_data, #hops_data, #yeast_data, .editable').on('keydown', '[contentEditable]', (event) =>
            @checkUpdateStats(event)
        )
        $('#fermentables_data, #hops_data, #yeast_data, .editable').on('blur', '[contentEditable]', (event) =>
            @updateStats()
        )

        # Setup validation delegates
        $('#fermentables_data, #hops_data, #yeast_data, .editable').on('keypress', '.validate', Util.validateInput)

        # Setup row removal delegates
        $('#fermentables_data, #hops_data, #yeast_data').on('click', '.remove', (event) =>
            @removeRow(event.target.parentNode)
            return false
        )
        
        # Setup focus delegates
        $('#fermentables_data, #hops_data, #yeast_data, .editable').on('focus', '[contentEditable]', (event) =>
            Util.selectAll(event)
        )

        # If this is the new recipe page, then see if we have a locally saved
        # recipe to load.
        if window.location.pathname is '/new'
            @loadLocal()

        # Setup scaling
        $('#gallonsSlider').noUiSlider('init',
            knobs: 1
            connect: 'lower'
            scale: [0, 40]
            start: parseFloat($('#gallonsValue').text()) * 2
            change: =>
                $('#gallonsValue').text(($('#gallonsSlider').noUiSlider('value')[1] / 2.0).toFixed(1))
        )

        $('#boilGallonsSlider').noUiSlider('init',
            knobs: 1
            connect: 'lower'
            scale: [0, 40]
            start: parseFloat($('#boilGallonsValue').text()) * 2
            change: =>
                $('#boilGallonsValue').text(($('#boilGallonsSlider').noUiSlider('value')[1] / 2.0).toFixed(1))
        )

        # Setup mash sliders
        $('#quartsSlider').noUiSlider 'init',
            knobs: 1
            connect: 'lower'
            scale: [1, 16]
            start: parseFloat($('#quartsValue').text()) * 4
            change: =>
                $('#quartsValue').text(($('#quartsSlider').noUiSlider('value')[1] / 4.0).toFixed(2))

        $('#mashoutSlider').noUiSlider 'init',
            knobs: 1
            connect: 'lower'
            scale: [0, 200]
            start: parseInt $('#mashoutValue').text()
            change: =>
                $('#mashoutValue').text $('#mashoutSlider').noUiSlider('value')[1]

        $('#spargeSlider').noUiSlider 'init',
            knobs: 1
            connect: 'lower'
            scale: [0, 16]
            start: parseFloat($('#spargeValue').text()) * 4
            change: =>
                $('#spargeValue').text(($('#spargeSlider').noUiSlider('value')[1] / 4.0).toFixed(2))

        # Setup ferment sliders
        $('#primarySlider').noUiSlider 'init',
            knobs: 1
            connect: 'lower'
            scale: [0, 30]
            start: parseInt $('#primaryDays').val()
            change: =>
                $('#primaryValue').text $('#primarySlider').noUiSlider('value')[1]

        $('#primaryTempSlider').noUiSlider 'init',
            knobs: 1
            connect: 'lower'
            scale: [32, 100]
            start: parseFloat $('#primaryTemp').val()
            change: =>
                $('#primaryTempValue').text $('#primaryTempSlider').noUiSlider('value')[1].toFixed(1)

        $('#secondarySlider').noUiSlider 'init',
            knobs: 1
            connect: 'lower'
            scale: [0, 30]
            start: parseInt $('#secondaryDays').val()
            change: =>
                $('#secondaryValue').text $('#secondarySlider').noUiSlider('value')[1]

        $('#secondaryTempSlider').noUiSlider 'init',
            knobs: 1
            connect: 'lower'
            scale: [32, 100]
            start: parseFloat $('#secondaryTemp').val()
            change: =>
                $('#secondaryTempValue').text $('#secondaryTempSlider').noUiSlider('value')[1].toFixed(1)

        $('#tertiarySlider').noUiSlider 'init',
            knobs: 1
            connect: 'lower'
            scale: [0, 30]
            start: parseInt $('#tertiaryDays').val()
            change: =>
                $('#tertiaryValue').text $('#tertiarySlider').noUiSlider('value')[1]

        $('#tertiaryTempSlider').noUiSlider 'init',
            knobs: 1
            connect: 'lower'
            scale: [32, 100]
            start: parseFloat $('#tertiaryTemp').val()
            change: =>
                $('#tertiaryTempValue').text $('#tertiaryTempSlider').noUiSlider('value')[1].toFixed(1)

        # Was the page loaded in edit mode? If so, enable editing!
        if window.location.pathname is '/new' or window.location.hash is '#edit'
            @enableEdit()

    # Initialize recipe import handling
    @initImport: =>
        $('#importButton').click((event) =>
            $('#importRecipesForm').submit();
        )

    # Get info about the current focused cell
    @currentFocusInfo: =>
        inTable = false
        tbody = null
        row = null
        trIndex = 0
        tdIndex = 0

        if $('#fermentables_data, #hops_data, #yeast_data').has(document.activeElement).length
            inTable = true
            row = $(document.activeElement).parent()
            tbody = row.parent()
            row.children().each((i, element) =>
                if element is document.activeElement
                    tdIndex = i
            )
            tbody.children().each((i, element) =>
                if element is row[0]
                    trIndex = i
            )

        return [inTable, tbody, row, trIndex, tdIndex]

    # Handle clicks on the clone button, creating a cloned copy of another
    # user's recipe
    @onCloned: (event) =>
        if not user
            window.location.href = '/profile'
            return

        _gaq.push(['_trackEvent', 'Recipe', 'Clone', $('#recipeName').text()])

        $.ajax(
            url: location.href + '/clone'
            type: 'post'
            success: (data, status, xhr) =>
                # TODO: handle errors here
                if data.redirect
                    window.location = data.redirect
        )

    # Scale a recipe to the desired batch and boil sizes
    @onScaled: (event) =>
        _gaq.push(['_trackEvent', 'Recipe', 'Scale', $('#recipeName').text()])
        scaleIngredients = $('#scaleIngredients .active').text() is 'On'
        @scale(parseFloat($('#gallonsValue').text()), parseFloat($('#boilGallonsValue').text()), scaleIngredients)

    # Show widget dialog
    @onWidget: (event) =>
        _gaq.push(['_trackEvent', 'Recipe', 'ViewWidget', $('#recipeName').text()])
        setTimeout(->
            frame = $('#widgetModal iframe').get(0)
            frame.src = frame.getAttribute('data-src')
        , 300)

    # Update ferment information based on chosen day counts from dialog
    @onFerment: =>
        @updateFerment $('#primaryValue').text(), $('#primaryTempValue').text(), $('#secondaryValue').text(), $('#secondaryTempValue').text(), $('#tertiaryValue').text(), $('#tertiaryTempValue').text()

    # Set the ferment values and update the recipe page
    @updateFerment: (primaryDays, primaryTemp, secondaryDays, secondaryTemp, tertiaryDays, tertiaryTemp) =>
        _gaq.push(['_trackEvent', 'Recipe', 'Ferment', ''])

        $('#primaryDays').val primaryDays
        $('#primaryTemp').val primaryTemp
        $('#secondaryDays').val secondaryDays
        $('#secondaryTemp').val secondaryTemp
        $('#tertiaryDays').val tertiaryDays
        $('#tertiaryTemp').val tertiaryTemp

        @updateStats()

    # Set the aging days and update the recipe page
    @updateAging: (days) =>
        _gaq.push(['_trackEvent', 'Recipe', 'Aging', days])

        $('#agingDays').val days

        @updateStats()

    # Enable recipe edit mode
    @enableEdit: =>
        if window.brokenBrowser
            $('#badBrowserModal').modal('show')
            return

        _gaq.push(['_trackEvent', 'Recipe', 'Edit', $('#recipeName').text()])

        $('#recipeName, #recipeDescription, #bottling_temp, #bottling_pressure, #mashEfficiency, #steepEfficiency').attr('contentEditable', 'true')
        $('#fermentables_data tr td:nth-child(2), #fermentables_data tr td:nth-child(3), #fermentables_data tr td:nth-child(4), #fermentables_data tr td:nth-child(5), #fermentables_data tr td:nth-child(6), #fermentables_data tr td:nth-child(8), #hops_data tr td:nth-child(1), #hops_data tr td:nth-child(2), #hops_data tr td:nth-child(3), #hops_data tr td:nth-child(4), #hops_data tr td:nth-child(5), #hops_data tr td:nth-child(6), #yeast_data tr td:nth-child(1), #yeast_data tr td:nth-child(2), #yeast_data tr td:nth-child(3), #yeast_data tr td:nth-child(4)').attr('contentEditable', 'true')
        $('#saveMsg, .edit-show').show()
        $('#fermentmenu').css('display', 'inline-block')
        $('#stylebtn').css('top', '8.5px')
        @adjustStyleButton()
        $('.edit-hide').hide()

        # Keyboard shortcuts
        Mousetrap.bind ['f', 's', 'y'], (event, combo) =>
            if combo is 'f'
                $('#newFermentable').click()
            else if combo is 's'
                $('#newSpice').click()
            else
                $('#newYeast').click()
            off

        Mousetrap.bindGlobal 'enter', =>
            # If we are currently in one of the tables, move to next row if it exists
            [inTable, tbody, row, trIndex, tdIndex] = @currentFocusInfo()
            if inTable
                if tbody.children().length > trIndex + 1
                    # Select the next row
                    $($(tbody.children()[trIndex + 1]).children()[tdIndex]).focus()
                else
                    # Move to the next table, creating a row if none exists
                    id = tbody.attr 'id'
                    if id is 'fermentables_data'
                        if $('#hops_data').children().length
                            $('#hops_data tr:first td:nth-child(4)').focus()
                        else
                            $('#newSpice').click()
                    else if id is 'hops_data'
                        if $('#yeast_data').children().length
                            $('#yeast_data tr:first td:nth-child(1)').focus()
                        else
                            $('#newYeast').click()

        Mousetrap.bindGlobal 'shift+enter', =>
            # If we are currently in one of the tables, move to previous row if it exists
            [inTable, tbody, row, trIndex, tdIndex] = @currentFocusInfo()
            if inTable
                if trIndex > 0
                    # Select the previous row
                    $($(tbody.children()[trIndex - 1]).children()[tdIndex]).focus()
                else
                    # Move up to the previous table if possible
                    id = tbody.attr 'id'
                    if id is 'hops_data'
                        $('#fermentables_data tr:last td:nth-child(4)').focus()
                    else if id is 'yeast_data'
                        $('#hops_data tr:last td:nth-child(4)').focus()

        Mousetrap.bindGlobal ['ctrl+enter', 'command+enter'], =>
            # Add a new row to the current table and select it
            if $('#hops_data').has(document.activeElement).length
                $('#newSpice').click()
            else if $('#yeast_data').has(document.activeElement).length
                $('#newYeast').click()
            else
                # Either fermentable item is selected or no item is selected
                $('#newFermentable').click()
            off

        Mousetrap.bindGlobal ['ctrl+s', 'command+s'], =>
            # Save the current recipe, overriding saving the HTML page
            @save()
    
    # Disable recipe edit mode, e.g. after a save
    @disableEdit: =>
        $('#recipeName, #recipeDescription, #batchSize, #boilSize, #bottling_temp, #bottling_pressure, #mashEfficiency, #steepEfficiency').removeAttr('contentEditable')
        $('#fermentables_data tr td:nth-child(2), #fermentables_data tr td:nth-child(3), #fermentables_data tr td:nth-child(4), #fermentables_data tr td:nth-child(5), #fermentables_data tr td:nth-child(7), #hops_data tr td:nth-child(1), #hops_data tr td:nth-child(2), #hops_data tr td:nth-child(3), #hops_data tr td:nth-child(4), #hops_data tr td:nth-child(5), #hops_data tr td:nth-child(6), #yeast_data tr td:nth-child(1), #yeast_data tr td:nth-child(2), #yeast_data tr td:nth-child(3), #yeast_data tr td:nth-child(4)').removeAttr('contentEditable')
        $('#saveMsg, .edit-show').hide()
        $('.edit-hide').show()

        # Remove editing shortcuts
        Mousetrap.unbind ['f', 's', 'y']
        Mousetrap.unbind 'enter'
        Mousetrap.unbind 'shift+enter'
        Mousetrap.unbind ['ctrl+enter', 'command+enter']
        Mousetrap.unbind ['ctrl+s', 'command+s']
    
    # Handle clicks on the delete button, removing a recipe
    @onDelete: (event) =>
        _gaq.push(['_trackEvent', 'Recipe', 'Delete', $('#recipeName').text()])
        $.ajax(
            url: location.href
            type: 'delete'
            success: (data, status, xhr) =>
                # TODO: handle errors here
                if data.redirect
                    window.location = data.redirect
        )

    # Add a fermentable row to the fermentables table based on a fermentable
    # template button item. Select the added row and update recipe stats.
    @addFermentableRowTemplate: (template) =>
        @addFermentableRow(1.0,
                           template.getAttribute('data-description'),
                           '',
                           template.getAttribute('data-ppg'),
                           template.getAttribute('data-srm'))
        $('#fermentables_data tr:last td:nth-child(2)').focus()
        @updateStats()

    # Add a fermentable row to the fermentables table.
    @addFermentableRow: (weight, description, late, ppg, srm) =>
        table = $('#fermentables_data')[0]
        lb = Math.floor(weight)
        oz = Math.round((weight - lb) * 16)
        row = '<tr><td class="num percent">?</td><td class="num validate positive integer" contentEditable="true">' + lb + '</td><td class="num validate positive integer" contentEditable="true">' + oz + '</td><td contentEditable="true">' + description + '</td><td contentEditable="true">' + late + '</td><td class="num validate positive integer" contentEditable="true">' + ppg + '</td><td class="num"><span class="srm" data-srm="' + srm + '" style="background-color: ' + Util.srmToRgb(srm) + '"></span> </td><td class="num validate positive integer" style="border-left: none;" contentEditable="true">' + srm + '</td><td class="edit-show" style="display: block; padding: 10px 8px;"><a href="#" class="remove"><i class="icon-remove"></i></a></td></tr>'
        table.innerHTML += row
    
    # Add a hop/spice row to the hops and spices table based on a hop
    # template button item
    @addHopRowTemplate: (template) =>
        # Try to guess a reasonable time for the next addition
        if parseFloat(template.getAttribute('data-aa'))
            latest = parseInt($('#hops_data tr:last td:nth-child(2)').html?()) || 90
            next = Recipe.NEXT_HOP_SCHEDULE[latest] or 5
            form = 'pellet'
        else
            next = 5
            form = 'ground'

        @addHopRow('boil', next, 1.0, template.getAttribute('data-description'),
                   template.getAttribute('data-aa'), form)

        $('#hops_data tr:last td:nth-child(1)').focus()
        @updateStats()

    # Add a hop row to the spices table
    @addHopRow: (use, time, weight, description, aa, form) =>
        table = $('#hops_data')[0]

        row = '<tr><td contentEditable="true">' + use + '</td><td class="num" contentEditable="true">' + time + '</td><td class="num validate positive number" contentEditable="true">' + weight + '</td><td contentEditable="true">' + description + '</td><td contentEditable="true">' + form + '</td><td class="num validate positive number" contentEditable="true">' + aa + '</td><td class="edit-show" style="display: block"><a href="#" class="remove"><i class="icon-remove"></i></a></td></tr>'
        table.innerHTML += row
    
    # Add a yeast/bug row to the yeast and other bugs table based on a yeast
    # template button item
    @addYeastRowTemplate: (template) =>
        @addYeastRow(template.getAttribute('data-description'),
                     template.getAttribute('data-type'),
                     template.getAttribute('data-form')
                     template.getAttribute('data-attenuation'))
        $('#yeast_data tr:last td:nth-child(1)').focus()
        @updateStats()

    # Add a yeast/bug to the yeast and other bugs table
    @addYeastRow: (description, type, form, attenuation) =>
        table = $('#yeast_data')[0]
        row = '<tr><td contentEditable="true">' + description + '</td><td contentEditable="true">' + type + '</td><td contentEditable="true">' + form + '</td><td class="num validate positive number" contentEditable="true">' + attenuation + '</td><td class="edit-show" style="display: block"><a href="#" class="remove"><i class="icon-remove"></i></a></td></tr>'
        table.innerHTML += row
    
    # Remove a row from the table in which it currently resides and update
    # the recipe info
    @removeRow: (element) =>
        row = element.parentNode.parentNode
        row.parentNode.removeChild(row)
        @updateStats()
    
    # Check whether the recipe info should be updated
    @checkUpdateStats: (event) =>
        #console.debug(event.which)
        switch event.which
            when 9   # Tab
                @updateStats()
            when 13  # Enter
                event.preventDefault()
                @updateStats()

    # Reorder the rows of a table based on an attribute and custom sort
    # function. Rows should be an array of [[attribute, element],
    # [attribute, element], ...].
    @reorderRows: (tbody, rows, sortFunc = (x, y) -> y[0] - x[0]) =>
        active = document.activeElement
        rows.sort(sortFunc)
        for [attrib, row] in rows
            tbody.append(row)
            for child in row.children
                if child is active
                    $(child).focus();
    
    # Are we mashing? Guess based on ingredients and overrides.
    @getMashingInfo: =>
        mashing = false

        $('#fermentables_data tr').each((index, element) =>
            desc = $(element.children[3]).text()

            if /mash/i.exec(desc) or not (@BOIL_FERMENTABLES.exec(desc) or @STEEP_FERMENTABLES.exec(desc))
                mashing = true
        )

        return mashing

    # Get information about a fermentable table row, such as the weight, ppg
    # gravity, addition type, etc.
    @getFermentableInfo: (element, gallons, mashing) =>
        lb = parseInt($(element.children[1]).text()) or 0
        oz = parseInt($(element.children[2]).text()) or 0
        desc = $(element.children[3]).text()
        late = ($(element.children[4]).text() or '') in ['y', 'yes']
        ppg = parseInt($(element.children[5]).text()) or 0
        srm = parseInt($(element.children[7]).text()) or 0

        mashEfficiency = parseInt($('#mashEfficiency').text()) / 100.0
        steepEfficiency = parseInt($('#steepEfficiency').text()) / 100.0
        
        weight = lb + (oz / 16.0)
        gravity = ppg * weight / gallons

        forced = false
        if /mash/i.exec(desc)
            addition = 'mash'
            forced = true
        else if /steep/i.exec(desc)
            addition = 'steep'
            forced = true
        else if /boil/i.exec(desc)
            addition = 'boil'
            forced = true
        else if @BOIL_FERMENTABLES.exec(desc)
            addition = 'boil'
        else if @STEEP_FERMENTABLES.exec(desc)
            addition = 'steep'
        else
            addition = 'mash'

        # If this grain is normally steeped but we are mashing, then
        # let's be sure to include this as a mashed grain unless the
        # author forced the inclusion of a steeping step.
        if mashing and addition is 'steep' and not forced
            addition = 'mash'

        if addition is 'steep'
            # Steeped grains have considerably lower efficiency
            gravity *= steepEfficiency
        else if addition is 'mash'
            # Mashed grains have an average efficiency of about 75%
            gravity *= mashEfficiency

        return [lb, oz, desc, late, ppg, srm, weight, gravity, addition, forced]

    # Update the recipe info. This calculates color, alcohol percentage,
    # original and final gravity, bitterness, calories, priming information,
    # and more. This should be called anytime the recipe changes in some way.
    @updateStats: =>
        gu = 0.0
        earlyGu = 0.0
        mcu = 0.0
        gallons = parseFloat($('#batchSize').text())
        boilGallons = parseFloat($('#boilSize').text())
        total_weight = 0.0
        approx_cost = 0.0

        og_element = $('#original_gravity')
        fg_element = $('#final_gravity')
        color_element = $('#recipe_color_value')
        ibu_element = $('#ibu')
        abv_element = $('#abv')

        timeline_map = 
            fermentables:
                mash: []
                steep: []
                boil: []
                boilEnd: []
            times: {}
            drySpice: {}
            yeast: []

        # Update breadcrumb name
        if $('#crumbName').attr('contentEditable')
            $('#crumbName').html($('#recipeName').html())

        # Update size sliders in scale dialog
        $('#gallonsValue').text(gallons);
        $('#boilGallonsValue').text(boilGallons);

        # Are we mashing?
        mashing = @getMashingInfo()

        rows = []
        $('#fermentables_data tr').each((index, element) =>
            [lb, oz, desc, late, ppg, srm, weight, gravity, addition, forced] = @getFermentableInfo(element, gallons, mashing)
            
            # Update color
            srmspan = element.children[6].children[0]
            srmspan.setAttribute('data-srm', srm)
            srmspan.style.backgroundColor = Util.srmToRgb(srm)
            
            total_weight += weight;
            mcu += srm * weight / gallons
            
            # Update approximate cost
            for [regex, cost] in @MALT_PRICES
                if regex.exec(desc)
                    approx_cost += weight * cost
                    break

            if addition is 'boil'
                if not late
                    timeline_map.fermentables.boil.push([lb, oz, desc, gravity])
                else
                    timeline_map.fermentables.boilEnd.push([lb, oz, desc, gravity])
            else if addition is 'steep'
                timeline_map.fermentables.steep.push([lb, oz, desc, gravity])
            else if addition is 'mash'
                timeline_map.fermentables.mash.push([lb, oz, desc, gravity])

            gu += gravity

            if not late
                earlyGu += gravity

            rows.push([weight, element]);
        )
        
        # Update percentages
        for [weight, row] in rows
            row.children[0].innerHTML = Math.round(weight / total_weight * 100)
        
        # Reorder rows based on descending weight percentage
        @reorderRows($('#fermentables_data'), rows)
        
        # Update original gravity
        gu = 1.0 + (gu / 1000.0)
        earlyGu = 1.0 + (earlyGu / 1000.0)
        og_element.html(gu.toFixed(3))
        
        # Update final gravity
        attenuation = 0
        
        # Get yeast attenuation
        rows = []
        $('#yeast_data tr').each((index, element) =>
            desc = $(element.children[0]).text() or ''
            atten = parseInt($(element.children[3]).text()) or 0
            if atten > attenuation
                attenuation = atten

            # Update cost
            for [regex, cost] in @YEAST_PRICES
                if regex.exec(desc)
                    approx_cost += cost
                    break

            timeline_map.yeast.push(desc)

            rows.push([atten, element])
        )
        @reorderRows($('#yeast_data'), rows)
        
        attenuation = 75 if attenuation is 0
        
        fg = gu - ((gu - 1.0) * attenuation / 100.0)
        fg_element.html(fg.toFixed(3))
        
        # Update alcohol percentage by volume
        abv = ((1.05 * (gu - fg)) / fg) / 0.79 * 100.0
        abv_element.html(abv.toFixed(1))
        
        # Update calories
        bottle = 3.55 # 355 ml, aka standard 12oz bottle
        gu_plato = (-463.37) + (668.72 * gu) - (205.35 * (gu * gu))
        fg_plato = (-463.37) + (668.72 * fg) - (205.35 * (fg * fg))
        real_extract = (0.1808 * gu_plato) + (0.8192 * fg_plato)
        abw = 0.79 * abv / fg
        calories = Math.max(0, ((6.9 * abw) + 4.0 * (real_extract - 0.10)) * fg * bottle)
        $('#calories').html(Math.round(calories))
        
        # Update brew color
        color = 1.4922 * Math.pow(mcu, 0.6859)
        color_element.html(Math.round(color))
        $('#recipe_color').attr('data-srm', color)
        $('#recipe_color').css('background-color', Util.srmToRgb(color))
        
        # Update bitterness units
        rows = []
        ibu = 0.0
        $('#hops_data tr').each((index, element) =>
            use = $(element.children[0]).text().toLowerCase() or ''
            time = Util.timeToMin($(element.children[1]).text()) or 0.0
            oz = parseFloat($(element.children[2]).text()) or 0.0
            desc = $(element.children[3]).text() or ''
            form = $(element.children[4]).text() or 'pellet'
            utilization_factor = 1.0
            if form is 'pellet'
                utilization_factor = 1.15
            aa = parseFloat($(element.children[5]).text()) or 0.0

            if aa and use is 'boil'
                bitterness = 1.65 * Math.pow(0.000125, earlyGu - 1.0) * ((1 - Math.pow(2.718, -0.04 * time)) / 4.15) * ((aa / 100.0 * oz * 7490.0) / boilGallons) * utilization_factor
                ibu += bitterness
            else
                bitterness = 0

            # Update cost
            for [regex, cost] in @HOP_PRICES
                if regex.exec(desc)
                    approx_cost += Math.ceil(oz) * cost
                    break

            if @DRY_SPICE.exec use
                if aa
                    desc += ' (dry hop)'

                timeline_map['drySpice'][time] ?= []
                timeline_map['drySpice'][time].push([oz, desc, bitterness])

                rows.push([1000 + time, element])
            else
                timeline_map['times'][time] ?= []
                timeline_map['times'][time].push([oz, desc, bitterness])

                rows.push([200 - time, element])
        )
        @reorderRows($('#hops_data'), rows, (x, y) -> x[0] - y[0])
        
        ibu_element.html(ibu.toFixed(1))
        
        buToGu = (ibu / ((gu - 1.0) * 1000)) or 0.0
        $('#buToGu').html(buToGu.toFixed(2))
        
        # Update priming sugar
        CORN_TO_TABLE = 0.90995
        CORN_TO_HONEY = 1.22496
        CORN_TO_DME = 1.33249
        volumes = parseFloat($('#bottling_pressure').html()) || 2.5
        temp = parseFloat($('#bottling_temp').html()) || 70
        priming_grams = 15.195 * 5 * (volumes - 3.0378 + (0.050062 * temp) - (0.00026555 * temp * temp))
        $('#corn_sugar_grams').html(Math.round(priming_grams))
        $('#table_sugar_grams').html(Math.round(priming_grams * CORN_TO_TABLE))
        $('#honey_grams').html(Math.round(priming_grams * CORN_TO_HONEY))
        $('#dme_grams').html(Math.round(priming_grams * CORN_TO_DME))
        priming_oz = priming_grams / 28.35
        $('#corn_sugar_oz').html(priming_oz.toFixed(2))
        $('#table_sugar_oz').html((priming_oz * CORN_TO_TABLE).toFixed(2))
        $('#honey_oz').html((priming_oz * CORN_TO_HONEY).toFixed(2))
        $('#dme_oz').html((priming_oz * CORN_TO_DME).toFixed(2))
        priming_cups = priming_grams / 200.0
        $('#corn_sugar_tsp').html(Math.round(priming_cups * 48))
        $('#table_sugar_tsp').html(Math.round(priming_cups * 0.88 * 48))
        $('#honey_tsp').html(Math.round(priming_cups * 0.71 * 48))
        $('#dme_tsp').html(Math.round(priming_cups * 1.62 * 48))
        $('#corn_sugar_cups').html(priming_cups.toFixed(2))
        $('#table_sugar_cups').html((priming_cups * 0.88).toFixed(2))
        $('#honey_cups').html((priming_cups * 0.71).toFixed(2))
        $('#dme_cups').html((priming_cups * 1.62).toFixed(2))
        
        bottleCount = Math.round(gallons * 128.0 / 12.0)
        $('#bottle_count').html(bottleCount);

        # Update approximate cost
        $('#total_cost').html(approx_cost.toFixed(2))
        $('#bottle_cost').html(Math.round(approx_cost / bottleCount * 100))

        # Update timeline
        totalTime = 0

        get_items = (fermentables, spices, yeasts) =>
            items = []
            for sugar in fermentables
                item = ''

                if sugar[0]
                    item += sugar[0] + 'lb '

                if sugar[1]
                    item += sugar[1] + 'oz '

                item += sugar[2] + ' (' + Math.round(sugar[3]) + ' <acronym title="Gravity Units">GU</acronym>)'
                items.push(item)

            for spice in spices
                item = spice[0] + 'oz ' + spice[1]

                if spice[2]
                    item += ' (' + spice[2].toFixed(1) + ' <acronym title="International Bitterness Units">IBU</acronym>)'

                items.push(item)

            for yeast in yeasts
                items.push(yeast)

            output = ''
            if items.length > 1
                output = items.reduce((x, y) -> x + ', ' + y)
            else if items.length
                output = items[0]

            return output

        mash = Mash.getFromPage()
        firstTemp = 154
        if mash.steps and mash.steps[0]
            firstTemp = parseFloat mash.steps[0].temperature

        primaryDays = parseInt $('#primaryDays').val()
        primaryTemp = parseFloat $('#primaryTemp').val()
        secondaryDays = parseInt $('#secondaryDays').val()
        secondaryTemp = parseFloat $('#secondaryTemp').val()
        tertiaryDays = parseInt $('#tertiaryDays').val()
        tertiaryTemp = parseFloat $('#tertiaryTemp').val()
        agingDays = parseInt $('#agingDays').val()

        boilName = 'water'
        timeline = '<li><span class="label label-inverse">start</span> Get ready to brew!'

        if timeline_map.fermentables.mash.length
            boilName = 'wort'
            mashWeight = (item[0] + (item[1] / 16) for item in timeline_map.fermentables.mash).reduce((x, y) -> x + y)
            mashGallons = mash.water_ratio / 4.0 * mashWeight
            strikeTemp = (0.2 / 1.5) * (firstTemp - 70) + firstTemp
            timeline += '<li><span class="label label-info">mash</span> Bring ' + mashGallons.toFixed(1) + ' gallons of water to ' + Math.round(strikeTemp) + '&deg;F (~' + Math.round(mashGallons * 5) + ' minutes)<br/>Add '
            timeline += get_items(timeline_map.fermentables.mash, [], []) + '<br/>'

            for step in mash.steps
                timeline += step.name + ' for ' + step.duration + ' minutes at ' + step.temperature + ' &deg;F<br/>'
                totalTime += parseFloat(step.duration)

            if mash.sparge
                timeline += 'Mashout to ' + mash.mashout + '&deg;F and sparge with ' + (mash.sparge / 4.0 * mashWeight).toFixed(1) + ' gallons of water at ' + mash.mashout + '&deg;F'
            else
                timeline += 'Mashout to ' + mash.mashout + '&deg;F'

            totalTime += Math.round(mashGallons * 5) + 15
        
        if timeline_map.fermentables.steep.length
            boilName = 'wort'
            steepWeight = (item[0] + (item[1] / 16) for item in timeline_map.fermentables.steep).reduce((x, y) -> x + y)
            steepGallons = steepWeight
            timeline += '<li><span class="label label-info">steep</span> Bring ' + steepGallons.toFixed(1) + ' gallons of water to 150&deg; - 170&deg;F (~' + Math.round(steepGallons * 5) + ' minutes)<br/>Steep '
            timeline += get_items(timeline_map.fermentables.steep, [], [])
            timeline += ' for 20 minutes, then remove and discard the grains. This liquid is now your wort.'
            totalTime += Math.round(steepGallons * 5) + 20

        timeline += '<li><span class="label label-info">boil</span>'
        if boilName is 'water'
            timeline += 'Bring ' + boilGallons + ' average gallons of ' + boilName + ' to a rolling boil (~'
        else
            timeline += 'Top-up ' + boilName + ' to ' + boilGallons + ' average gallons and bring to a rolling boil (~'

        timeline += Math.round(boilGallons * 10) + ' minutes).</li>'
        totalTime += parseFloat(boilGallons * 10)

        times = (parseInt(key) for own key, value of timeline_map.times)

        # If we have late additions and no late addition time, add it
        if timeline_map.fermentables.boilEnd.length and 5 not in times
            timeline_map.times[5] = []
            times.push(5)

        for time, i in times.sort((x, y) -> y - x)
            if i is 0
                totalTime += time

            timeline += '<li><span class="label label-info">-' + time + ' minutes</span> Add '

            if i is 0 and timeline_map.fermentables.boil.length
                timeline += get_items(timeline_map.fermentables.boil, timeline_map.times[time], [])
            else if time is 5 and timeline_map.fermentables.boilEnd.length
                timeline += get_items(timeline_map.fermentables.boilEnd, timeline_map.times[time], [])
            else
                timeline += get_items([], timeline_map.times[time], [])
            timeline += '</li>'

        # Add cooling time
        totalTime += 30

        timeline += '<li><span class="label label-info">0 minutes</span> Flame out; begin chilling to ' + primaryTemp.toFixed(1) + '&deg;F</li>
            <li><span class="label label-info">30 minutes</span> Chilling complete; top up with water to total ' + gallons + ' gallons; aerate and pitch ' + get_items([], [], timeline_map.yeast) + '</li>
            <li><span class="unknown-time">...</span>&nbsp;</li>'

        for own time, i of timeline_map.drySpice
            timeline += '<li><span class="label label-info">' + Util.minToTime(time) + '</span> Add '
            timeline += get_items([], timeline_map.drySpice[time], [])
            timeline += '</li>'

        if not primaryDays and not secondaryDays and not tertiaryDays
            timeline += '<li><span class="label label-inverse">Drink</span> Drink immediately (about ' + bottleCount + ' bottles)</li>'
        else if tertiaryDays
            timeline += '<li><span class="label label-info">' + primaryDays + ' days</span> Move to secondary fermenter at ' + secondaryTemp + '&deg;F after ' + primaryDays + ' days</li>'
            timeline += '<li><span class="label label-info">' + (primaryDays + secondaryDays) + ' days </span> Move to tertiary fermenter at ' + tertiaryTemp + '&deg;F after ' + secondaryDays + ' days</li>'
            timeline += '<li><span class="label label-info">' + (primaryDays + secondaryDays + tertiaryDays) + ' days </span> Prime and bottle about ' + bottleCount + ' bottles after ' + tertiaryDays + ' days</li>'
        else if secondaryDays
            timeline += '<li><span class="label label-info">' + primaryDays + ' days</span> Move to secondary fermenter at ' + secondaryTemp + '&deg;F after ' + primaryDays + ' days</li>'
            timeline += '<li><span class="label label-info">' + (primaryDays + secondaryDays) + ' days </span> Prime and bottle about ' + bottleCount + ' bottles after ' + secondaryDays + ' days</li>'
        else
            timeline += '<li><span class="label label-info">' + primaryDays + ' days</span> Prime and bottle about ' + bottleCount + ' bottles</li>'

        timeline += '<li><span class="unknown-time">...</span>&nbsp;</li>
            <li><span class="label label-inverse">' + (primaryDays + secondaryDays + tertiaryDays + agingDays) + ' days</span> Relax, don\'t worry, and have a homebrew after ' + agingDays + ' days!</li>'

        $('#timeline ol').html(timeline)

        $('#timeline ol [title]').tooltip({
            delay: {
                show: 500,
                hide: 100
            }
        })

        $('#brewTime').html((totalTime / 60).toFixed(1) + ' hours')

        # Update style matching information
        styleName = $('#styleName').get(0)
        style = BeerStyles.get(styleName.getAttribute('data-category'), styleName.getAttribute('data-style'))
        if style
            # Show the style button
            # Currently this feature is DISABLED, to enable it, uncomment the below line
            $('#stylebtn').show()
            @adjustStyleButton()

            # Force the modal dialog to be shown so we can get dimensions
            styleGuideModal = $('#styleGuideModal')
            display = styleGuideModal.css('display')
            styleGuideModal.css('display', 'block')

            @updateStyleGraph('gu', gu, style.gu, 3)
            @updateStyleGraph('fg', fg, style.fg, 3)
            @updateStyleGraph('srm', color, style.srm, 1)
            @updateStyleGraph('ibu', ibu, style.ibu, 1)
            @updateStyleGraph('abv', abv, style.abv, 1)

            # Reset
            styleGuideModal.css('display', display)

            og_element.attr('data-original-title', style.gu[0].toFixed(3) + ' - ' + style.gu[1].toFixed(3))
            fg_element.attr('data-original-title', style.fg[0].toFixed(3) + ' - ' + style.fg[1].toFixed(3))
            color_element.attr('data-original-title', style.srm[0].toFixed(1) + ' - ' + style.srm[1].toFixed(1))
            ibu_element.attr('data-original-title', style.ibu[0].toFixed(1) + ' - ' + style.ibu[1].toFixed(1))
            abv_element.attr('data-original-title', style.abv[0].toFixed(1) + ' - ' + style.abv[1].toFixed(1))

            if style.gu[0] > gu or gu > style.gu[1]
                og_element.addClass('styleError')
            else
                og_element.removeClass('styleError')

            if style.fg[0] > fg or fg > style.fg[1]
                fg_element.addClass('styleError')
            else
                fg_element.removeClass('styleError')

            if style.srm[0] > color or color > style.srm[1]
                color_element.addClass('styleError')
            else
                color_element.removeClass('styleError')

            if style.ibu[0] > ibu or ibu > style.ibu[1]
                ibu_element.addClass('styleError')
            else
                ibu_element.removeClass('styleError')

            if style.abv[0] > abv or abv > style.abv[1]
                abv_element.addClass('styleError')
            else
                abv_element.removeClass('styleError')
        else
            # Clear all styling info
            og_element.attr('data-original-title', '')
            og_element.removeClass('styleError')

            fg_element.attr('data-original-title', '')
            fg_element.removeClass('styleError')

            color_element.attr('data-original-title', '')
            color_element.removeClass('styleError')

            ibu_element.attr('data-original-title', '')
            ibu_element.removeClass('styleError')

            abv_element.attr('data-original-title', '')
            abv_element.removeClass('styleError')

            # Hide style guide button
            $('#stylebtn').hide()

        # Save recipe to local storage if this is a new recipe being created
        if window.location.pathname is '/new'
            @saveLocal()

    # Update the graph for the given property
    @updateStyleGraph: (property, value, range, places) =>
        # Get the container that holds all the graph's divs
        container = $('#' + property + 'graph')

        # Basic dimensions needed for positioning
        width = container.width()
        height = container.height()

        # Set the text properties immediately so their calculated sizes can be
        # used later
        valText = $('.val', container)
        minText = $('.min', container)
        maxText = $('.max', container)
        valText.html(value.toFixed(places))
        minText.html(range[0].toFixed(places))
        maxText.html(range[1].toFixed(places))

        # The divs that make up the actual graph
        goodline = $('.goodline', container)
        badline = $('.badline', container)
        cap1 = $('.cap1', container)
        cap2 = $('.cap2', container)
        triangle = $('.triangle', container)

        # Edge offsets if triangle is at edge
        triangleOffset = 3;
        endCapTriangleOffset = 8;

        # Triangle dimensions
        triangleWidth = 6
        halfTriangleWidth = 3

        # Force rounding (can't round to a specific decimal, so multiply by
        # 10^places then round)
        places = Math.pow(10, places)
        value = Math.round(value * places)
        min = Math.round(range[0] * places)
        max = Math.round(range[1] * places)

        # Reset CSS for all elements to start with a clean slate
        goodline.css({
                'left': ''
                'right': ''
                'width': ''
            })
        badline.css({
                'left': ''
                'right': ''
                'width': ''
            })
        cap1.css({
                'left': ''
                'right': ''
            })
        cap2.css({
                'left': ''
                'right': ''
            })
        triangle.css({
                'left': ''
                'right': ''
            })
        triangle.removeClass('badtriangle goodtriangle')
        minText.css({
                'top': ''
                'left': ''
            })
        maxText.css({
                'top': ''
                'left': ''
                'right': ''
            })
        valText.css('left', '');

        if min <= value <= max
            # In range
            # Find how far to place the center (min is smallest, max is largest)
            center = (value - min) / (max - min) * width

            # Move the relevant divs around
            goodline.css({
                    'left': 0
                    'right': 0
                })
            cap1.css('left', 0)
            cap2.css('right', 0)
            triangle.css('left', Math.max(0, Math.min(width - triangleWidth, center - halfTriangleWidth)))
            triangle.removeClass('badtriangle').addClass('goodtriangle')

            # Move text to proper locations
            maxText.css('right', 0)
            valText.css('left', Math.max(0, Math.min(width - valText.width(), center - (valText.width() / 2))));

        else if value < min
            # Less than min
            # Find how far to place the center (value is smallest, max is largest)
            percent = (min - value) / (max - value)
            center = percent * (width - triangleOffset) + triangleOffset

            # Make sure the end cap doesn't overlap with the triangle
            center = Math.max(endCapTriangleOffset, Math.round(center))

            # Move the relevant divs around
            badline.css('width', center)
            goodline.css({
                    'left': center
                    'right': 0
                })
            cap1.css('left', center)
            cap2.css('right', 0)
            triangle.removeClass('goodtriangle').addClass('badtriangle')

            # Move text to proper locations
            # If text would overlap, move min to top
            maxText.css('right', 0)
            minLeft = 0
            minWidth = minText.width()
            overlap = maxText.position().left - center
            w2 = minWidth / 2
            if (overlap < 0)
                # Maximum overlap, move min text to top and set right edge
                # to match up with center end cap
                minLeft = center - minWidth + 2
                minText.css('top', valText.position().top)

            else if (overlap < 10)
                # Some overlap, move min text to top and set min text
                # centered on end cap
                minLeft = center - w2
                minText.css('top', valText.position().top)

            else if (overlap - w2 < 10)
                # No overlap, but getting close set right edge of min
                # text to match with center end cap
                minLeft = center - minWidth + 2

            else
                # No overlap, set min text to center on end cap making
                # sure not to cover the triangle
                minLeft = Math.max(center - w2, endCapTriangleOffset - 2)

            # Make sure we don't go over the right edge
            minText.css('left', Math.min(minLeft, width - minWidth))

        else
            # More than max
            # Find how far to place the center (rante[0] is smallest, value is largest)
            percent = (max - min) / (value - min);
            center = percent * (width - triangleOffset)

            # Make sure the end cap doesn't overlap with the triangle
            center = Math.min(width - endCapTriangleOffset, Math.round(center))

            # Move the relevant divs around
            badline.css({
                    'left': center
                    'right': 0
                })
            goodline.css('width', center)
            cap1.css('left', 0)
            cap2.css('left', center)
            triangle.css('right', 0)
            triangle.removeClass('goodtriangle').addClass('badtriangle')

            # Move text to proper locations
            # If text would overlap, move min to top
            minText.css('left', 0)
            valText.css('left', width - valText.width())
            maxLeft = 0
            maxWidth = maxText.width()
            overlap = center - minText.width()
            w2 = maxWidth / 2
            if (overlap < 0)
                # Maximum overlap, move min text to top and set right edge
                # to match up with center end cap
                maxLeft = center - 2
                maxText.css('top', valText.position().top)

            else if (overlap < 10)
                # Some overlap, move min text to top and set min text
                # centered on end cap
                maxLeft = center - w2
                maxText.css('top', valText.position().top)

            else if (overlap - w2 < 10)
                # No overlap, but getting close set right edge of min
                # text to match with center end cap
                maxLeft = center - 2

            else
                # No overlap, set min text to center on end cap making
                # sure not to cover the triangle
                maxLeft = Math.min(center - w2, width - endCapTriangleOffset - maxWidth + 2)

            # Make sure we don't go over the right edge
            maxText.css('left', Math.max(maxLeft, 0))

    # Scale a recipe to a new batch and boil size, trying to keep the gravities
    # and bitterness the same if scaleIngredients is true.
    @scale: (newGallons, newBoilGallons, scaleIngredients) =>
        earlyGu = 0.0

        # Get current sizes
        gallons = parseFloat($('#batchSize').text())
        boilGallons = parseFloat($('#boilSize').text())

        if scaleIngredients
            # Are we mashing?
            mashing = @getMashingInfo()

            $('#fermentables_data tr').each((index, element) =>
                [lb, oz, desc, late, ppg, srm, weight, gravity, addition, forced] = @getFermentableInfo(element, gallons, mashing)
                weight = lb + (oz / 16.0)

                newWeight = weight / gallons * newGallons;
                newLb = Math.floor(newWeight)
                newOz = Math.round((newWeight - newLb) * 16.0)

                if newOz is 16
                    newLb += 1
                    newOz = 0

                if not late
                    earlyGu += gravity
                
                $(element.children[1]).text(newLb)
                $(element.children[2]).text(newOz)
            )

            $('#hops_data tr').each((index, element) =>
                time = parseInt($(element.children[1]).text()) or 0.0
                oz = parseFloat($(element.children[2]).text()) or 0.0
                form = $(element.children[4]).text() or 'pellet'

                utilization_factor = 1.0
                if form is 'pellet'
                    utilization_factor = 1.15

                aa = parseFloat($(element.children[5]).text()) or 0.0

                if (aa && time)
                    # This is a bittering ingredient, so scale using the bitterness formula
                    bitterness = 1.65 * Math.pow(0.000125, earlyGu - 1.0) * ((1 - Math.pow(2.718, -0.04 * time)) / 4.15) * ((aa / 100.0 * oz * 7490.0) / boilGallons) * utilization_factor

                    newOz = Math.round(((bitterness * newBoilGallons) / (1.65 * Math.pow(0.000125, earlyGu - 1.0) * ((1 - Math.pow(2.718, -0.04 * time)) / 4.15) * (aa / 100.0 * 7490.0) * utilization_factor)) * 100) / 100.0
                else
                    # Non-bittering ingredient, scale linearly
                    newOz = Math.round((oz / gallons * newGallons) * 100) / 100.0

                $(element.children[2]).text(newOz)
            )

        # Update sizes on page
        $('#batchSize').text(newGallons)
        $('#boilSize').text(newBoilGallons)

        # Update calculated page info with newly scaled values
        @updateStats()

    # Get a recipe object from the current page. This converts the various HTML tables
    # and other elements into an object suitable for JSON-encoding to be sent to the
    # server for processing, e.g. saving the recipe.
    @getFromPage: =>
        # Setup basic recipe object
        recipe =
            name: $('#recipeName').text()
            description: $('#recipeDescription').text()
            category: $('#styleName').get(0).getAttribute('data-category') or ''
            style: $('#styleName').get(0).getAttribute('data-style')or ''
            batchSize: parseFloat($('#batchSize').text()) or 5.0
            boilSize: parseFloat($('#boilSize').text()) or 5.5
            color: parseInt($('#recipe_color_value').text()) or 1
            ibu: parseFloat($('#ibu').text()) or 0.0
            alcohol: parseFloat($('#abv').text()) or 0.0
            bottlingTemp: parseInt($('#bottling_temp').text()) or 70
            bottlingPressure: parseFloat($('#bottling_pressure').text()) or 2.5
            mashEfficiency: parseInt($('#mashEfficiency').text()) or 75
            steepEfficiency: parseInt($('#steepEfficiency').text()) or 50
            primaryDays: parseInt($('#primaryDays').val()) or 14
            primaryTemp: parseInt($('#primaryTemp').val()) or 68
            secondaryDays: parseInt($('#secondaryDays').val()) or 0
            secondaryTemp: parseInt($('#secondaryTemp').val()) or 32
            tertiaryDays: parseInt($('#tertiaryDays').val()) or 0
            tertiaryTemp: parseInt($('#tertiaryTemp').val()) or 32
            agingDays: parseInt($('#agingDays').val()) or 14
            mash: Mash.getFromPage() or ''
            ingredients:
                fermentables: []
                spices: []
                yeast: []

        # Add fermentables data
        $('#fermentables_data tr').each((index, element) =>
            lb = parseInt($(element.children[1]).text()) or 0
            oz = parseInt($(element.children[2]).text()) or 0

            recipe.ingredients.fermentables.push(
                weight: lb + (oz / 16.0)
                description: $(element.children[3]).text() or ''
                late: $(element.children[4]).text() or ''
                ppg: parseInt($(element.children[5]).text()) or 0
                color: parseInt($(element.children[7]).text()) or 1
            )
        )

        # Add hops data
        $('#hops_data tr').each((index, element) =>
            recipe.ingredients.spices.push(
                use: $(element.children[0]).text() or ''
                time: $(element.children[1]).text() or ''
                oz: parseFloat($(element.children[2]).text()) or 0.0
                description: $(element.children[3]).text() or ''
                form: $(element.children[4]).text() or 'pellet'
                aa: parseFloat($(element.children[5]).text()) or 0.0
            )
        )

        # Add yeast data
        $('#yeast_data tr').each((index, element) =>
            recipe.ingredients.yeast.push(
                description: $(element.children[0]).text() or ''
                type: $(element.children[1]).text() or ''
                form: $(element.children[2]).text() or ''
                attenuation: parseInt($(element.children[3]).text()) or 0.0
            )
        )

        return recipe

    # Save the current recipe to the database, and if successful then redirect
    # to the new recipe URL (if the name changed). If no existing recipe for
    # the current slug can be found then a new one will be created.
    @save: =>
        _gaq.push(['_trackEvent', 'Recipe', 'Save', $('#recipeName').text()])
        # Do an AJAX call to save this recipe
        $.ajax(
            url: location.href
            type: 'post'
            data:
                recipe: JSON.stringify(@getFromPage())
            success: (data, status, xhr) =>
                # TODO: handle errors

                # Delete the new recipe local cache as we have now saved the
                # new recipe successfully.
                if window.location.pathname is '/new'
                    @clearLocal()

                if data.redirect
                    window.location = data.redirect
        )

    # Save the current recipe to local storage so that it can be loaded again
    # later when the user comes back to this page.
    @saveLocal: =>
        localStorage['currentRecipe'] = JSON.stringify(@getFromPage())

    # Clear the current recipe saved in local storage
    @clearLocal: =>
        localStorage.removeItem('currentRecipe')

    # Load a recipe from local storage
    @loadLocal: =>
        # No recipe saved? Just return silently
        return if not localStorage['currentRecipe']

        recipe = JSON.parse(localStorage['currentRecipe'])

        # Load basic recipe information
        $('#recipeName').text(recipe.name)
        $('#recipeDescription').text(recipe.description)

        if recipe.category and recipe.category isnt 'null'
            style = recipe.category + ' - ' + recipe.style
        else
            style = 'No style'

        $('#styleName').attr(
            'data-category': recipe.category
            'data-style': recipe.style
        ).text(style)
        $('#batchSize').text(recipe.batchSize)
        $('#boilSize').text(recipe.boilSize)
        $('#bottling_temp').text(recipe.bottlingTemp)
        $('#bottling_pressure').text(recipe.bottlingPressure)
        $('#mashEfficiency').text(recipe.mashEfficiency)
        $('#steepEfficiency').text(recipe.steepEfficiency)
        $('#primaryDays').val(recipe.primaryDays)
        $('#primaryValue').text(recipe.primaryDays)
        $('#primaryTemp').val(recipe.primaryTemp)
        $('#primaryTempValue').text(recipe.primaryTemp)
        $('#secondaryDays').val(recipe.secondaryDays)
        $('#secondaryValue').text(recipe.secondaryDays)
        $('#secondaryTemp').val(recipe.secondaryTemp)
        $('#secondaryTempValue').text(recipe.secondaryTemp)
        $('#tertiaryDays').val(recipe.tertiaryDays)
        $('#tertiaryValue').text(recipe.tertiaryDays)
        $('#tertiaryTemp').val(recipe.tertiaryTemp)
        $('#tertiaryTempValue').text(recipe.tertiaryTemp)
        $('#agingDays').val(recipe.agingDays)

        # Load fermentables, spices, yeast
        for fermentable in recipe.ingredients.fermentables
            @addFermentableRow(fermentable.weight, fermentable.description, fermentable.late, fermentable.ppg, fermentable.color)

        for spice in recipe.ingredients.spices
            @addHopRow(spice.use, spice.time, spice.oz, spice.description, spice.aa, spice.form)

        for yeast in recipe.ingredients.yeast
            @addYeastRow(yeast.description, yeast.type, yeast.form, yeast.attenuation)

        if recipe.mash
            Mash.load recipe.mash

        @updateStats()

    # Adjust the position of the style button by a half-pixel (if necessary)
    # to make sure the lines are clear
    @adjustStyleButton: =>
        btn = $('#stylebtn')
        svg = $('svg', btn).get(0)

        if svg.getScreenCTM?
            f = ->
                matrix = svg.getScreenCTM()
                btn.css('left', '-=0.5') if Math.floor(matrix.e) < matrix.e
                btn.css('top', '-=0.5') if Math.floor(matrix.f) < matrix.f
            if window.loaded then f() else $(window).load(f)
