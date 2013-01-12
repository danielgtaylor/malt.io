# Malt.io build script

colors = require 'colors'
fs = require 'fs'
os = require 'os'

{spawn} = require 'child_process'
{join} = require 'path'

# Common paths to styles and scripts
STATIC = join process.cwd(), 'static'
STYLES = join STATIC, 'styles'
SCRIPTS = join STATIC, 'scripts'

# Settings
verbose = false

# Commands to run
shell = 'bash'
coffee = 'coffee'
uglifyjs = 'uglifyjs'
lessc = 'lessc'
devserver = ['dev_appserver.py', '--skip_sdk_update_check', '.']

# Command modifications for Windows
if os.platform() in ['win32', 'win64']
    coffee += '.cmd'
    uglifyjs += '.cmd'
    lessc += '.cmd'
    pycco = ['python.exe', 'C:\\Python27\\Scripts\\pycco']
    devserver = ['python.exe', 'C:\\Program Files (x86)\\Google\\google_appengine\\dev_appserver.py', '--skip_sdk_update_check', '.']

# Modify string to give it a method to compare endings
String.prototype.endsWith = (suffix) ->
    @indexOf(suffix, this.length - suffix.length) isnt -1

# Run a command with the given arguments
# If a callback is given, call it when the command completes
# successfully
run = (cmd, args = [], callback = null) ->
    console.log 'Running ' + cmd + ' ' + args?.join ' ' if verbose
    proc = spawn cmd, args,
        cwd = process.cwd()
        env = process.env
    proc.stderr.on 'data', (data) ->
        console.log data.toString()
    proc.stdout.on 'data', (data) ->
        console.log data.toString()
    proc.on 'exit', (code) ->
        callback?() if code is 0

# Modify a file in-place using a regular expression
# Search can either be a string or regular expression
sed = (filename, search, replace) ->
    data = fs.readFileSync filename, 'utf8'
    fs.writeFileSync filename, data.replace(search, replace)

# Options
option '', '--verbose', 'Output extra information'

# Tasks
task 'clean', 'clean generated files', (options) ->
    fs.unlink join(STYLES, 'main.css')
    fs.unlink join(SCRIPTS, 'main.js')
    fs.unlink join(SCRIPTS, 'embed.js')

task 'docs', 'generate documentation', (options) ->
    console.log '[DOCS] Generating documentation...'
    console.log 'TODO!'

task 'server', 'run a development server', (options) ->
    invoke 'watch'
    invoke 'static'

    console.log '[SERVER] Running development server...'.green
    run devserver[0], devserver[1..]

task 'static', 'generate static files (scripts, styles, etc)', (options) ->
    verbose = options.verbose

    if not fs.existsSync 'secrets.py'
        fs.createReadStream('secrets.py.template').pipe fs.createWriteStream('secrets.py')

    console.log '[CSS] Generating static/styles/main.css'.green
    run lessc, ['--yui-compress', join(STYLES , 'main.less'), join(STYLES, 'main.css')]
    
    console.log '[JS] Generating static/scripts/main.js'.green
    run coffee, ['-c', '-b', '-j', join(SCRIPTS, 'main.js'), join(SCRIPTS, 'main')], ->
        run uglifyjs, ['-o', join(SCRIPTS, 'main.js'), join(SCRIPTS, 'main.js')]

    console.log '[JS] Generating static/scripts/embed.js'.green
    run coffee, ['-c', '-b', join(SCRIPTS, 'embed.coffee')], ->
        run uglifyjs, ['-o', join(SCRIPTS, 'embed.js'), join(SCRIPTS, 'embed.js')]

    console.log '[HTML] Updating template cache'.green
    sed join(process.cwd(), 'templates', 'base.html'), /\?v=[0-9]*/ig, '?v=' + Math.round new Date().getTime() / 1000

task 'watch', 'watch for changes and regenerate static files', (options) ->
    console.log '[WATCH] Watching static files'.green
    rebuild = false

    # Check every periodically to see if we need to rebuild
    interval = (seconds, func) -> setInterval func, seconds
    interval 250, ->
        if rebuild
            console.log '[WATCH] Files have changed... rebuilding!'.yellow
            invoke 'static'
            rebuild = false

    # Watch static file paths and mark for rebuild when files change
    for path in [join(STATIC, 'scripts'), join(STATIC, 'scripts', 'main'), join(STATIC, 'styles')]
        if options.verbose
            console.log 'Watching ' + path
        fs.watch path, (event, filename) ->
            if not filename or filename.endsWith('.coffee') or filename.endsWith('.less')
                rebuild = true
