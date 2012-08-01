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
    
    # Initialize the recipe by rendering color swatches on the page and
    # setting up event delegates to handle editing if the recipe is put
    # into edit view.
    @init: =>
        # Setup color swatches
        $('.srm[data-srm]').each((index, element) =>
            element.style.backgroundColor = Util.srmToRgb(element.dataset.srm)
        )
        
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

        # Update the page stats, like color, bitterness, alcohol, etc
        @updateStats()

        # Was the page loaded in edit mode? If so, enable editing!
        if window.location.pathname is '/new' or window.location.hash is '#edit'
            @enableEdit()
    
    # Enable recipe edit mode
    @enableEdit: =>
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
    
    # Add a fermentable row to the fermentables table based on a fermentable
    # template button item.
    @addFermentableRow: (template) =>
        table = $('#fermentables_data')[0]
        row = '<tr><td class="num percent">?</td><td class="num" contentEditable="true">1</td><td class="num" contentEditable="true">0</td><td contentEditable="true">' + template.dataset.description + '</td><td class="num" contentEditable="true">' + template.dataset.ppg + '</td><td class="num"><span class="srm" data-srm="' + template.dataset.srm + '" style="background-color: ' + Util.srmToRgb(template.dataset.srm) + '"></span> </td><td class="num" style="border-left: none;" contentEditable="true">' + template.dataset.srm + '</td><td class="edit-show" style="display: block"><a href="#" class="remove"><i class="icon-remove"></i></a></td></tr>'
        table.innerHTML += row
        $('#fermentables_data tr:last td:nth-child(2)').focus()
        @updateStats()
    
    # Add a hop/spice row to the hops and spices table based on a hop
    # template button item
    @addHopRow: (template) =>
        table = $('#hops_data')[0]
        
        # Try to guess a reasonable time for the next addition
        if parseFloat(template.dataset.aa)
            latest = parseInt($('#hops_data tr:last td:nth-child(2)').html?()) || 90
            next = Recipe.NEXT_HOP_SCHEDULE[latest]
            form = 'pellet'
        else
            next = 5
            form = 'ground'
        
        row = '<tr><td contentEditable="true">boil</td><td class="num" contentEditable="true">' + next + 'min</td><td class="num" contentEditable="true">1.00</td><td contentEditable="true">' + template.dataset.description + '</td><td contentEditable="true">' + form + '</td><td contentEditable="true">' + template.dataset.aa + '</td><td class="edit-show" style="display: block"><a href="#" class="remove"><i class="icon-remove"></i></a></td></tr>'
        table.innerHTML += row
        $('#hops_data tr:last td:nth-child(1)').focus()
        @updateStats()
    
    # Add a yeast/bug row to the yeast and other bugs table based on a yeast
    # template button item
    @addYeastRow: (template) =>
        table = $('#yeast_data')[0]
        row = '<tr><td contentEditable="true">' + template.dataset.description + '</td><td contentEditable="true">' + template.dataset.type + '</td><td contentEditable="true">' + template.dataset.form + '</td><td class="num" contentEditable="true">' + template.dataset.attenuation + '</td><td class="edit-show" style="display: block"><a href="#" class="remove"><i class="icon-remove"></i></a></td></tr>'
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
        mcu = 0.0
        gallons = $('#batchSize').html()
        boilGallons = $('#boilSize').html()
        total_weight = 0.0
        approx_cost = 0.0

        # Update breadcrumb name
        $('#crumbName').html($('#recipeName').html())

        rows = []
        $('#fermentables_data tr').each((index, element) =>
            lb = parseInt(element.children[1].innerHTML) or 0
            oz = parseInt(element.children[2].innerHTML) or 0
            desc = element.children[3].innerHTML
            ppg = parseInt(element.children[4].innerHTML) or 0
            srm = parseInt(element.children[6].innerHTML) or 0
            
            # Update color
            srmspan = element.children[5].children[0]
            srmspan.dataset.srm = srm
            srmspan.style.backgroundColor = Util.srmToRgb(srm)
            
            weight = lb + (oz / 16.0)
            total_weight += weight;
            gu += ppg * weight / gallons
            mcu += srm * weight / gallons
            
            # Update approximate cost
            for [regex, cost] in @MALT_PRICES
                if regex.exec(desc)
                    approx_cost += weight * cost
                    break

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
        $('#original_gravity').html(gu.toFixed(3))
        
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
        )
        
        attenuation = 75 if attenuation is 0
        
        fg = gu - ((gu - 1.0) * attenuation / 100.0)
        $('#final_gravity').html(fg.toFixed(3))
        
        # Update alcohol percentage by volume
        abv = ((1.05 * (gu - fg)) / fg) / 0.79 * 100.0
        $('#abv').html(abv.toFixed(1))
        
        # Update calories
        bottle = 3.55 # 355 ml, aka standard 12oz bottle
        gu_plato = (-463.37) + (668.72 * gu) - (205.35 * (gu * gu))
        fg_plato = (-463.37) + (668.72 * fg) - (205.35 * (fg * fg))
        real_extract = (0.1808 * gu_plato) + (0.8192 * fg_plato)
        abw = 0.79 * abv / fg
        calories = ((6.9 * abv) + 4.0 * (real_extract - 0.10)) * fg * bottle
        $('#calories').html(Math.round(calories))
        
        # Update brew color
        color = 1.4922 * Math.pow(mcu, 0.6859)
        $('#recipe_color_value').html(Math.round(color))
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
            ibu += 1.65 * Math.pow(0.000125, gu - 1.0) * ((1 - Math.pow(2.718, -0.04 * time)) / 4.15) * ((aa / 100.0 * oz * 7490.0) / boilGallons) * utilization_factor

            # Update cost
            for [regex, cost] in @HOP_PRICES
                if regex.exec(desc)
                    approx_cost += Math.ceil(oz) * cost
                    break
        )
        $('#ibu').html(ibu.toFixed(1))
        
        buToGu = ibu / ((gu - 1.0) * 1000)
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

    # Get a recipe object from the current page. This converts the various HTML tables
    # and other elements into an object suitable for JSON-encoding to be sent to the
    # server for processing, e.g. saving the recipe.
    @getFromPage: =>
        # Setup basic recipe object
        recipe =
            name: $('#recipeName').html()
            description: $('#recipeDescription').html()
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
                ppg: parseInt(element.children[4].innerHTML) or 0
                color: parseInt(element.children[6].innerHTML) or 1
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
                    else
                        window.location = data.redirect
        )
