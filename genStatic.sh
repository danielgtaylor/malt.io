#!/bin/bash

# Stylesheets
echo 'Generating static/styles/main.css'
lessc --yui-compress static/styles/main.less >static/styles/main.css

# Scripts
echo 'Generating static/scripts/main.js'
coffee -c -b -p static/scripts/*.coffee | uglifyjs >static/scripts/main.js

# Update query string for caching
echo 'Updating templates/base.html'
sed -i "s/\?v=[0-9]*/\?v=`date +%s`/ig" templates/base.html
