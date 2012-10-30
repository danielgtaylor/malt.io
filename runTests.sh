#!/bin/bash

echo "Running CoffeeScript unit tests..."
jasmine-node --coffee static/scripts

echo "Running Python unit tests..."
GAE=`dirname "\`which dev_appserver.py\`"`
nosetests --exclude-dir="contrib" --with-doctest --with-gae --gae-lib-root="$GAE"
