###!
  Cakefile for Smallimap
  @author Sebastian Helzle (sebastian@helzle.net or @sebobo)

  Usage:

    Recompile coffeescript and sass when files change:
      cake watch
###

pluginName = "backbonejs-test"
{spawn, exec} = require "child_process"
fs = require "fs"

watching =
  sass: true
  coffee: true

src =
  sass: "sass"
  coffee: "coffee"

out =
  css: "css"
  js: "js"

notify = (source, message) ->
  message = message.trim()
  # Default output to console
  console.log "#{source} - #{message}"
  # Check if growlnotify is enabled and use that if available
  exec "type growlnotify >/dev/null 2>&1 && { growlnotify -m \"#{source}: #{message}\"; }"

task 'watch', 'Watch sass, coffee and haml files for changes and recompile from src folders', ->

  if watching.coffee
    notify "Watcher", "Watching #{src.coffee} folder for changes in coffee scripts."

    coffeeProcess = spawn 'coffee', ['--bare', '--output', "#{out.js}", '--watch', '--compile', src.coffee]
    coffeeProcess.stdout.on 'data', (data) ->
      notify "coffeescript", data.toString()


  if watching.sass
    notify "Watcher", "Watching #{src.sass} folder for changes in sass files."

    sassProcess = spawn 'sass', ['--style', 'expanded', '--watch', "#{src.sass}:#{out.css}"]
    sassProcess.stdout.on 'data', (data) ->
      notify "SASS", data.toString()
