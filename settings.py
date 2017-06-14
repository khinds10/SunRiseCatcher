#!/usr/bin/python
# Kevin Hinds http://www.kevinhinds.com
# License: GPL 2.0

# your email address (sunrise pictures mailed out)
emailAddress = 'your-email@gmail.com'

# forecast.io API key for local weather information
weatherAPIURL = 'https://api.forecast.io/forecast/'
weatherAPIKey = 'YOUR FORECAST.IO KEY HERE'

# digole display driver settings
projectFolder = '/home/pi/SunRiseCatcher/'
digoleDriverFolder = projectFolder + 'display/'
digoleDriverEXE = digoleDriverFolder + "display"

# capture image settings
basewidth = 160
hsize = 128

# number of sunrise images to capture in the morning
numberOfSunriseCaptures = 15

# how long after sunrise to capture pictures for in minutes
timeToCaptureMinutes = 30

# optional for running the remote sunrise logger
deviceLoggerAPI = 'YOUR API URL'

# search google to get the Latitude/Longitude for your home location
latitude = 42.4152778
longitude = -71.1569444