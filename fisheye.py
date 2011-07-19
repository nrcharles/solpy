#! /usr/bin/env python
 
print "OpenCV Python version of edge"
 
import sys
 
# import the necessary things for OpenCV
#from opencv import cv
#from opencv import cv
#from cv import *
import cv
from math import sin
from math import cos
from math import radians
 
# some definitions
win_name = "Edge"
trackbar_name = "Threshold"
trackbar_name1 = "Radius"
trackbar_name2 = "North"
global radius 
global outputArray 
global cardinalOffset
cardinalOffset = 0
global threshold 
global center
gImage = None

def addVectorR(point,vector):
    """Warning!: righthanded cordinate system
    given a vector returns gImage array cordinates
    """
    angle,magnitude = vector
    x,y = point
    dx = int(magnitude * cos(radians(angle)))
    dy = int(magnitude * sin(radians(angle)))
    #return (y + dy,x - dx)
    return (x - dx,y + dy)
    #return (x + dx,y + dy)
    #return (x + dx,y - dy)
    #return (x - dx,y - dy)

def addVector(point,vector):
    """Warning!: pixel based system
    given a vector returns point wise cordinates
    """
    angle,magnitude = vector
    x,y = point
    dx = int(magnitude * cos(radians(angle)))
    dy = int(magnitude * sin(radians(angle)))
    return (x + dx, y - dy)

def pixelCompare(image, p1,p2):
    x1,y1 = p1
    x2,y2 = p2
    if (image[x1,y1] == image[x2,y2]):
        return True
    else:
        return False

def distanceToEdge(image, point, radius):
    rx,ry = cv.GetSize(image) 
    print rx,ry
    x,y = point
    #point is in pixel cordinates, but comparision is right hand cordinates
    rPoint = (y,x)
    print "conversion",point,rPoint
    vectors = []
    for i in range(360):
        j = 0
        while pixelCompare(image,addVectorR(rPoint,(i,j)),rPoint) and j < radius:
            j += 1
        vectors.append(((720 + 90 - i - cardinalOffset) % 360 ,j))
        #cv.Line(image, point, addVector(point,i,j), (0,0,255))
        #cv.ShowImage('temp', image)
    image[y,x+4] = (255,0,255)
    cv.Circle(image, point, 1, (0,255,0))
    cv.Circle(image, (x/2,y/2), 1, (255,255,255))
    cv.ShowImage('temp', image)
    return vectors

def drawVectors(image,point,array):
    """"given a start point and an array of magnitudes and degree angles
    draws on gImage"""
    for vector in array:
        a,m = vector
        cv.Line(image, point, addVector(point,(a+cardinalOffset, m)) ,(255,0,0))
    return image

def magnitudeToTheta(array):
    theta = []
    for vector in array:
        a,m = vector
        #print radius,m
        t = (float(radius - m)/float(radius)) * 90 
        theta.append((a,t))
    return theta
 
def on_trackbar (pos):
    global threshold
    threshold = pos
    draw()
 
def on_trackbar1 (rad):
    global radius
    radius = max(res)/2 - rad
    draw()

def on_trackbar2 (offset):
    global cardinalOffset
    cardinalOffset = offset
    draw()

def on_Xchange(newx):
    global center
    x,y = center
    center = (newx,y)
    draw()

def on_Ychange(newy):
    global center
    x,y = center
    center = (x,newy)
    draw()

class c():
    def __init__(self, seq):
        self.contours =[]
        self._traverse(seq)
    def _traverse(self, seq):
        while seq:
            self._traverse(seq.v_next())
            self.contours.append(seq)
            seq = seq.h_next()
        self.contours.sort()
    def sky(self):
        print cv.ContourArea(self.contours[1])
        return self.contours[1]

def getSkyContour(skygImage):
    storage = cv.CreateMemStorage()
    seq = cv.FindContours(skygImage, storage, cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_SIMPLE)
    ci = c(seq)
    return ci.sky()

def writeArray(array,filename):
    print array
    f = open(filename,'w')
    #for value in outputArray:
    #    f.write('%s,%s\n' % value)
    f.write('00 Cordinates to come later\n')
    f.write(','.join([str(v[0]) for v in array]))
    f.write('\n')
    f.write(','.join([str(v[1]) for v in array]))
    f.write('\n')
    f.flush()
    f.close()

def drawHorizonMask(image,radius):
    res = cv.GetSize(image) 
    x,y = res
    mask = cv.CreateImage(res, 8, 1)
    cv.Zero(mask)
    reimage = cv.CreateImage(res, 8, 3)
    cv.Zero(reimage)
    cv.Circle(mask, center, radius, (255,255,255))
    cv.FloodFill(mask,(1,1),(0,0,0))
    cv.FloodFill(mask, center, (255,255,255),lo_diff=cv.RealScalar(5))
    cv.Copy(image, reimage, mask)
    return reimage 

def drawHorizonLine(image,radius):
    res = cv.GetSize(image) 
    x,y = res
    cv.Circle(image, center, radius, (255,255,255))
    return image

def drawNorth(image, point, offset):
    global radius
    cv.Line(image, point, addVector(point,(offset,radius)), (0,0,255))
    cv.Line(image, point, addVector(point,((offset+180) % 360,radius)), (255,255,255))
    return image

def getCannyMask(image):
    """convert image to gray scale run the edge dector 
    returns mask
    """
    res = cv.GetSize(image) 
    gray = cv.CreateImage (res, 8, 1)
    mask = cv.CreateImage (res, 8, 1)
    cv.CvtColor(image, gray, cv.CV_BGR2GRAY)
    cv.Smooth (gray, mask, cv.CV_BLUR, 3, 3, 0)
    cv.Not(gray, mask)
 
    cv.Canny(gray, mask, threshold, threshold * 3, 3)
    return mask

def saveVectorImage(filename,vectorArray,res):
    x,y = res
    vectorImage = cv.CreateImage(res, 8, 3)
    cv.Zero(vectorImage)
    drawVectors(vectorImage,center,vectorArray)
    cv.SaveImage(filename,vectorImage)

def draw():
    global gImage
    global outputArray
    global cardinalOffset
    x,y = res
    col_edge = cv.CreateImage(res, 8, 3)
    cv.SetZero(col_edge)

    edge = getCannyMask(gImage)
    cv.Copy(gImage, col_edge, edge)
    final = drawHorizonLine(col_edge,radius)
    skyArray = distanceToEdge(final,center,radius)

    displayImage = cv.CreateImage(res, 8, 3)
    cv.SetZero(displayImage)
    cv.Copy(gImage, displayImage)
    displayImage = drawVectors(displayImage, center, skyArray)
    displayImage = drawNorth(displayImage,center,cardinalOffset)
    displayImage = drawHorizonLine(displayImage,radius)

    saveVectorImage('vectorImage.png',skyArray,res)
    outputArray = magnitudeToTheta(skyArray)

    cv.ShowImage('Image', displayImage)
    cv.SaveImage('final.png',displayImage)
 
if __name__ == '__main__':
    global radius
    #filename = "/Users/nathan/polar.png"
    #filename = "/Users/nathan/Desktop/out2LR.png"
    filename = "/Users/nathan/Desktop/out2-fisheye.png"

 
    if len(sys.argv)>1:
        filename = sys.argv[1]
 
    # load the gImage gived on the command line
    gImage = cv.LoadImage (filename)
    res = cv.GetSize(gImage) 
    #res =(683, 681)
    #print res
 
    if not gImage:
        print "Error loading image '%s'" % filename
        sys.exit(-1) 

    # create the window
    cv.NamedWindow (win_name,cv.CV_WINDOW_NORMAL)
    cv.NamedWindow('Image')
    cv.MoveWindow('Image',1,220)
    cv.NamedWindow('temp')
    cv.MoveWindow('temp',800,220)
 
    # create the trackbar
    x,y = res
    cv.CreateTrackbar (trackbar_name, win_name, 1, 100, on_trackbar)
    cv.CreateTrackbar (trackbar_name1, win_name, 10, max(res)/2, on_trackbar1)
    cv.CreateTrackbar (trackbar_name2, win_name, 1, 360, on_trackbar2)
    cv.CreateTrackbar ('x', win_name, x/2, x, on_Xchange)
    cv.CreateTrackbar ('y', win_name, y/2, y, on_Ychange)
    center = (x/2,y/2)
    cv.ResizeWindow(win_name, 1200,200)
    radius = max(res)/2 - 10 
 
    # show the gImage
    on_trackbar (0)
 
    # wait a key pressed to end
    cv.WaitKey (0)
    writeArray(outputArray,'output.csv')
