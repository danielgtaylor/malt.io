# Utility class for various random methods
class Util
    # Convert an SRM color value to RGB values, returning a string suitable
    # for use as a CSS color, e.g. ```'rgb(210, 180, 40)'```.
    # 
    # This method uses a nonlinear curve to convert values to a close
    # approximation of the RGB values.
    @srmToRgb: (srm) =>
        r = Math.round(Math.min(255, Math.max(0, 255 * Math.pow(0.975, srm))))
        g = Math.round(Math.min(255, Math.max(0, 245 * Math.pow(0.88, srm))))
        b = Math.round(Math.min(255, Math.max(0, 220 * Math.pow(0.7, srm))))
        
        return 'rgb(' + r + ', ' + g + ', ' + b + ')'
    
    # Select all text of the currently selected element.
    @selectAll: (event) =>
        return if not event

        # Create a new range selecting all text
        range = document.createRange()
        range.selectNodeContents(event.target)
        
        # Remove existing ranges, and then add our new one
        selection = window.getSelection()
        selection.removeAllRanges()
        selection.addRange(range)
