#! /usr/bin/env python
# Copyright (C) 2010 Nathan Charles
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import cv
from math import sin
from math import cos
from math import radians

def usage():
    """Prints usage options when called with no arguments or with invalid arguments
    """
    print """usage: [options]
   -h    help
   -f    filename of photo 
    """
 
# some definitions
global radius 
global outputArray 
global cardinalOffset
cardinalOffset = 0
global threshold 
global center
global res
gImage = None

#UI Control
def onThresholdChange(pos):
    global threshold
    threshold = pos
    draw()
 
def onRadiusChange(rad):
    global radius
    global res
    radius = max(res)/2 - rad
    draw()

def onNorthChange(offset):
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

#Measurement 
def addVectorR(point,vector):
    """Warning!: righthanded cordinate system
    given a vector returns gImage array cordinates
    """
    angle,magnitude = vector
    x,y = point
    dx = int(magnitude * cos(radians(angle)))
    dy = int(magnitude * sin(radians(angle)))
    return (x - dx,y + dy)

def pixelCompare(image, p1,p2):
    x1,y1 = p1
    x2,y2 = p2
    if (image[x1,y1] == image[x2,y2]):
        return True
    else:
        return False

def distanceToEdge(image, point, radius):
    rx,ry = cv.GetSize(image) 
    x,y = point
    #point is in pixel cordinates, but comparision is right hand cordinates
    rPoint = (y,x)
    vectors = []
    for i in range(360):
        j = 0
        while pixelCompare(image,addVectorR(rPoint,(i,j)),rPoint) and j < radius:
            j += 1
        vectors.append(((720 + 90 - i - cardinalOffset) % 360 ,j))
    image[y,x+4] = (255,0,255)
    cv.Circle(image, point, 1, (0,255,0))
    cv.Circle(image, (x/2,y/2), 1, (255,255,255))
    cv.ShowImage('temp', image)
    return vectors

def addVector(point,vector):
    """Warning!: pixel based system
    given a vector returns point wise cordinates
    """
    angle,magnitude = vector
    x,y = point
    dx = int(magnitude * cos(radians(angle)))
    dy = int(magnitude * sin(radians(angle)))
    return (x + dx, y - dy)

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
        t = (float(radius - m)/float(radius)) * 90 
        theta.append((a,t))
    return theta

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
    vectorImage = cv.CreateImage(res, 8, 3)
    cv.Zero(vectorImage)
    drawVectors(vectorImage,center,vectorArray)
    cv.SaveImage(filename,vectorImage)

def drawHorizonMask(image,radius):
    res = cv.GetSize(image) 
    mask = cv.CreateImage(res, 8, 1)
    cv.Zero(mask)
    reimage = cv.CreateImage(res, 8, 3)
    cv.Zero(reimage)
    cv.Circle(mask, center, radius, (255,255,255))
    cv.FloodFill(mask,(1,1),(0,0,0))
    cv.FloodFill(mask, center, (255,255,255),lo_diff=cv.RealScalar(5))
    cv.Copy(image, reimage, mask)
    return reimage 

def drawHorizonLine(image, center, radius):
    cv.Circle(image, center, radius, (255,255,255))
    return image

def drawNorth(image, point, offset):
    global radius
    cv.Line(image, point, addVector(point,(offset,radius)), (0,0,255))
    cv.Line(image, point, addVector(point,((offset+180) % 360,radius)), (255,255,255))
    return image

def draw():
    global gImage
    global outputArray
    global cardinalOffset
    global center
    res = cv.GetSize(gImage) 
    col_edge = cv.CreateImage(res, 8, 3)
    cv.SetZero(col_edge)

    edge = getCannyMask(gImage)
    cv.Copy(gImage, col_edge, edge)
    final = drawHorizonLine(col_edge,center,radius)
    skyArray = distanceToEdge(final,center,radius)

    displayImage = cv.CreateImage(res, 8, 3)
    cv.SetZero(displayImage)
    cv.Copy(gImage, displayImage)
    displayImage = drawVectors(displayImage, center, skyArray)
    displayImage = drawNorth(displayImage,center,cardinalOffset)
    displayImage = drawHorizonLine(displayImage,center, radius)

    saveVectorImage('vectorImage.png',skyArray,res)
    outputArray = magnitudeToTheta(skyArray)

    cv.ShowImage('Image', displayImage)
    cv.SaveImage('final.png',displayImage)

def bootstrap(filename):
    global radius
    global gImage
    global center
    global res
    windowName = "Edge"

    gImage = cv.LoadImage (filename)
    res = cv.GetSize(gImage) 
 
    if not gImage:
        print "Error loading image '%s'" % filename
        sys.exit(-1) 

    # create the window
    cv.NamedWindow(windowName,cv.CV_WINDOW_NORMAL)
    cv.NamedWindow('Image')
    cv.MoveWindow('Image',1,220)
    cv.NamedWindow('temp')
    cv.MoveWindow('temp',800,220)
 
    # create the trackbar
    x,y = res
    center = (x/2,y/2)
    cv.CreateTrackbar ("Threshold", windowName, 1, 100, onThresholdChange)
    cv.CreateTrackbar ("Horizon", windowName, 10, max(res)/2, onRadiusChange)
    cv.CreateTrackbar ("North", windowName, 1, 360, onNorthChange)
    cv.CreateTrackbar ('x', windowName, x/2, x, on_Xchange)
    cv.CreateTrackbar ('y', windowName, y/2, y, on_Ychange)
    cv.ResizeWindow(windowName, 1200,200)
    radius = max(res)/2 - 10 
 
    onThresholdChange (0)
 
    cv.WaitKey (0)

    writeArray(outputArray,'output.csv')

if __name__ == "__main__":
    import getopt
    import sys
    opts, args = getopt.getopt(sys.argv[1:], 'f:h')
    filename = None
 
    if opts:
        for o,a in opts:
            if o == '-h':
                usage()
                sys.exit(1)
            if o == '-f':
                filename = a
    else:
        usage()
        sys.exit(1)

    try:
        #start program  
        bootstrap(filename)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
