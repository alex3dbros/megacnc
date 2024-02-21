(($) ->

  imageToJson = (img) ->
    canvasObj = $ '<canvas>'
    canvas = canvasObj[0]

    $('body').append canvasObj
    canvas.width = img.width
    canvas.height = img.height

    console.log "Image width: #{img.width}"
    console.log "Image height: #{img.height}"

    # Get context and draw image into canvas
    ctx = canvas.getContext '2d'
    ctx.drawImage img, 0, 0

    jsonData = []

    imageData = ctx.getImageData 0, 0, canvas.width, canvas.height

    console.log imageData

    for y in [0..imageData.width - 1]
      jsonData[y] = []
      for x in [0..imageData.height - 1]
        pos = (x * imageData.width * 4) + y * 4

        red = imageData.data[pos]
        green = imageData.data[pos + 1]
        blue = imageData.data[pos + 2]
        alpha = imageData.data[pos + 3]

        isLand = red + green + blue is 0

        if isLand
          imageData.data[pos] = 0
          imageData.data[pos+1] = 255
          imageData.data[pos+2] = 0
        else
          imageData.data[pos] = 0
          imageData.data[pos+1] = 0
          imageData.data[pos+2] = 255

        jsonData[y][x] = if isLand then 1 else 0

    ctx.putImageData imageData, 0, 0

    jsonData

  # Loading image
  console.log 'Loading image'
  worldImage = new Image() 
  $(worldImage).load ->
    console.log 'Image loaded'

    # Converting image
    console.log 'Converting image'
    worldJson = imageToJson worldImage

    # Show result
    console.log 'Result:'
    console.log worldJson

    resultDiv = $ '<div>'
    resultDiv.text JSON.stringify(worldJson)
    $('body').append resultDiv

  worldImage.src = 'img/world.png'

  # $('body').append worldImage



)(jQuery)