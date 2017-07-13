#!/usr/bin/python
# Kevin Hinds http://www.kevinhinds.com
# License: GPL 2.0
import time, json, string, cgi, subprocess, json, PIL, cv2, subprocess, colorutils, pprint, os
import picamera
from datetime import datetime
import numpy as np
import settings as settings
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from operator import itemgetter

# set directory for the script to run locally for GCC commands
os.chdir("/home/pi/SunRiseCatcher")

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
font = ImageFont.truetype("/home/pi/SunRiseCatcher/fonts/BitstreamVeraSans.ttf", 17)
fontSmall = ImageFont.truetype("/home/pi/SunRiseCatcher/fonts/BitstreamVeraSans.ttf", 15)
pp = pprint.PrettyPrinter(indent=4)
camera = picamera.PiCamera()
camera.vflip = True
camera.hflip = True
        
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
        todayFeelsLikeTempHigh = weatherInfo['daily']['data'][0]['temperatureMax']
        todayFeelsLikeTempLow = weatherInfo['daily']['data'][0]['temperatureMin']
        todaySummary = weatherInfo['hourly']['summary']
        break
    except (Exception):
        time.sleep(10)

#-----------------------------------------------------------------------------------------------------------------------------
# sleep till sunrise, then start capturing pictures, if no times found then just sleep for 2 hours (so roughly around 6am)
#-----------------------------------------------------------------------------------------------------------------------------
timeTillSunrise = sunriseTime - timeNow
if (timeTillSunrise > 0):
    print "Sleeping till Sunrise (zzz): " + str(timeTillSunrise) + " seconds"
    time.sleep(timeTillSunrise)
else:
    time.sleep(1)

#-----------------------------------------------------------------------------------------------------------------------------
# take set number of pictures in the desired time frame after sunset (set in settings)
#-----------------------------------------------------------------------------------------------------------------------------
colorsInPictures = {}
pictureColorTotals = {}
cameraPictureTaken = settings.digoleDriverFolder + 'image.jpg'
secondsBetweenPictures = int((settings.timeToCaptureMinutes * 60) / settings.numberOfSunriseCaptures)
sunriseOccuredTime = datetime.fromtimestamp(sunriseTime)
sunriseOccuredTime = sunriseOccuredTime.strftime('%l:%M%p on %b %d %Y')
while count <= settings.numberOfSunriseCaptures:
    try:

        # capture image from camera
        camera.capture(cameraPictureTaken)

        # save the current capture
        pictureTakenFileName = time.strftime('%l:%M%p on %b %d %Y').replace(" ", "-")
        pictureTakenFileName = 'Sunrise-' + pictureTakenFileName + '.jpg';
        pictureTaken = time.strftime('%l:%M%p on %b %d ')
        subprocess.call(['cp', cameraPictureTaken, settings.projectFolder + '/sunrise-pictures/' + pictureTakenFileName ])
        colorsInPictures[pictureTakenFileName] = {}
        pictureColorTotals[pictureTakenFileName] = 0

        # resize the image to for digole display
        img = Image.open(cameraPictureTaken)
        img = img.resize((settings.basewidth, settings.hsize), PIL.Image.ANTIALIAS)
        img.save(cameraPictureTaken)

        # create the image data file
        file = open(settings.digoleDriverFolder + "imageData.h","w")
        file.write("const uint8_t imageData[]= {")
        file.write("0x00,0x00,0x00")

        # loop through and build the image using BGR color scheme
        img = cv2.imread(cameraPictureTaken)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        x = 0
        while (x < 128):
            y = 0
            while (y < 160):
                try:
                    px = img[x,y]
                    try:
                        colorCode = str(colorutils.rgb_to_hex((px[0], px[1], px[2])))
                        colorsInPictures[pictureTakenFileName][colorCode] = colorsInPictures[pictureTakenFileName][colorCode] + 1
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

        # display the image w/timestamp on digole display
        subprocess.call([settings.digoleDriverEXE, 'myimage'])
        printByFontColorPosition("10", "252", "5", "375", pictureTaken, pictureTaken)
        pictureColorTotals[pictureTakenFileName] = len(colorsInPictures[pictureTakenFileName])
        time.sleep(secondsBetweenPictures)
        count = count + 1
        
    except (Exception):
       time.sleep(secondsBetweenPictures)

# get the most colorful image and display it on the digole display / email it to user for morning email
mostColorfulImage = ''
currentMostColorfulImage = settings.digoleDriverFolder + 'currentMostColorful.jpg'
for key, value in sorted(pictureColorTotals.iteritems(), key=lambda (k,v): (v,k)):
    mostColorfulImage = key
mostColorfulImage = settings.projectFolder + '/sunrise-pictures/' + mostColorfulImage
print 'Most Colorful Sunrise Image is: ' + mostColorfulImage

# resize the image to for digole display
img = Image.open(mostColorfulImage)
img = img.resize((settings.basewidth,settings.hsize), PIL.Image.ANTIALIAS)
img.save(currentMostColorfulImage)

# create the image data file
file = open(settings.digoleDriverFolder + "imageData.h","w")
file.write("const uint8_t imageData[]= {")
file.write("0x00,0x00,0x00")

# loop through and build the image using BGR color scheme
img = cv2.imread(currentMostColorfulImage)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
x = 0
while (x < 128):
    y = 0
    while (y < 160):
        try:
            px = img[x,y]
            colorCode = str(colorutils.rgb_to_hex((px[0], px[1], px[2])))
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
printByFontColorPosition("10", "252", "5", "375", pictureTaken, pictureTaken)

# draw the current conditions and time on the sunrise full image
img = Image.open(mostColorfulImage)
draw = ImageDraw.Draw(img)
imageForecastText = 'Today: (' + str(int(todayFeelsLikeTempHigh)) + '*F)  High / (' + str(int(todayFeelsLikeTempLow)) + '*F) Low / ' + str(todaySummary)
imageCurrentlyText = 'Sunrise Conditions @ [' + str(sunriseOccuredTime) + ' ] / ' + str(currentSummary) + ' / Felt Like: ' + str(int(currentFeelsLikeTemp)) + '*F [' + str(int(currentHumidity*100)) + '%]'
imageCurrentlyText2 = 'Wind Speed was: ' + str(int(currentWindSpeed)) + ' mph / Cloud Cover was: ' + str(int(currentCloudCover*100)) + '%' 
draw.text( (10, 400), imageCurrentlyText , (255,255,200), font=font )
draw.text( (10, 425), imageCurrentlyText2 , (255,255,200), font=font )
draw.text( (10, 450), imageForecastText , (200,200,200), font=fontSmall )
img.save(mostColorfulImage)

#email the most colorful image as a morning email
subprocess.Popen( "/usr/bin/uuencode " + mostColorfulImage + " sunrise.jpg | /usr/bin/mail -s 'Sunrise: " + time.strftime('%b %d, %Y') +"' " + settings.emailAddress, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
