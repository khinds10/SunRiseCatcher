#!/usr/bin/python
# Kevin Hinds http://www.kevinhinds.com
# License: GPL 2.0
import time, json, string, cgi, subprocess, json, PIL, cv2, subprocess, colorutils, pprint
import picamera
from datetime import datetime
import numpy as np
import settings as settings
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from operator import itemgetter

def resetScreen():
    """clear and rotate screen"""
    subprocess.call([settings.digoleDriverEXE, "clear"])

def setFont(fontSize):
    """set font size for screen"""
    subprocess.call([settings.digoleDriverEXE, "setFont", fontSize])
    
def setColor(fontColor):
    """set font color for screen"""
    subprocess.call([settings.digoleDriverEXE, "setColor", fontColor])

def printByFontColorPosition(fontSize, fontColor, x, y, text, previousText):
    """erase existing text and print at x,y """
    setFont(fontSize)
    
    # print the previous text in black to then print the new text
    setColor("0")
    subprocess.call([settings.digoleDriverEXE, "printxy_abs", x, y, previousText])
    
    # print the new text at the desired color, x, y and font size
    setColor(fontColor)
    subprocess.call([settings.digoleDriverEXE, "printxy_abs", x, y, text])
        
# begin the attempt to get the current weather for sunrise data (get what time the sunrises)
count = 0
timeNow = int(time.time())
font = ImageFont.truetype("font.ttf", 17)
fontSmall = ImageFont.truetype("font.ttf", 15)
pp = pprint.PrettyPrinter(indent=4)
camera = picamera.PiCamera()

# current weather values
weatherInfo = None
sunriseTime = ''
currentFeelsLikeTemp = ''
currentHumidity = ''
currentSummary = ''
currentWindSpeed = ''
currentCloudCover = ''
todayFeelsLikeTempHigh = ''
todayFeelsLikeTempLow = ''
todaySummary = ''

#-----------------------------------------------------------------------------------------------------------------------------
# get the temp and conditions at sunrise and conditions for the day (try 10 times in case of network outage other errors)
#-----------------------------------------------------------------------------------------------------------------------------
while count < 10:
    try:
        count = count + 1
        weatherInfo = json.loads(subprocess.check_output(['curl', settings.weatherAPIURL + settings.weatherAPIKey + '/' + str(settings.latitude) + ',' + str(settings.longitude) + '?lang=en']))
        sunriseTime = weatherInfo['daily']['data'][0]['sunriseTime']
        currentFeelsLikeTemp = weatherInfo['currently']['apparentTemperature']
        currentHumidity = weatherInfo['currently']['humidity']
        currentSummary = weatherInfo['currently']['summary']
        currentWindSpeed = weatherInfo['currently']['windSpeed']
        currentCloudCover = weatherInfo['currently']['cloudCover']
        todayFeelsLikeTempHigh = weatherInfo['daily']['data'][0]['temperatureMin']
        todayFeelsLikeTempLow = weatherInfo['daily']['data'][0]['temperatureMax']
        todaySummary = weatherInfo['hourly']['summary']
        break
    except (Exception):
        time.sleep(10)

#-----------------------------------------------------------------------------------------------------------------------------
# sleep till sunrise, then start capturing pictures, if no times found then just sleep for 2 hours (so roughly around 6am)
#-----------------------------------------------------------------------------------------------------------------------------
timeTillSunrise = sunriseTime - timeNow
if (timeTillSunrise > 0):
    time.sleep(timeTillSunrise)
else:
    time.sleep(1)

#-----------------------------------------------------------------------------------------------------------------------------
# take set number of pictures in the desired time frame after sunset (set in settings)
#-----------------------------------------------------------------------------------------------------------------------------
colorsInPictures = {}
pictureColorTotals = {}
secondsBetweenPictures = int((settings.timeToCaptureMinutes * 60) / settings.numberOfSunriseCaptures)
while count <= settings.numberOfSunriseCaptures:
    try:
        count = count + 1

        # capture image from camera
        camera.capture(settings.digoleDriverFolder + 'image.jpg')

        # save the current capture
        pictureTakenFileName = time.strftime('%l:%M%p on %b %d %Y').replace(" ", "-")
        pictureTakenFileName = 'Sunrise-' + pictureTakenFileName + '.jpg';
        pictureTaken = time.strftime('%l:%M%p on %b %d')
        subprocess.call(['cp', settings.digoleDriverFolder + 'image.jpg', settings.projectFolder + pictureTakenFileName ])
        colorsInPictures[pictureTakenFileName] = {}
        pictureColorTotals[pictureTakenFileName] = 0

        # draw the current conditions and time on the sunrise full image
        img = Image.open(settings.projectFolder + pictureTakenFileName)
        draw = ImageDraw.Draw(img)
        imageForecastText = 'Today: High (' + str(int(todayFeelsLikeTempHigh)) + '*F) Low (' + str(int(todayFeelsLikeTempLow)) + '*F) ' + str(todaySummary)
        imageCurrentlyText = 'Sunrise: [' + str(pictureTaken) + ' ] / ' + str(currentSummary) + ' / Feels Like: ' + str(int(currentFeelsLikeTemp)) + '*F | ' + str(int(currentHumidity*100)) + '%'
        imageCurrentlyText2 = 'Wind Speed: ' + str(int(currentWindSpeed)) + ' mph / Cloud Cover: ' + str(int(currentCloudCover*100)) + '%' 
        draw.text( (10, 400), imageCurrentlyText , (255,255,200), font=font )
        draw.text( (10, 425), imageCurrentlyText2 , (255,255,200), font=font )
        draw.text( (10, 450), imageForecastText , (200,200,200), font=fontSmall )
        img.save(settings.projectFolder + '/sunrise-pictures/' + pictureTakenFileName)

        # resize the image to for digole display
        img = Image.open(settings.digoleDriverFolder + 'image.jpg')
        img = img.resize((settings.basewidth,settings.hsize), PIL.Image.ANTIALIAS)
        img.save(settings.digoleDriverFolder + 'image.jpg')

        # create the image data file
        file = open(settings.digoleDriverFolder + "imageData.h","w")
        file.write("const uint8_t imageData[]= {")
        file.write("0x00,0x00,0x00")

        # loop through and build the image using BGR color scheme
        img = cv2.imread(settings.digoleDriverFolder + 'image.jpg')
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        x = 0
        while (x < 128):
            y = 0
            while (y < 160):
                try:
                    px = img[x,y]
                    try:
                        colorCode = str(colorutils.rgb_to_hex((px[0], px[1], px[2])))
                        colorsInPictures[pictureTakenFileName][colorCode] = colorsInPictures[pictureTakenFileName][colorCode]  + 1
                    except:
                        colorsInPictures[pictureTakenFileName][colorCode] = 1
                    hexValue = ",0x%02x" % int(px[0]/4)
                    file.write(hexValue)
                    hexValue = ",0x%02x" % int(px[1]/4)
                    file.write(hexValue)
                    hexValue = ",0x%02x" % int(px[2]/4)
                    file.write(hexValue)        
                except:
                    pass
                y = y + 1
            x = x + 1
        file.write("};") 
        file.close()

        # compile the new image into the digole driver in C
        subprocess.call(['gcc', settings.digoleDriverFolder + 'digole.c'])
        subprocess.call(['mv', 'a.out', settings.digoleDriverFolder + 'display'])

        # reset screen and display image
        resetScreen()

        # display the image w/timestamp
        subprocess.call([settings.digoleDriverEXE, 'myimage'])
        printByFontColorPosition("10", "252", "5", "150", pictureTaken, pictureTaken)
        pictureColorTotals[pictureTakenFileName] = len(colorsInPictures[pictureTakenFileName])
        time.sleep(secondsBetweenPictures)
    except (Exception):
       time.sleep(secondsBetweenPictures)



print pictureColorTotals



# TODO

mostColorfulImage = ''
for key, value in sorted(pictureColorTotals.iteritems(), key=lambda (k,v): (v,k)):
    mostColorfulImage = key
    
print 'Most Colorful Image: ' + mostColorfulImage

# get the most colorful picture and save it to the screen

    # The little display tells the current time and weather (when sunrise started sunrise)
    
    # but save the most recent one if we're still in the middle of the capture phase
    
    # get the colors with the 'numpy' array - get the hex values from top 10 colors
                
# Email is then sent of the image with the current outdoor conditions of the picture and the forecast for the day

    # at 30 minutes after sunrise
    
# need the most recent picture taken time for the function: printByFontColorPosition("10", "252", "5", "150", pictureTaken, pictureTaken)
