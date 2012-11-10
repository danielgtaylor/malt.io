#!/bin/bash

# Secrets file, create if it doesn't exist
if [ ! -e secrets.py ] ; then
    cp secrets.py.template secrets.py
fi

# Stylesheets
echo 'Generating static/styles/main.css'
lessc --yui-compress static/styles/main.less >static/styles/main.css

# Scripts
echo 'Generating static/scripts/main.js'
coffee -c -b -p static/scripts/main/*.coffee | uglifyjs >static/scripts/main.js

echo 'Generating static/scripts/embed.js'
coffee -c -b -p static/scripts/embed.coffee | uglifyjs >static/scripts/embed.js

# Update query string for caching
echo 'Updating template caching...'
if [[ $OSTYPE != darwin* ]]; then
	sed -i "s/\?v=[0-9]*/\?v=`date +%s`/ig" templates/base.html
else
	sed "s/\?v=[0-9]*/\?v=`date +%s`/g" templates/base.html >templates/base-new.html
	mv templates/base-new.html templates/base.html
fi
