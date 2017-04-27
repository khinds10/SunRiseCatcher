import picamera, PIL
from PIL import Image
camera = picamera.PiCamera()
camera.capture('image.jpg')

basewidth = 160
img = Image.open('image.jpg')
wpercent = (basewidth/float(img.size[0]))
hsize = int((float(img.size[1])*float(wpercent)))
img = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
img.save('image.jpg')