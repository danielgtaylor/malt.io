# Shivs for Internet Explorer
document.getElementsByClassName ?= (className) ->
    (e for e in document.getElementsByTagName('div') when e.className.indexOf(className) isnt -1)

window.addEventListener ?= (eventName, callback) ->
    window.attachEvent('on' + eventName, callback)

# Setup widgets on page load using iframes
window.addEventListener('load', ->
    defaultWidth = 260

    window.maltioBaseUrl ?= 'http://www.malt.io'

    for div in document.getElementsByClassName('maltio-recipe')
        div.innerHTML = '<iframe src="' + window.maltioBaseUrl + '/embed/' + div.getAttribute('data-user') + '/' + div.getAttribute('data-recipe') + '?width=' + (div.getAttribute('data-width') or defaultWidth) + '" width="' + (div.getAttribute('data-width') or defaultWidth) + '" height="154" frameborder="0" scrolling="no"></iframe>'
)