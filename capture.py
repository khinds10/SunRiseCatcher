#!/usr/bin/python
# Kevin Hinds http://www.kevinhinds.com
# License: GPL 2.0
import time, json, string, cgi, subprocess, json, PIL, cv2, subprocess
#import picamera
from datetime import datetime
import numpy as np
import settings as settings
from PIL import Image

# begin the attempt to get the current weather for sunrise data (get what time the sunrises)
count = 0
timeNow = int(time.time())

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
    sleep(timeTillSunrise)
else:
    sleep(7200)

#-----------------------------------------------------------------------------------------------------------------------------
# take pictures each 2 minutes after sunrise starts for 30 minutes (try 10 times in case of error)
#-----------------------------------------------------------------------------------------------------------------------------
#while count < 15:
#try:
#count = count + 1

# capture image from camera
camera = picamera.PiCamera()
camera.capture(digoleDriverFolder + 'image.jpg')

# save the current capture
pictureTaken = "{:%c}".format(datetime.now()).replace(" ", "-")
subprocess.call(['cp', digoleDriverFolder + 'image.jpg', projectFolder + 'sunrise-' + pictureTaken + '.jpg'])

# resize the image to for digole display
img = Image.open(digoleDriverFolder + 'image.jpg')
img = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
img.save(digoleDriverFolder + 'image.jpg')

# create the image data file
file = open(digoleDriverFolder + "imageData.h","w")
file.write("const uint8_t imageData[]= {")
file.write("0x00,0x00,0x00")

# loop through and build the image using BGR color scheme
img = cv2.imread('image.jpg')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
x = 0
while (x < 128):
    y = 0
    while (y < 160):
        try:
            px = img[x,y]
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
subprocess.call(['gcc', digoleDriverFolder + 'digole.c'])
subprocess.call(['mv', digoleDriverFolder + 'a.out', digoleDriverFolder + 'display'])

# reset screen and display image
subprocess.call([settings.digoleDriverEXE, "clear"])

# display the image
subprocess.call([settings.digoleDriverEXE, 'myimage'])

#time.sleep(120)    
#break
#except (Exception):
#time.sleep(120)

# TODO

# get the most colorful picture and save it to the screen

    # The little display tells the current time and weather (when sunrise started sunrise)
    
    # but save the most recent one if we're still in the middle of the capture phase
    
    # get the colors with the 'numpy' array - get the hex values from top 10 colors
                
# Email is then sent of the image with the current outdoor conditions of the picture and the forecast for the day

    # at 30 minutes after sunrise