class BeerStyles
    @init: =>
        html = '<ul class="unstyled"><li><a href="#" data-dismiss="modal">No style</a></li></ul>'

        for own category, styles of BeerStyles.categories
            html += '<h6>' + category + '</h6>'
            html += '<ul class="unstyled">'

            for own name, style of styles
                html += '<li><a href="#" data-dismiss="modal" data-category="' + category + '" data-style="' + name + '">' + name + '</a></li>'

            html += '</ul>'

        $('#styleList').html(html)

        $('#styleModal').on('click', 'li > a', (event) =>
            target = event.currentTarget
            category = target.getAttribute('data-category')
            style = target.getAttribute('data-style')
            styleName = $('#styleName').get(0)

            if category and style
                styleName.innerHTML = category + ' - ' + style
            else
                styleName.innerHTML = 'No style'

            styleName.setAttribute('data-category', category)
            styleName.setAttribute('data-style', style)
            Recipe.updateStats()
        )

    @get: (category, style) =>
        styleData = null

        if @categories.hasOwnProperty(category) and @categories[category].hasOwnProperty(style)
            styleData = @categories[category][style]

        return styleData

    @categories:
        'Light Lager':
            'Lite American Lager':
                gu: [1.028, 1.040]
                fg: [0.998, 1.008]
                srm: [2, 3]
                ibu: [8, 12]
                abv: [2.8, 4.2]
            'Standard American Lager':
                gu: [1.040, 1.050]
                fg: [1.004, 1.010]
                srm: [2, 4]
                ibu: [8, 15]
                abv: [4.2, 5.3]
            'Premium American Lager':
                gu: [1.046, 1.056]
                fg: [1.008, 1.012]
                srm: [2, 6]
                ibu: [15, 25]
                abv: [4.6, 6]
            'Munich Helles':
                gu: [1.045, 1.051]
                fg: [1.008, 1.012]
                srm: [3, 5]
                ibu: [16, 22]
                abv: [4.7, 5.4]
            'Dortmunder Export':
                gu: [1.048, 1.056]
                fg: [1.010, 1.015]
                srm: [4, 6]
                ibu: [23, 30]
                abv: [4.8, 6]
        'Pilsner':
            'German Pilsner (Pils)':
                gu: [1.044, 1.050]
                fg: [1.008, 1.013]
                srm: [2, 5]
                ibu: [25, 45]
                abv: [4.4, 5.2]
            'Bohemian Pilsener':
                gu: [1.044, 1.056]
                fg: [1.013, 1.017]
                srm: [3.5, 6]
                ibu: [35, 45]
                abv: [4.2, 5.4]
            'Classic American Pilsner':
                gu: [1.044, 1.050]
                fg: [1.010, 1.015]
                srm: [3, 6]
                ibu: [25, 40]
                abv: [4.5, 6]
        'European Amber Lager':
            'Vienna Lager':
                gu: [1.046, 1.052]
                fg: [1.010, 1.014]
                srm: [10, 16]
                ibu: [18, 30]
                abv: [4.5, 5.5]
            'Oktoberfest':
                gu: [1.050, 1.057]
                fg: [1.012, 1.016]
                srm: [7, 14]
                ibu: [20, 28]
                abv: [4.8, 5.7]
        'Dark Lager':
            'Dark American Lager':
                gu: [1.044, 1.056]
                fg: [1.008, 1.012]
                srm: [14, 22]
                ibu: [8, 20]
                abv: [4.2, 6]
            'Munich Dunkel':
                gu: [1.048, 1.056]
                fg: [1.010, 1.016]
                srm: [14, 28]
                ibu: [18, 28]
                abv: [4.5, 5.6]
            'Schwarzbier':
                gu: [1.046, 1.052]
                fg: [1.010, 1.016]
                srm: [17, 30]
                ibu: [22, 32]
                abv: [4.4, 5.4]
        'Bock':
            'Maibock / Helles Bock':
                gu: [1.064, 1.072]
                fg: [1.011, 1.018]
                srm: [6, 11]
                ibu: [23, 35]
                abv: [6.3, 7.4]
            'Traditional Bock':
                gu: [1.064, 1.072]
                fg: [1.013, 1.019]
                srm: [14, 22]
                ibu: [20, 27]
                abv: [6.3, 7.2]
            'Doppelbock':
                gu: [1.072, 1.112]
                fg: [1.016, 1.024]
                srm: [6, 25]
                ibu: [16, 26]
                abv: [7, 10]
            'Eisbock':
                gu: [1.078, 1.120]
                fg: [1.020, 1.035]
                srm: [18, 30]
                ibu: [25, 35]
                abv: [9, 14]
        'Light Hybrid Beer':
            'Cream Ale':
                gu: [1.042, 1.055]
                fg: [1.006, 1.012]
                srm: [2.5, 5]
                ibu: [15, 20]
                abv: [4.2, 5.6]
            'Blonde Ale':
                gu: [1.038, 1.054]
                fg: [1.008, 1.013]
                srm: [3, 6]
                ibu: [15, 28]
                abv: [3.8, 5.5]
            'Kölsch':
                gu: [1.044, 1.050]
                fg: [1.007, 1.011]
                srm: [3.5, 5]
                ibu: [20, 30]
                abv: [4.4, 5.2]
            'American Wheat or Rye Beer':
                gu: [1.040, 1.055]
                fg: [1.008, 1.013]
                srm: [3, 6]
                ibu: [15, 30]
                abv: [4, 5.5]
        'Amber Hybrid Beer':
            'Northern German Altbier':
                gu: [1.046, 1.054]
                fg: [1.010, 1.015]
                srm: [13, 19]
                ibu: [25, 40]
                abv: [4.5, 5.2]
            'California Common Beer':
                gu: [1.048, 1.054]
                fg: [1.011, 1.014]
                srm: [10, 14]
                ibu: [30, 45]
                abv: [4.5, 5.5]
            'Düsseldorf Altbier':
                gu: [1.046, 1.054]
                fg: [1.010, 1.015]
                srm: [11, 17]
                ibu: [35, 50]
                abv: [4.5, 5.2]
        'English Pale Ale':
            'Standard / Ordinary Bitter':
                gu: [1.032, 1.040]
                fg: [1.007, 1.011]
                srm: [4, 14]
                ibu: [25, 35]
                abv: [3.2, 3.8]
            'Special / Best / Premium Bitter':
                gu: [1.040, 1.048]
                fg: [1.008, 1.012]
                srm: [5, 16]
                ibu: [25, 40]
                abv: [3.8, 4.6]
            'Extra Special / Strong Bitter':
                gu: [1.048, 1.060]
                fg: [1.010, 1.016]
                srm: [6, 18]
                ibu: [30, 50]
                abv: [4.6, 6.2]
        'Scottish and Irish Ale':
            'Scottish Light 60/-':
                gu: [1.030, 1.035]
                fg: [1.010, 1.013]
                srm: [9, 17]
                ibu: [10, 20]
                abv: [2.5, 3.2]
            'Scottish Heavy 70/-':
                gu: [1.035, 1.040]
                fg: [1.010, 1.015]
                srm: [9, 17]
                ibu: [10, 25]
                abv: [3.2, 3.9]
            'Scottish Export 80/-':
                gu: [1.040, 1.054]
                fg: [1.010, 1.016]
                srm: [9, 17]
                ibu: [15, 30]
                abv: [3.9, 5.0]
            'Irish Red Ale':
                gu: [1.044, 1.050]
                fg: [1.010, 1.014]
                srm: [9, 18]
                ibu: [17, 28]
                abv: [4, 6]
            'Strong Scotch Ale':
                gu: [1.070, 1.130]
                fg: [1.018, 1.056]
                srm: [14, 25]
                ibu: [17, 35]
                abv: [6.5, 10]
        'American Ale':
            'American Pale Ale':
                gu: [1.045, 1.060]
                fg: [1.010, 1.015]
                srm: [5, 14]
                ibu: [30, 45]
                abv: [4.5, 6.2]
            'American Amber Ale':
                gu: [1.045, 1.060]
                fg: [1.010, 1.015]
                srm: [10, 17]
                ibu: [25, 40]
                abv: [4.5, 6.2]
            'American Brown Ale':
                gu: [1.045, 1.060]
                fg: [1.010, 1.016]
                srm: [18, 35]
                ibu: [20, 40]
                abv: [4.3, 6.2]
        'English Brown Ale':
            'Mild':
                gu: [1.030, 1.038]
                fg: [1.008, 1.013]
                srm: [12, 25]
                ibu: [10, 25]
                abv: [2.8, 4.5]
            'Southern English Brown':
                gu: [1.033, 1.042]
                fg: [1.011, 1.014]
                srm: [19, 35]
                ibu: [12, 20]
                abv: [2.8, 4.1]
            'Northern English Brown':
                gu: [1.040, 1.052]
                fg: [1.008, 1.013]
                srm: [12, 22]
                ibu: [20, 30]
                abv: [4.2, 5.4]
        'Porter':
            'Brown Porter':
                gu: [1.040, 1.052]
                fg: [1.008, 1.014]
                srm: [20, 30]
                ibu: [18, 35]
                abv: [4, 5.4]
            'Robust Porter':
                gu: [1.048, 1.065]
                fg: [1.012, 1.016]
                srm: [22, 35]
                ibu: [25, 50]
                abv: [4.8, 6.5]
            'Baltic Porter':
                gu: [1.060, 1.090]
                fg: [1.016, 1.024]
                srm: [17, 30]
                ibu: [20, 40]
                abv: [5.5, 9.5]
        'Stout':
            'Dry Stout':
                gu: [1.036, 1.050]
                fg: [1.007, 1.011]
                srm: [25, 40]
                ibu: [30, 45]
                abv: [4, 5]
            'Sweet Stout':
                gu: [1.044, 1.060]
                fg: [1.012, 1.024]
                srm: [30, 40]
                ibu: [20, 40]
                abv: [4, 6]
            'Oatmeal Stout':
                gu: [1.048, 1.065]
                fg: [1.010, 1.018]
                srm: [22, 40]
                ibu: [25, 40]
                abv: [4.2, 5.9]
            'Foreign Extra Stout':
                gu: [1.056, 1.075]
                fg: [1.010, 1.018]
                srm: [30, 40]
                ibu: [30, 70]
                abv: [5.5, 8]
            'American Stout':
                gu: [1.050, 1.075]
                fg: [1.010, 1.022]
                srm: [30, 40]
                ibu: [35, 75]
                abv: [5, 7]
            'Russian Imperial Stout':
                gu: [1.075, 1.115]
                fg: [1.018, 1.030]
                srm: [30, 40]
                ibu: [50, 90]
                abv: [8, 12]
        'India Pale Ale':
            'English IPA':
                gu: [1.050, 1.075]
                fg: [1.010, 1.018]
                srm: [8, 14]
                ibu: [40, 60]
                abv: [5, 7.5]
            'American IPA':
                gu: [1.056, 1.075]
                fg: [1.010, 1.018]
                srm: [6, 15]
                ibu: [40, 70]
                abv: [5.5, 7.5]
            'Imperial IPA':
                gu: [1.070, 1.090]
                fg: [1.010, 1.020]
                srm: [8, 15]
                ibu: [60, 120]
                abv: [7.5, 10]
        'German Wheat and Rye Beer':
            'Weizen / Weissbier':
                gu: [1.044, 1.052]
                fg: [1.010, 1.014]
                srm: [2, 8]
                ibu: [8, 15]
                abv: [4.3, 5.6]
            'Dunkelweizen':
                gu: [1.044, 1.056]
                fg: [1.010, 1.014]
                srm: [14, 23]
                ibu: [10, 18]
                abv: [4.3, 5.6]
            'Weizenbock':
                gu: [1.064, 1.090]
                fg: [1.015, 1.022]
                srm: [12, 25]
                ibu: [15, 30]
                abv: [6.5, 8]
            'Roggenbier (German Rye Beer)':
                gu: [1.046, 1.056]
                fg: [1.010, 1.014]
                srm: [14, 19]
                ibu: [10, 20]
                abv: [4.5, 6]
        'Belgian and French Ale':
            'Witbier':
                gu: [1.044, 1.052]
                fg: [1.008, 1.012]
                srm: [2, 4]
                ibu: [10, 20]
                abv: [4.5, 5.5]
            'Belgian Pale Ale':
                gu: [1.048, 1.054]
                fg: [1.010, 1.014]
                srm: [8, 14]
                ibu: [20, 30]
                abv: [4.8, 5.5]
            'Saison':
                gu: [1.048, 1.065]
                fg: [1.002, 1.012]
                srm: [5, 14]
                ibu: [20, 35]
                abv: [5, 7]
            'Bière de Garde':
                gu: [1.060, 1.080]
                fg: [1.008, 1.016]
                srm: [6, 19]
                ibu: [18, 28]
                abv: [6, 8.5]
            'Belgian Specialty Ale':
                gu: [1.000, 1.120]
                fg: [1.000, 1.060]
                srm: [2, 40]
                ibu: [0, 120]
                abv: [0, 14]
        'Sour Ale':
            'Berliner Weisse':
                gu: [1.028, 1.032]
                fg: [1.003, 1.006]
                srm: [2, 3]
                ibu: [3, 8]
                abv: [2.8, 3.8]
            'Flanders Red Ale':
                gu: [1.048, 1.057]
                fg: [1.002, 1.012]
                srm: [10, 16]
                ibu: [10, 25]
                abv: [4.6, 6.5]
            'Flanders Brown Ale / Oud Bruin':
                gu: [1.040, 1.074]
                fg: [1.008, 1.012]
                srm: [15, 22]
                ibu: [20, 25]
                abv: [4, 8]
            'Straight (Unblended) Lambic':
                gu: [1.040, 1.054]
                fg: [1.001, 1.010]
                srm: [3, 7]
                ibu: [0, 10]
                abv: [5, 6.5]
            'Gueuze':
                gu: [1.040, 1.060]
                fg: [1.000, 1.006]
                srm: [3, 7]
                ibu: [0, 10]
                abv: [5, 8]
            'Fruit Lambic':
                gu: [1.040, 1.060]
                fg: [1.000, 1.010]
                srm: [3, 7]
                ibu: [0, 10]
                abv: [5, 7]
        'Belgian Strong Ale':
            'Belgian Blond Ale':
                gu: [1.062, 1.075]
                fg: [1.008, 1.018]
                srm: [4, 7]
                ibu: [15, 30]
                abv: [6, 7.5]
            'Belgian Dubbel':
                gu: [1.062, 1.075]
                fg: [1.008, 1.018]
                srm: [10, 17]
                ibu: [15, 25]
                abv: [6, 7.6]
            'Belgian Tripel':
                gu: [1.075, 1.085]
                fg: [1.008, 1.014]
                srm: [4.5, 7]
                ibu: [20, 40]
                abv: [7.5, 9.5]
            'Belgian Golden Strong Ale':
                gu: [1.070, 1.095]
                fg: [1.005, 1.016]
                srm: [3, 6]
                ibu: [22, 35]
                abv: [7.5, 10.5]
            'Belgian Dark Strong Ale':
                gu: [1.075, 1.110]
                fg: [1.010, 1.024]
                srm: [12, 22]
                ibu: [20, 35]
                abv: [8, 11]
        'Strong Ale':
            'Old Ale':
                gu: [1.060, 1.090]
                fg: [1.015, 1.022]
                srm: [10, 22]
                ibu: [30, 60]
                abv: [6, 9]
            'English Barleywine':
                gu: [1.080, 1.120]
                fg: [1.018, 1.030]
                srm: [8, 22]
                ibu: [35, 70]
                abv: [8, 12]
            'American Barleywine':
                gu: [1.080, 1.120]
                fg: [1.016, 1.030]
                srm: [10, 19]
                ibu: [50, 120]
                abv: [8, 12]
        'Fruit Beer':
            'Fruit Beer':
                gu: [1.000, 1.120]
                fg: [1.000, 1.160]
                srm: [1, 40]
                ibu: [0, 120]
                abv: [0, 14]
        'Spice / Herb / Vegetable Beer':
            'Spice, Herb, or Vegetable Beer':
                gu: [1.000, 1.120]
                fg: [1.000, 1.160]
                srm: [1, 40]
                ibu: [0, 120]
                abv: [0, 14]
            'Christmas / Winter Specialty Spiced Beer':
                gu: [1.000, 1.120]
                fg: [1.000, 1.160]
                srm: [8, 40]
                ibu: [0, 120]
                abv: [6, 14]
        'Smoke-Flavored and Wood-Aged Beer':
            'Classic Rauchbier':
                gu: [1.050, 1.056]
                fg: [1.012, 1.016]
                srm: [14, 22]
                ibu: [20, 30]
                abv: [4.8, 6]
            'Other Smoked Beer':
                gu: [1.000, 1.120]
                fg: [1.000, 1.160]
                srm: [1, 40]
                ibu: [0, 120]
                abv: [0, 14]
            'Wood-Aged Beer':
                gu: [1.000, 1.120]
                fg: [1.000, 1.160]
                srm: [1, 40]
                ibu: [0, 120]
                abv: [0, 14]
        'Specialty Beer':
            'Specialty Beer':
                gu: [1.000, 1.120]
                fg: [1.000, 1.160]
                srm: [1, 40]
                ibu: [0, 120]
                abv: [0, 14]
