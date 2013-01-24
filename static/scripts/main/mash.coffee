# A class for custom mashing
class Mash
    @init: =>
        $('#singleInfusion154').click (event) =>
            @load
                type: 'singleinfusion'
                water_ratio: 1.25
                steps: [
                    name: 'Starch conversion rest'
                    duration: 60
                    temperature: 154
                ]
                mashout: 170
                sparge: 0.5
            Recipe.updateStats()
            event.preventDefault()

        $('#addSingleInfusionStep').click (event) => 
            event.preventDefault()
            @addSingleInfusionStep()

        $('#singleInfusionSteps').on 'click', '.remove', (event) =>
            event.preventDefault()
            @removeStep event.target.parentNode.parentNode

        $('#mash-button').click =>
            Recipe.updateStats()

    @addSingleInfusionStep: (name="Unnamed rest", duration=60, temperature=154) =>
        html = '<div class="mashStep">
                    <input type="text" value="' + name + '"/>
                    <input type="text" value="' + duration + '" style="width: 30px;"/><span> minutes at </span>
                    <input type="text" value="' + temperature + '" style="width: 30px;"/><span> &deg;F</span>
                    <a class="remove" href="#"><i class="icon-remove"></i></a>
                </div>'
        $('#singleInfusionSteps').append html

    @removeStep: (element) =>
        element.parentNode.removeChild element

    @getFromPage: =>
        mash =
            type: 'singleinfusion'
            water_ratio: parseFloat $('#quartsValue').text()
            steps: []
            mashout: parseFloat $('#mashoutValue').text()
            sparge: parseFloat $('#spargeValue').text()

        $('#singleInfusionSteps .mashStep').each (index, element) =>
            mash.steps.push
                name: $(element.children[0]).val()
                duration: parseFloat $(element.children[1]).val()
                temperature: parseFloat $(element.children[3]).val()

        return mash

    @load: (mash) =>
        $('#quartsValue').text mash.water_ratio
        $('#mashoutValue').text mash.mashout
        $('#spargeValue').text mash.sparge
        $('#singleInfusionSteps').empty()

        for step in mash.steps
            @addSingleInfusionStep step.name, step.duration, step.temperature
