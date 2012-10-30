Util = require('../main/util.coffee').Util

describe "Utility Tests", ->
  it "SRM => RBG Color conversion", ->
    expect(Util.srmToRgb(4.0)).toBe('rgb(230, 147, 53)')
    expect(Util.srmToRgb(12.0)).toBe('rgb(188, 53, 3)')
    expect(Util.srmToRgb(26.0)).toBe('rgb(132, 9, 0)')
