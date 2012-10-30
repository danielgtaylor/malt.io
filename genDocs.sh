#!/bin/bash

pycco *.py
pycco -d docs/handlers handlers/*.py
pycco -d docs/models models/*.py
pycco -d docs/static static/scripts/*.coffee static/scripts/main/*.coffee
