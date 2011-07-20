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
import os.path

def usage():
    """Prints usage options when called with no arguments or with invalid arguments
    """
    print """usage: [options]
   -h    help
   -f    filename of fisheye panorama 
    """

class sky():
    def __init__(self):
        self.center = 0
        self.radius = 0
        self.cardinalOffset = 0 

class controller():
    def __init__(self,cImage):
        self.sky = sky()
        self.cImage = cImage
        self.res = cv.GetSize(cImage) 
        x,y = self.res
        self.sky.radius = max(self.res)/2 
        self.sky.center = (x/2,y/2)
        self.sky.cardinalOffset = 0
        self.threshold = 0
        windowName = "Fisheye"
        cv.NamedWindow(windowName,cv.CV_WINDOW_NORMAL)
        cv.NamedWindow('Image')
        cv.MoveWindow('Image',1,220)
     
        cv.CreateTrackbar ("Threshold", windowName, 1, 100, self.onThresholdChange)
        cv.CreateTrackbar ("Horizon", windowName, 10, max(self.res)/2, self.onRadiusChange)
        cv.CreateTrackbar ("North", windowName, 1, 360, self.onNorthChange)
        cv.CreateTrackbar ('x', windowName, x/2, x, self.on_Xchange)
        cv.CreateTrackbar ('y', windowName, y/2, y, self.on_Ychange)
        cv.ResizeWindow(windowName, 1200,200)
        self.onThresholdChange (0)
        
    def onThresholdChange(self, pos):
        self.threshold = pos
        self.draw()
     
    def onRadiusChange(self, rad):
        self.sky.radius = max(self.res)/2 - rad
        self.draw()

    def onNorthChange(self, offset):
        self.sky.cardinalOffset = offset
        self.draw()

    def on_Xchange(self, newx):
        x,y = self.sky.center
        self.sky.center = (newx,y)
        self.draw()

    def on_Ychange(self, newy):
        x,y = self.sky.center
        self.sky.center = (x,newy)
        self.draw()

    def draw(self):
        self.skyArray = skyToPolar(self.cImage,self.sky,self.threshold)
        self.displayImage = renderSkyArray(self.cImage,self.skyArray,self.sky)
        self.outputArray = magnitudeToTheta(self.skyArray,self.sky.radius)
        cv.ShowImage('Image', self.displayImage)

    def onSave(self):
        pass

    def save(self,filename):
        cv.SaveImage(filename +'-vectors.png',self.displayImage)
        saveArray(self.outputArray,filename + '.csv')

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

def skyToPolar(image,sky,threshold):
    """takes:  image, sky, threshold
    returns: rendered image, outputArray"""
    res = cv.GetSize(image) 
    col_edge = cv.CreateImage(res, 8, 3)
    cv.SetZero(col_edge)
    edge = getCannyMask(image,threshold)
    cv.Copy(image, col_edge, edge)
    final = drawHorizonLine(col_edge,sky)
    x,y = sky.center
    #point is in pixel cordinates, but comparision is right hand cordinates
    rPoint = (y,x)
    vectors = []
    for i in range(360):
        j = 0
        while pixelCompare(final,addVectorR(rPoint,(i,j)),rPoint) and j < sky.radius:
            j += 1
        vectors.append(((720 + 90 - i - sky.cardinalOffset) % 360 ,j))
    return vectors

def magnitudeToTheta(array,radius):
    theta = []
    for vector in array:
        a,m = vector
        t = (float(radius - m)/float(radius)) * 90 
        theta.append((a,t))
    return theta

#Drawing 
def addVector(point,vector):
    """Warning!: pixel based system
    given a vector returns point wise cordinates
    """
    angle,magnitude = vector
    x,y = point
    dx = int(magnitude * cos(radians(angle)))
    dy = int(magnitude * sin(radians(angle)))
    return (x + dx, y - dy)

def drawVectors(image,array,sky):
    """"given a start point and an array of magnitudes and degree angles
    draws on gImage"""
    for vector in array:
        a,m = vector
        cv.Line(image, sky.center, addVector(sky.center,(a+sky.cardinalOffset, m)) ,(255,0,0))
    return image


def getCannyMask(image,threshold):
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

def drawHorizonMask(image, sky):
    center = sky.center
    radius = sky.radius
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

def drawHorizonLine(image, sky):
    cv.Circle(image, sky.center, sky.radius, (255,255,255))
    return image

def drawNorth(image, sky):
    point = sky.center
    radius = sky.radius
    offset = sky.cardinalOffset
    cv.Line(image, point, addVector(point,(offset,radius)), (0,0,255))
    cv.Line(image, point, addVector(point,((offset+180) % 360,radius)), (255,255,255))
    return image

def renderSkyArray(image,skyArray,sky):
    res = cv.GetSize(image) 
    displayImage = cv.CreateImage(res, 8, 3)
    cv.SetZero(displayImage)
    cv.Copy(image, displayImage)
    displayImage = drawVectors(displayImage,skyArray, sky)
    displayImage = drawNorth(displayImage, sky)
    displayImage = drawHorizonLine(displayImage,sky)
    return displayImage

#misc
def saveArray(array,filename):
    f = open(filename,'w')
    f.write('00 Cordinates to come later\n')
    f.write(','.join([str(v[0]) for v in array]))
    f.write('\n')
    f.write(','.join([str(v[1]) for v in array]))
    f.write('\n')
    f.flush()
    f.close()

def saveVectorImage(filename,vectorArray,res,sky):
    vectorImage = cv.CreateImage(res, 8, 3)
    cv.Zero(vectorImage)
    drawVectors(vectorImage,vectorArray,sky)
    cv.SaveImage(filename,vectorImage)

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
        gImage = cv.LoadImage(filename)
        if not gImage:
            print "Error loading image '%s'" % filename
            sys.exit(-1) 

        ui = controller(gImage)
        cv.WaitKey (0)
        ui.save(os.path.basename(filename).split('.')[0])

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
