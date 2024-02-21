
(($) ->
  debugMode = true
  testIntervalId = -1
  markerPath = 'images/marker.png'
  siLogoPath = 'images/si.png'
  myLogoPath = 'images/sh-it.png'
  mapOptions =
    dotRadius: 3
    width: 920
    height: 460
    colors:
      lights: ["#fdf6e3", "#fafafa", "#dddddd", "#cccccc", "#bbbbbb"]
      darks: ["#777777", "#888888", "#999999", "#aaaaaa"]

  log = (message) ->
    window.console?.log message if debugMode

  # Query clients from the server and show them on the map
  getClientsForMap = ->
    smallimap.addMapIcon('Sebastian Helzle IT-Consulting, Karlsruhe', 'Hey, this is where I live!', markerPath, myLogoPath, 8.38, 49)
    smallimap.addMapIcon('Small Improvements, Berlin', 'Easy performance review software online.', markerPath, siLogoPath, 13.40185, 52.52564)
    smallimap.addMapIcon('Sample Company, Rio', 'Somewhere in brazil', markerPath, siLogoPath, -43.173, -22.925)

  # Test function for the map which creates random events all over the world
  window.runSmallimapTest = ->
    testIntervalId = setInterval ->
        event = new $.si.smallimap.events.BlipEvent smallimap,
          latitude: Math.random() * 180 - 90
          longitude: Math.random() * 360 - 180
          color: '#ff3333'
          eventRadius: 5
          duration: 3000
          weight: 0.6
        smallimap.enqueueEvent event
      , 512
    """
    lastX = 0
    lastY = 0
    pxToX = (px) -> Math.floor(px / smallimap.dotDiameter)
    pyToY = (py) -> Math.floor(py / smallimap.dotDiameter)

    $('#smallimap').mousemove(function (event) {
      var px = event.pageX - $(this).offset().left,// - smallimap.width,
        py = event.pageY - $(this).offset().top,
        x = pxToX(px),
        y = pyToY(py);

      if(x != lastX || y != lastY) {
        var inEvent = new $.si.smallimap.events.LensEvent(smallimap, {
            longitude: smallimap.xToLong(x),
            latitude: smallimap.yToLat(y),
            eventRadius: 0,
            duration: 128,
            fade: "in"
        });
        smallimap.enqueueEvent(inEvent);
        var outEvent = new $.si.smallimap.events.LensEvent(smallimap, {
            longitude: smallimap.xToLong(lastX),
            latitude: smallimap.yToLat(lastY),
            eventRadius: 0,
            delay: 128,
            duration: 256,
            fade: "out"
        });
        smallimap.enqueueEvent(outEvent);
        lastX = x
        lastY = y
      }
    });
    """

  window.stopSmallimapTest = ->
    clearInterval testIntervalId

  # Init smallipops
  $('.smallipop').smallipop
    theme: 'black'
    cssAnimations:
      enabled: true
      show: 'animated flipInX'
      hide: 'animated flipOutX'

  # Init map
  window.smallimap = $('#smallimap').smallimap(mapOptions).data('api')

  # Init metrics client
  smallimap.run()

  # Get list of clients
  getClientsForMap()

  $('#startDemoButton').click (e) ->
    e.preventDefault()

    $('.smallipopTour').smallipop 'tour'

    stopSmallimapTest() if testIntervalId
    runSmallimapTest()

)(jQuery)
