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
    
    # Initialize the recipe by rendering color swatches on the page and
    # setting up event delegates to handle editing if the recipe is put
    # into edit view.
    @init: =>
        # Setup color swatches
        $('.srm[data-srm]').each((index, element) =>
            element.style.backgroundColor = Util.srmToRgb(element.getAttribute('data-srm'))
        )

        # Setup action buttons
        $('#edit-button').click(@enableEdit)
        $('#delete-button').click(@onDelete)
        $('#like-button').click(@onLiked)
        $('#clone-button').click(@onCloned)
        
        # Setup editing delegates
        $('#fermentables_data, #hops_data, #yeast_data, .editable').on('keydown', '[contentEditable]', (event) =>
            @checkUpdateStats(event)
        )
        $('#fermentables_data, #hops_data, #yeast_data, .editable').on('blur', '[contentEditable]', (event) =>
            @updateStats()
        )

        # Setup row removal delegates
        $('#fermentables_data, #hops_data, #yeast_data').on('click', '.remove', (event) =>
            @removeRow(event.target.parentNode)
            return false
        )
        
        # Setup focus delegates
        $('#fermentables_data, #hops_data, #yeast_data, .editable').on('focus', '[contentEditable]', (event) =>
            Util.selectAll(event)
        )

        # Was the page loaded in edit mode? If so, enable editing!
        if window.location.pathname is '/new' or window.location.hash is '#edit'
            @enableEdit()
    
    # Handle clicks on the like button
    @onLiked: (event) =>
        if not user
            window.location.href = '/profile'
            return

        if $('#like-button').hasClass('active')
            action = 'delete'
        else
            action = 'post'

        $.ajax(
            url: location.href + '/like'
            type: action
            success: (data, status, xhr) =>
                # TODO: handle errors here
                $('.likes-tag').html(data.likes + ' likes')
        )

    # Handle clicks on the clone button, creating a cloned copy of another
    # user's recipe
    @onCloned: (event) =>
        if not user
            window.location.href = '/profile'
            return

        $.ajax(
            url: location.href + '/clone'
            type: 'post'
            success: (data, status, xhr) =>
                # TODO: handle errors here
                if data.redirect
                    window.location = data.redirect
        )

    # Enable recipe edit mode
    @enableEdit: =>
        if window.brokenBrowser
            $('#badBrowserModal').modal('show')
            return

        $('#recipeName, #recipeDescription, #batchSize, #boilSize, #bottling_temp, #bottling_pressure').attr('contentEditable', 'true')
        $('#fermentables_data tr td:nth-child(2), #fermentables_data tr td:nth-child(3), #fermentables_data tr td:nth-child(4), #fermentables_data tr td:nth-child(5), #fermentables_data tr td:nth-child(7), #hops_data tr td:nth-child(1), #hops_data tr td:nth-child(2), #hops_data tr td:nth-child(3), #hops_data tr td:nth-child(4), #hops_data tr td:nth-child(5), #hops_data tr td:nth-child(6), #yeast_data tr td:nth-child(1), #yeast_data tr td:nth-child(2), #yeast_data tr td:nth-child(3), #yeast_data tr td:nth-child(4)').attr('contentEditable', 'true')
        $('#saveMsg, .edit-show').show()
        $('.edit-hide').hide()
    
    # Disable recipe edit mode, e.g. after a save
    @disableEdit: =>
        $('#recipeName, #recipeDescription, #batchSize, #boilSize, #bottling_temp, #bottling_pressure').removeAttr('contentEditable')
        $('#fermentables_data tr td:nth-child(2), #fermentables_data tr td:nth-child(3), #fermentables_data tr td:nth-child(4), #fermentables_data tr td:nth-child(5), #fermentables_data tr td:nth-child(7), #hops_data tr td:nth-child(1), #hops_data tr td:nth-child(2), #hops_data tr td:nth-child(3), #hops_data tr td:nth-child(4), #hops_data tr td:nth-child(5), #hops_data tr td:nth-child(6), #yeast_data tr td:nth-child(1), #yeast_data tr td:nth-child(2), #yeast_data tr td:nth-child(3), #yeast_data tr td:nth-child(4)').removeAttr('contentEditable')
        $('#saveMsg, .edit-show').hide()
        $('.edit-hide').show()
    
    # Handle clicks on the delete button, removing a recipe
    @onDelete: (event) =>
        if $(event.target).hasClass('btn-danger')
            $.ajax(
                url: location.href
                type: 'delete'
                success: (data, status, xhr) =>
                    # TODO: handle errors here
                    if data.redirect
                        window.location = data.redirect
            )
        else
            $(event.target).addClass('btn-danger').html('<i class="icon-remove icon-white"></i> Delete?')

    # Add a fermentable row to the fermentables table based on a fermentable
    # template button item.
    @addFermentableRow: (template) =>
        table = $('#fermentables_data')[0]
        row = '<tr><td class="num percent">?</td><td class="num" contentEditable="true">1</td><td class="num" contentEditable="true">0</td><td contentEditable="true">' + template.getAttribute('data-description') + '</td><td contentEditable="true"></td><td class="num" contentEditable="true">' + template.getAttribute('data-ppg') + '</td><td class="num"><span class="srm" data-srm="' + template.getAttribute('data-srm') + '" style="background-color: ' + Util.srmToRgb(template.getAttribute('data-srm')) + '"></span> </td><td class="num" style="border-left: none;" contentEditable="true">' + template.getAttribute('data-srm') + '</td><td class="edit-show" style="display: block"><a href="#" class="remove"><i class="icon-remove"></i></a></td></tr>'
        table.innerHTML += row
        $('#fermentables_data tr:last td:nth-child(2)').focus()
        @updateStats()
    
    # Add a hop/spice row to the hops and spices table based on a hop
    # template button item
    @addHopRow: (template) =>
        table = $('#hops_data')[0]
        
        # Try to guess a reasonable time for the next addition
        if parseFloat(template.getAttribute('data-aa'))
            latest = parseInt($('#hops_data tr:last td:nth-child(2)').html?()) || 90
            next = Recipe.NEXT_HOP_SCHEDULE[latest]
            form = 'pellet'
        else
            next = 5
            form = 'ground'
        
        row = '<tr><td contentEditable="true">boil</td><td class="num" contentEditable="true">' + next + 'min</td><td class="num" contentEditable="true">1.00</td><td contentEditable="true">' + template.getAttribute('data-description') + '</td><td contentEditable="true">' + form + '</td><td class="num" contentEditable="true">' + template.getAttribute('data-aa') + '</td><td class="edit-show" style="display: block"><a href="#" class="remove"><i class="icon-remove"></i></a></td></tr>'
        table.innerHTML += row
        $('#hops_data tr:last td:nth-child(1)').focus()
        @updateStats()
    
    # Add a yeast/bug row to the yeast and other bugs table based on a yeast
    # template button item
    @addYeastRow: (template) =>
        table = $('#yeast_data')[0]
        row = '<tr><td contentEditable="true">' + template.getAttribute('data-description') + '</td><td contentEditable="true">' + template.getAttribute('data-type') + '</td><td contentEditable="true">' + template.getAttribute('data-form') + '</td><td class="num" contentEditable="true">' + template.getAttribute('data-attenuation') + '</td><td class="edit-show" style="display: block"><a href="#" class="remove"><i class="icon-remove"></i></a></td></tr>'
        table.innerHTML += row
        $('#yeast_data tr:last td:nth-child(1)').focus()
        @updateStats()
    
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
    
    # Update the recipe info. This calculates color, alcohol percentage,
    # original and final gravity, bitterness, calories, priming information,
    # and more. This should be called anytime the recipe changes in some way.
    @updateStats: =>
        gu = 0.0
        earlyGu = 0.0
        mcu = 0.0
        gallons = $('#batchSize').html()
        boilGallons = $('#boilSize').html()
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
            yeast: []

        # Update breadcrumb name
        $('#crumbName').html($('#recipeName').html())

        rows = []
        $('#fermentables_data tr').each((index, element) =>
            lb = parseInt(element.children[1].innerHTML) or 0
            oz = parseInt(element.children[2].innerHTML) or 0
            desc = element.children[3].innerHTML
            late = (element.children[4].innerHTML or '') in ['y', 'yes']
            ppg = parseInt(element.children[5].innerHTML) or 0
            srm = parseInt(element.children[7].innerHTML) or 0
            
            # Update color
            srmspan = element.children[6].children[0]
            srmspan.setAttribute('data-srm', srm)
            srmspan.style.backgroundColor = Util.srmToRgb(srm)
            
            weight = lb + (oz / 16.0)
            total_weight += weight;
            gravity = ppg * weight / gallons
            mcu += srm * weight / gallons
            
            # Update approximate cost
            for [regex, cost] in @MALT_PRICES
                if regex.exec(desc)
                    approx_cost += weight * cost
                    break

            if /mash/i.exec(desc)
                addition = 'mash'
            else if /steep/i.exec(desc)
                addition = 'steep'
            else if /boil/i.exec(desc)
                addition = 'boil'
            else if @BOIL_FERMENTABLES.exec(desc)
                addition = 'boil'
            else if @STEEP_FERMENTABLES.exec(desc)
                addition = 'steep'
            else
                addition = 'mash'

            if addition is 'boil'
                if not late
                    timeline_map.fermentables.boil.push([lb, oz, desc, gravity])
                else
                    timeline_map.fermentables.boilEnd.push([lb, oz, desc, gravity])
            else if addition is 'steep'
                # Steeped grains have considerably lower efficiency of 30%
                gravity *= 0.3

                timeline_map.fermentables.steep.push([lb, oz, desc, gravity])
            else if addition is 'mash'
                # Mashed grains have an average efficiency of about 75%
                # TODO: Make this configurable later
                gravity *= 0.75

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
        active = document.activeElement
        rows.sort((x, y) ->
            return y[0] - x[0]
        )
        tbody = $('#fermentables_data')
        for [weight, row] in rows
            tbody.append(row)
            for child in row.children
                if child is active
                    $(child).focus();
        
        # Update original gravity
        gu = 1.0 + (gu / 1000.0)
        earlyGu = 1.0 + (earlyGu / 1000.0)
        og_element.html(gu.toFixed(3))
        
        # Update final gravity
        attenuation = 0
        
        # Get yeast attenuation
        $('#yeast_data tr').each((index, element) =>
            desc = element.children[0].innerHTML or ''
            atten = parseInt(element.children[3].innerHTML) or 0
            if atten > attenuation
                attenuation = atten

            # Update cost
            for [regex, cost] in @YEAST_PRICES
                if regex.exec(desc)
                    approx_cost += cost
                    break

            timeline_map.yeast.push(desc)
        )
        
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
        ibu = 0.0
        $('#hops_data tr').each((index, element) =>
            time = parseInt(element.children[1].innerHTML) or 0.0
            oz = parseFloat(element.children[2].innerHTML) or 0.0
            desc = element.children[3].innerHTML or ''
            form = element.children[4].innerHTML or 'pellet'
            utilization_factor = 1.0
            if form is 'pellet'
                utilization_factor = 1.15
            aa = parseFloat(element.children[5].innerHTML) or 0.0
            bitterness = 1.65 * Math.pow(0.000125, earlyGu - 1.0) * ((1 - Math.pow(2.718, -0.04 * time)) / 4.15) * ((aa / 100.0 * oz * 7490.0) / boilGallons) * utilization_factor
            ibu += bitterness

            # Update cost
            for [regex, cost] in @HOP_PRICES
                if regex.exec(desc)
                    approx_cost += Math.ceil(oz) * cost
                    break

            timeline_map['times'][time] ?= []
            timeline_map['times'][time].push([oz, desc, bitterness])
        )
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

                item += sugar[2] + ' (' + Math.round(sugar[3]) + ' GU)'
                items.push(item)

            for spice in spices
                item = spice[0] + 'oz ' + spice[1]

                if spice[2]
                    item += ' (' + spice[2].toFixed(1) + ' IBU)'

                items.push(item)

            for yeast in yeasts
                items.push(yeast)

            output = ''
            if items.length > 1
                output = items.reduce((x, y) -> x + ', ' + y)
            else if items.length
                output = items[0]

            return output

        timeline = '<li><span class="label label-inverse">start</span> Get ready to brew!'

        if timeline_map.fermentables.mash.length
            timeline += '<li><span class="label label-info">mash</span> Mash '

            mashing = timeline_map.fermentables.mash
            if timeline_map.fermentables.steep.length
                mashing = mashing.concat(timeline_map.fermentables.steep)

            timeline += get_items(mashing, [], [])
            timeline += ' for 60 minutes at 154&deg;F'
            totalTime += 60
        else if timeline_map.fermentables.steep.length
            timeline += '<li><span class="label label-info">steep</span> Steep '
            timeline += get_items(timeline_map.fermentables.steep, [], [])
            timeline += ' for 20 minutes in warm water (less than 150&deg;F)'
            totalTime += 20

        timeline += '<li><span class="label label-info">boil</span> Bring ' + boilGallons + ' average gallons of water to a boil (~' + Math.round(boilGallons * 10) + ' minutes)</li>'
        totalTime += parseFloat(boilGallons * 10)

        times = (parseInt(key) for key, value of timeline_map.times)

        # If we have late additions and no late addition time, add it
        if timeline_map.fermentables.boilEnd.length and 5 not in times
            timeline_map.times[5] = []
            times.push(5)

        for time, i in times.sort((x, y) -> y - x)
            timeline += '<li><span class="label label-info">-' + time + ' minutes</span> Add '

            if i is 0 and timeline_map.fermentables.boil.length
                timeline += get_items(timeline_map.fermentables.boil, timeline_map.times[time], [])
                totalTime += parseInt(time)
            else if time is 5 and timeline_map.fermentables.boilEnd.length
                timeline += get_items(timeline_map.fermentables.boilEnd, timeline_map.times[time], [])
            else
                timeline += get_items([], timeline_map.times[time], [])
            timeline += '</li>'

        # Add cooling time
        totalTime += 30

        timeline += '<li><span class="label label-info">0 minutes</span> Flame out; begin chilling to 100&deg;F</li>
            <li><span class="label label-info">30 minutes</span> Chilling complete; top up with water to total ' + gallons + ' gallons; aerate and pitch ' + get_items([], [], timeline_map.yeast) + '</li>
            <li><span class="unknown-time">...</span>&nbsp;</li>
            <li><span class="label label-info">14 days</span> Prime and bottle about ' + bottleCount + ' bottles</li>
            <li><span class="unknown-time">...</span>&nbsp;</li>
            <li><span class="label label-inverse">28 days</span> Relax, don\'t worry, and have a homebrew!</li>'

        $('#timeline ol').html(timeline)

        $('#brewTime').html((totalTime / 60).toFixed(1) + ' hours')

        # Update style matching information
        styleName = $('#styleName').get(0)
        style = BeerStyles.get(styleName.getAttribute('data-category'), styleName.getAttribute('data-style'))
        if style
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

    # Get a recipe object from the current page. This converts the various HTML tables
    # and other elements into an object suitable for JSON-encoding to be sent to the
    # server for processing, e.g. saving the recipe.
    @getFromPage: =>
        # Setup basic recipe object
        recipe =
            name: $('#recipeName').html()
            description: $('#recipeDescription').html()
            category: $('#styleName').get(0).getAttribute('data-category') or ''
            style: $('#styleName').get(0).getAttribute('data-style')or ''
            batchSize: parseFloat($('#batchSize').html()) or 5.0
            boilSize: parseFloat($('#boilSize').html()) or 5.5
            color: parseInt($('#recipe_color_value').html()) or 1
            ibu: parseFloat($('#ibu').html()) or 0.0
            alcohol: parseFloat($('#abv').html()) or 0.0
            bottlingTemp: parseInt($('#bottling_temp').html()) or 70
            bottlingPressure: parseFloat($('#bottling_pressure').html()) or 2.5
            ingredients:
                fermentables: []
                spices: []
                yeast: []

        # Add fermentables data
        $('#fermentables_data tr').each((index, element) =>
            lb = parseInt(element.children[1].innerHTML) or 0
            oz = parseInt(element.children[2].innerHTML) or 0

            recipe.ingredients.fermentables.push(
                weight: lb + (oz / 16.0)
                description: element.children[3].innerHTML or ''
                late: element.children[4].innerHTML or ''
                ppg: parseInt(element.children[5].innerHTML) or 0
                color: parseInt(element.children[7].innerHTML) or 1
            )
        )

        # Add hops data
        $('#hops_data tr').each((index, element) =>
            recipe.ingredients.spices.push(
                use: element.children[0].innerHTML or ''
                time: element.children[1].innerHTML or ''
                oz: parseFloat(element.children[2].innerHTML) or 0.0
                description: element.children[3].innerHTML or ''
                form: element.children[4].innerHTML or 'pellet'
                aa: parseFloat(element.children[5].innerHTML) or 0.0
            )
        )

        # Add yeast data
        $('#yeast_data tr').each((index, element) =>
            recipe.ingredients.yeast.push(
                description: element.children[0].innerHTML or ''
                type: element.children[1].innerHTML or ''
                form: element.children[2].innerHTML or ''
                attenuation: parseInt(element.children[3].innerHTML) or 0.0
            )
        )

        return recipe

    # Save the current recipe to the database, and if successful then redirect
    # to the new recipe URL (if the name changed). If no existing recipe for
    # the current slug can be found then a new one will be created.
    @save: =>
        # Do an AJAX call to save this recipe
        $.ajax(
            url: location.href
            type: 'post'
            data:
                recipe: JSON.stringify(@getFromPage())
            success: (data, status, xhr) =>
                # TODO: handle errors
                if data.redirect
                    # If the history object exists, then disable editing nad
                    # update the current URL without a page reload, otherwise
                    # just do a normal redirect
                    if window.history
                        @disableEdit()
                        window.history.replaceState(null, null, data.redirect)

                        # Reset comments
                        DISQUS?.reset(
                            reload: true,
                            config: =>
                                this.page.identifier = undefined
                                this.page.url = data.redirect
                        )

                        $('#disqus_thread').show()
                    else
                        window.location = data.redirect
        )
