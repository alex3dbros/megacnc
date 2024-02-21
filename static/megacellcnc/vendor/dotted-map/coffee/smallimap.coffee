###!
Smallimap
Copyright (c) 2012 Small Improvements (http://www.small-improvements.com)

Licensed under the MIT (http://www.opensource.org/licenses/mit-license.php) license.

@author Sebastian Helzle (sebastian@small-improvements.com)
@author Tim Taubner (tim@small-improvements.com)
###

(($) ->
  $.si ||= {}
  $.si.smallimap =
    version: '0.2.0'
    defaults:
      dotRadius: 4
      fps: 20
      width: 1000
      height: 500
      showNight: true
      colors:
        lights: ["#fdf6e3", "#fafafa", "#dddddd", "#cccccc", "#bbbbbb"]
        darks: ["#444444", "#666666", "#888888", "#aaaaaa"]
        land:
          day: (smallimap) ->
            smallimap.colors.lights.slice(1).concat(smallimap.colors.darks.slice(1).reverse())
          night: (smallimap) ->
            smallimap.colors.land.day().reverse()

  class Smallimap

    constructor: (@obj, cwidth, cheight, @renderContext, @world, options={}) ->
      $.extend true, @, options

      @dotDiameter = @dotRadius * 2
      @width = cwidth / @dotDiameter
      @height = cheight / @dotDiameter
      @lastX = -1
      @lastY = -1
      @dirtyXs = undefined
      @eventQueue = []
      @lastRefresh = 0
      @mapIcons = []

      @grid = @generateGrid @width, @height

    run: =>
      @refresh()

    refresh: =>
      now = new Date().getTime()
      dt = now - @lastRefresh
      @lastRefresh = now

      # Refresh event queue
      ongoingEvents = []
      for event in @eventQueue when event.refresh dt
        ongoingEvents.push event
      @eventQueue = ongoingEvents

      # Render dirty dots
      unless @dirtyXs
        @dirtyXs = []
        @dirtyXs[x] = true for x in [0..@width - 1]

      for x in [0..@width - 1]
        if @dirtyXs[x]
          @dirtyXs[x] = false
          @render(x,y) for y in [0..@height - 1] when @grid[x][y].dirty

      # Request next animation frame for rendering
      requestAnimationFrame @refresh

    generateGrid: (width, height) =>
      grid = []

      for x in [0..width - 1]
        for y in [0..height - 1]
          grid[x] ||= []
          grid[x][y] = new MapDot(@, x, y, @landinessOf(x, y))

      return grid

    longToX: (longitude) ->
      Math.floor((longitude + 180) * @width / 360 + 0.5) # <- round

    latToY: (latitude) ->
      Math.floor((-latitude + 90) * @height / 180 + 0.5) # <- round

    xToLong: (x) ->
      Math.floor(x * 360 / @width - 180 + 0.5)

    yToLat: (y) ->
      - Math.floor(y * 180 / @height - 90 + 0.5)

    colorFor: (longitude, latitude, landiness) =>
      darkness = landiness * landiness
      now = new Date()
      sunSet = new SunriseSunset(now.getYear(), now.getMonth() + 1, now.getDate(), latitude, longitude)

      landColors = @colors.land.day(@)
      idx = Math.floor(darkness * (landColors.length - 2))
      if sunSet.isDaylight(now.getHours()) or not @showNight# or latitude >= 69
        new Color(landColors[idx])
      else
        new Color(landColors[idx + 1])

    radiusFor: (longitude, latitude, landiness) =>
      now = new Date()
      sunSet = new SunriseSunset(now.getYear(), now.getMonth() + 1, now.getDate(), latitude, longitude)

      # if lat >= 69 the northpole should get it well deserved sunshine
      if sunSet.isDaylight(now.getHours()) or not @showNight# or latitude >= 69
        @dotRadius * Math.max(0.2, landiness) * 0.6
      else
        @dotRadius * Math.max(0.25, landiness) * 0.78

    convertToWorldX: (x) =>
      Math.floor(x * @world.length / @width)

    convertToWorldY: (y) =>
      Math.floor(y * @world[0].length / @height)

    landinessOf: (x, y) =>
      worldXStart = @convertToWorldX x
      worldXEnd = @convertToWorldX(x + 1) - 1
      worldYStart = @convertToWorldY y
      worldYEnd = @convertToWorldY(y + 1) - 1
      totalCount = 0
      existsCount = 0

      for i in [worldXStart..worldXEnd]
        for j in [worldYStart..worldYEnd]
          totalCount += 1
          existsCount += 1 if @world[i] and @world[i][j]

      existsCount / totalCount

    render: (x, y, millis) =>
      dot = @grid[x][y]

      color = dot.target.color or dot.initial.color
      radius = dot.target.radius or dot.initial.radius

      @renderContext.clearRect(x * @dotDiameter, y * @dotDiameter, @dotDiameter, @dotDiameter)
      @renderContext.fillStyle = color.rgbString()
      @renderContext.beginPath()
      @renderContext.arc(x * @dotDiameter + @dotRadius, y * @dotDiameter + @dotRadius, radius, 0, Math.PI * 2, true)
      @renderContext.closePath()
      @renderContext.fill()

      dot.dirty = false
      dot.target = {}

    markDirty: (x, y) =>
      @dirtyXs[x] = true if @dirtyXs
      @grid[x][y].dirty = true

    reset: (x, y) =>
      @markDirty x, y

    triggerOverlay: =>
        y = 0
        push = (x, dt) =>
          dot = @grid[x][0]
          r = dot.initial.radius

          setDots = (r) =>
            for y in [0..@height - 1]
              @grid[x][y].setRadius r

          @eventQueue.push =>
            setDots r + dt
            setTimeout =>
              setDots r
              @eventQueue.push =>
                push((x + 1) % @width, dt)
            , 1000 / @width * 8

        push(0, 0.5) for y in [0..@height - 1]

    enqueueEvent: (event) =>
      event.init()
      @eventQueue.push(event)

    addMapIcon: (title, label, iconMarker, iconUrl, longitude, latitude) =>
      longitude = parseFloat longitude
      latitude = parseFloat latitude

      mapX = @longToX(longitude) * @dotDiameter + @dotRadius
      mapY = @latToY(latitude) * @dotDiameter + @dotRadius

      @mapIcons.push new MapIcon(@obj, title, label, iconMarker, iconUrl, mapX, mapY)

  class Effect

    constructor: (@dot, @duration, options) ->
      @timeElapsed = 0
      @easing = options.easing || easing.linear
      @callback = options.callback

    update: (dt) =>
      @timeElapsed += dt
      @refresh(@easing Math.min(1, @timeElapsed/@duration))
      if @timeElapsed > @duration
        @callback?()
        false
      else
        true

    refresh: (progress) =>
      "unimplemented"

  class RadiusEffect extends Effect
    constructor: (dot, duration, options) ->
      super dot, duration, options
      @startRadius = options.startRadius
      @endRadius = options.endRadius

    refresh: (progress) =>
      @dot.setRadius @endRadius * progress + @startRadius * (1 - progress)

  class ColorEffect extends Effect
    constructor: (dot, duration, options) ->
      super dot, duration, options
      @startColor = options.startColor
      @endColor = options.endColor

    refresh: (progress) =>
      start = new Color(@startColor.rgbString())
      @dot.setColor start.mix(@endColor, progress)

  class DelayEffect extends Effect
    constructor: (dot, duration, options) ->
      super dot, duration, options

    refresh: (progress) =>
      "nothing to do"

  class Event
    constructor: (@smallimap, options) ->
      @callback = options.callback
      @queue = []

    enqueue: (effect) =>
      @queue.push effect

    init: () =>
      "no init, dude"

    refresh: (dt) =>
      currentEffects = @queue.splice(0)
      @queue = []
      for effect in currentEffects
        if effect.update dt
          @queue.push effect
      @queue.length > 0

  class GeoEvent extends Event
    constructor: (smallimap, options) ->
      super smallimap, options
      @latitude = parseFloat options.latitude
      @longitude = parseFloat options.longitude
      @x = @smallimap.longToX @longitude
      @y = @smallimap.latToY @latitude

  class GeoAreaEvent extends GeoEvent
    constructor: (smallimap, options) ->
      super smallimap, options
      @eventRadius = options.eventRadius || 8

    init: () =>
      for i in [-@eventRadius..@eventRadius]
        for j in [-@eventRadius..@eventRadius]
          nx = @x + i
          ny = @y + j
          d = Math.sqrt(i * i + j * j)
          if d < @eventRadius + 0.5 and @smallimap.grid[nx] and @smallimap.grid[nx][ny]
            dot = @smallimap.grid[nx][ny]
            @initEventsForDot nx, ny, d, dot

  class BlipEvent extends GeoAreaEvent
    constructor: (smallimap, options) ->
      super smallimap, options
      @color = new Color(options.color or "#336699")
      @duration = options.duration or 2048
      @weight = options.weight or 0.5

    initEventsForDot: (nx, ny, d, dot) =>
      ratio = Math.sqrt(d / @eventRadius * @weight)
      delay = @duration / 9 * ratio

      fadeInDuration = @duration / 9 * (1 - ratio)
      fadeOutDuration = @duration * 8 / 9 * (1 - ratio)

      startColor = dot.initial.color
      endColor = new Color(@color.rgbString()).mix(startColor, ratio*ratio)

      startRadius = dot.initial.radius
      if(startRadius >= @smallimap.dotRadius * 0.5)
        endRadius = startRadius - startRadius * 0.5 * (1 - ratio)
      else
        endRadius = (@smallimap.dotRadius - startRadius) * (1 - ratio) + startRadius

      if fadeInDuration > 0
        @enqueue new DelayEffect(dot, delay,
          callback: =>
            @enqueue new ColorEffect(dot, fadeInDuration,
              startColor: startColor
              endColor: endColor
              easing: easing.quadratic
              callback: =>
                @enqueue new ColorEffect(dot, fadeOutDuration,
                  startColor: endColor
                  endColor: startColor
                  easing: Math.sqrt
                )
            )
            @enqueue new RadiusEffect(dot, fadeInDuration,
              startRadius: startRadius
              endRadius: endRadius
              easing: easing.linear
              callback: =>
                @enqueue new RadiusEffect(dot, fadeOutDuration,
                  startRadius: endRadius
                  endRadius: startRadius
                  easing: Math.quadratic
                )
            )
        )

  class LensEvent extends GeoEvent
    constructor: (smallimap, options) ->
      super smallimap, options
      @delay = options.delay or 0
      @duration = options.duration or 1024
      @weight = options.weight || 1
      @isOut = options.fade == "out"

    init: () =>
      dot = @smallimap.grid[@x][@y]
      duration = @duration
      startRadius = dot.initial.radius
      endRadius = (@smallimap.dotRadius - startRadius)*@weight + startRadius
      if @isOut # swap the radius
        startRadius = endRadius
        endRadius = dot.initial.radius
      @enqueue new DelayEffect(dot, @delay,
        callback: =>
          @enqueue new RadiusEffect(dot, @duration,
            startRadius: startRadius
            endRadius: endRadius
            easing: easing.quadratic
          )
      )

  class MapDot
    constructor: (@smallimap, @x, @y, @landiness) ->
      @target = {}
      @dirty = true
      @initial =
        color: new Color("#333")
        radius: @smallimap.radiusFor @smallimap.xToLong(@x), @smallimap.yToLat(@y), @landiness

    setRadius: (radius) =>
      if @target.radius
        @target.radius = (@target.radius + radius) / 2
      else
        @target.radius = radius

      @smallimap.markDirty @x, @y

    setColor: (color) =>
      if @target.color
        @target.color = @target.color.mix color
      else
        @target.color = color

      @smallimap.markDirty @x, @y

  class MapIcon
    constructor: (@mapContainer, @title, @label, @iconMarker, @iconUrl, @x, @y) ->
      @init()

    init: =>
      iconHtml = """
        <div class=\"smallipop smallimap-mapicon\">
          <img src=\"#{@iconMarker}\" alt=\"#{@title}\"/>
          <div class=\"smallipopHint\"></div>
        </div>
      """
      @iconObj = $ iconHtml

      hintContent = @iconObj.children '.smallipopHint'
      if @iconUrl
        hintContent.append "<img class=\"smallimap-icon\" src=\"#{@iconUrl}\"/>"
      if @label
        hintContent.append "<p class=\"smallimap-icon-label\">#{@label}</p>"
      if @title
        hintContent.append "<span class=\"smallimap-icon-title\">#{@title}</span>"

      @iconObjImage = @iconObj.children 'img'
      @iconObjImage.load =>
        @width = @iconObjImage[0].width or 24
        @height = @iconObjImage[0].height or 24

        @iconObjImage.css
          width: '100%'
          height: '100%'

        # Get icon size
        if @iconUrl
          hintContent.children('.smallimap-icon').load ->
            hintIcon = $ @
            hintIcon.attr
              width: hintIcon[0].width
              height: hintIcon[0].height

        @iconObj.css
          position: 'absolute'
          left: @x - @width / 2
          top: @y - @height
          width: @width
          height: @height

        @mapContainer.append @iconObj
        @iconObj.smallipop
          theme: 'blue'
          hideTrigger: true
          popupDistance: 10
          popupYOffset: 10
          popupAnimationSpeed: 200

    remove: =>
      @iconObj.remove()

  easing =
    linear: (progress) ->
      progress
    quadratic: (progress) ->
      progress*progress
    cubic: (progress) ->
      progress*progress*progress
    inverse: (easingFunction) ->
      (progress) ->
        1 - easingFunction(1 - progress)

  $.si.smallimap.effects =
    Effect: Effect
    ColorEffect: ColorEffect
    RadiusEffect: RadiusEffect

  $.si.smallimap.events =
    Event: Event
    BlipEvent: BlipEvent
    LensEvent: LensEvent

  $.si.smallimap.easing = easing

  $.fn.smallimap = (options={}) ->
    options = $.extend true, {}, $.si.smallimap.defaults, options

    return @.each ->
      # Initialize each trigger, create id and bind events
      self = $(@).css
        position: 'relative'

      canvasObj = $ '<canvas>'
      canvasObj.attr
        width: options.width
        height: options.height

      # Append canvas to dom
      self.append canvasObj

      # Get render context from canvas
      canvas = canvasObj.get 0
      ctx = canvas.getContext '2d'
      smallimap = new Smallimap(self, canvas.width, canvas.height, ctx, smallimapWorld, options)

      self.data 'api', smallimap

)(jQuery)
