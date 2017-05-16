import picamera, PIL, cv2, subprocess
import numpy as np
from PIL import Image

# settings
digoleDriveLocation = "/home/pi/display"
basewidth = 160
hsize = 128

def resetScreen():
    """clear screen"""
    subprocess.call([digoleDriveLocation, "clear"])

# capture image from camera
camera = picamera.PiCamera()
camera.capture('image.jpg')

# resize the image to for digole display
img = Image.open('image.jpg')
img = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
img.save('image.jpg')

# create the image data file
file = open("imageData.h","w")
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
subprocess.call(['gcc', 'digole.c'])
subprocess.call(['mv', 'a.out', 'display'])

# reset screen and display image
resetScreen()

# display the image
subprocess.call(['./display', 'myimage'])