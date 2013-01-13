Malt.io
=======
A free community for brewers. Create, clone and share recipes for beer and mead, log brew days, comment on brews, follow your favorite brewers and more!

Technology
----------
The following technologies are used for Malt.io:

 * [Git](https://help.github.com/)
 * [Google App Engine](https://developers.google.com/appengine/)
 * [Python](http://www.python.org/)
 * [Webapp2](http://webapp-improved.appspot.com/)
 * [Jinja2](http://jinja.pocoo.org/docs/)
 * [HTML5](http://www.html5rocks.com/)
 * [CoffeeScript](http://coffeescript.org)
 * [Less](http://www.lesscss.org/)
 * [Gravatar](http://en.gravatar.com/)
 * [Stripe](https://stripe.com/)
 * [Nose](https://nose.readthedocs.org/en/latest/) and [Jasmine](http://pivotal.github.com/jasmine/)

Getting Started
---------------
You can run a local copy of the site for development. Several prerequisites must be installed and configured first. I **highly** suggest checking out the [Sublime Text 2](http://www.sublimetext.com/2) editor, grabbing the [Sublime Package Control](http://wbond.net/sublime_packages/package_control/installation) add-on and installing the CoffeeScript, LESS, and PEP8 packages.

**On Ubuntu Linux**:

```bash
sudo apt-get install git python-pip nodejs npm

# Get Google AppEngine
wget http://googleappengine.googlecode.com/files/google_appengine_1.7.3.zip
unzip google_appengine_1.7.3.zip

# Modify your path, e.g put the following into your ~/.bashrc:
export PATH=$PATH:/home/<username>/google_appengine

# Get other dependencies
pip install pycco nose NoseGAE nose-exclude
npm install --global coffee-script less uglify-js jasmine-node
npm install colors

# Get Malt.io codebase
git clone https://github.com/danielgtaylor/malt.io.git

# Run the development server
cd malt.io
cake server
```

You should now be able to access the site at [http://localhost:8080/](http://localhost:8080)

**On Windows**:

 * Install [GitHub](http://windows.github.com/)
 	* Set the shell in *tools* -> *options* -> *default shell* to *Git Bash*
 * Install [Python 2.7.x](http://python.org/download/)
 * Install [Python easy_install](http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11.win32-py2.7.exe#md5=57e1e64f6b7c7f1d2eddfc9746bbaf20)
 * Install [Node.js](http://nodejs.org/#download)
 * Install [Google AppEngine](https://developers.google.com/appengine/downloads)
 * Modify your PATH
	1. Right-click on *Computer* in the Start Menu, select *Properties*
	1. Click *Advanced system settings*
	1. Click *Environment variables*
	1. Select *PATH* and click *Edit* in the top half of the window
	1. Ensure your path contains python, python scripts, app engine and npm: `...;C:\Program Files\Google\google_appengine;C:\Python27;C:\Python27\Scripts;C:\Users\<username>\AppData\Roaming\npm\`
 * Click *Clone in Windows* above to clone Malt.io
 * Then run *Git Shell* (or check out [ConEmu](http://code.google.com/p/conemu-maximus5/)) from your start menu and do:

 	```bash
	# Install other dependencies
	easy_install pycco nose NoseGAE nose-exclude
	npm install --global coffee-script less uglify-js jasmine-node
	npm install colors

	# Run the development server
	cd malt.io
	cake server
	```

You should now be able to access the site at [http://localhost:8080/](http://localhost:8080)

Static Files
------------
Malt.io uses CoffeeScript and Less, which are languages built on top of Javascript and CSS, respectively. You should never modify the Javascript or CSS files manually.

In order to see changes to these files in the browser you must first regenerate their compiled Javascript and CSS. A script is provided for this:

```bash
cd malt.io
cake static
```

This script generates a main CSS file, a main Javascript file, and updates query strings so that browser caching isn't an issue. You **must** run this script to see your changes.

To see changes to the Python code or Jinja2 templates, just ensure the development server is running and reload the page in your browser. The development server handles reloading updated files automatically.

Documentation
-------------
You can generate code documentation for both the server-side Python and client-side CoffeeScript:

```bash
cd malt.io
./genDocs.sh
```

You will see a bunch of new HTML files in the `docs` directory. There is one documentation file per file of source code.

Unit Testing
------------
Unit tests are built into the project in the form of doctests and UnitTest subclasses for Python, and Jasmine tests for CoffeeScript. You can run the entire test suite with the following:

```bash
cd malt.io
./runTests.sh
```

This will test all the server-side Python excluding the *contrib* folder, and all the client-side CoffeeScript.

**Unit tests should be run before doing a commit**. This helps to ensure that nothing breaks on the live site. Unit tests **will** be run before any pull request is accepted, so please make sure your changes do not break existing code!

Code Overview
-------------
The following describes the general layout of the code within this project:

 * contrib: third party packages
	* paodate: date handling
	* stripe: payment processing
	* unidecode: unicode transliteration
 * handlers: http request handlers that render pages
 * models: datastore model definitions and methods
 * static: non-dynamic files served by the web server
 	* img: images
	* scripts: client-side coffeescripts and javascripts
	* styles: less and css stylesheets
 * templates: html template files using jinja2
 * app.yaml: google appengine app definition
 * main.py: main script entrypoint
 * settings.py: site settings
 * urls.py: maps regular expressions to handlers
 * util.py: various utility methods

License
-------
Copyright (c) 2013 Daniel G. Taylor

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.