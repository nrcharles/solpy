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
   -f    filename of photo 
    """
 
# some definitions
global outputArray 
gImage = None

#class world
#physical data
#token to pass env data through GUI
#
class nugget():
    def __init__(self):
        self.center = 0
        self.res = None
        self.radius = 0
        self.cardinalOffset = 0 

class GUI():
    def __init__(self,cImage):
        self.cImage = cImage
        self.threshold = 0
        res = cv.GetSize(cImage) 
        self.res = res
        self.radius = max(self.res)/2 
        x,y = res
        self.center = (x/2,y/2)
        self.threshold = 0
        self.cardinalOffset = 0
        windowName = "Edge"
        # create the window
        cv.NamedWindow(windowName,cv.CV_WINDOW_NORMAL)
        cv.NamedWindow('Image')
        cv.MoveWindow('Image',1,220)
     
        # create the trackbar
        cv.CreateTrackbar ("Threshold", windowName, 1, 100, self.onThresholdChange)
        cv.CreateTrackbar ("Horizon", windowName, 10, max(res)/2, self.onRadiusChange)
        cv.CreateTrackbar ("North", windowName, 1, 360, self.onNorthChange)
        cv.CreateTrackbar ('x', windowName, x/2, x, self.on_Xchange)
        cv.CreateTrackbar ('y', windowName, y/2, y, self.on_Ychange)
        #cv.CreateButton('save', self.onSave)
        cv.ResizeWindow(windowName, 1200,200)
        self.onThresholdChange (0)
        
    def onThresholdChange(self, pos):
        self.threshold = pos
        draw(self)
     
    def onRadiusChange(self, rad):
        self.radius = max(self.res)/2 - rad
        draw(self)

    def onNorthChange(self, offset):
        self.cardinalOffset = offset
        draw(self)

    def on_Xchange(self, newx):
        x,y = self.center
        self.center = (newx,y)
        draw(self)

    def on_Ychange(self, newy):
        x,y = self.center
        self.center = (x,newy)
        draw(self)

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

def distanceToEdge(image, point, radius, cardinalOffset = 0 ):
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
    #debugging window
    #cv.NamedWindow('temp')
    #cv.MoveWindow('temp',800,220)
    #cv.ShowImage('temp', image)
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

def drawVectors(image,point,array,cardinalOffset = 0):
    """"given a start point and an array of magnitudes and degree angles
    draws on gImage"""
    for vector in array:
        a,m = vector
        cv.Line(image, point, addVector(point,(a+cardinalOffset, m)) ,(255,0,0))
    return image

def magnitudeToTheta(array,radius):
    theta = []
    for vector in array:
        a,m = vector
        t = (float(radius - m)/float(radius)) * 90 
        theta.append((a,t))
    return theta

def saveArray(array,filename):
    #print array
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

def saveVectorImage(filename,center,vectorArray,res,cardinalOffset = 0):
    vectorImage = cv.CreateImage(res, 8, 3)
    cv.Zero(vectorImage)
    drawVectors(vectorImage,center,vectorArray,cardinalOffset)
    cv.SaveImage(filename,vectorImage)

def drawHorizonMask(image, center, radius):
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

def drawNorth(image, point, radius, offset):
    cv.Line(image, point, addVector(point,(offset,radius)), (0,0,255))
    cv.Line(image, point, addVector(point,((offset+180) % 360,radius)), (255,255,255))
    return image

def draw(env):
    res = cv.GetSize(env.cImage) 
    col_edge = cv.CreateImage(res, 8, 3)
    cv.SetZero(col_edge)
    edge = getCannyMask(env.cImage,env.threshold)
    cv.Copy(env.cImage, col_edge, edge)
    final = drawHorizonLine(col_edge,env.center,env.radius)
    skyArray = distanceToEdge(final,env.center,env.radius,env.cardinalOffset)

    displayImage = cv.CreateImage(res, 8, 3)
    cv.SetZero(displayImage)
    cv.Copy(env.cImage, displayImage)
    displayImage = drawVectors(displayImage, env.center, skyArray, env.cardinalOffset)
    displayImage = drawNorth(displayImage,env.center,env.radius, env.cardinalOffset)
    displayImage = drawHorizonLine(displayImage,env.center, env.radius)

    env.outputArray = magnitudeToTheta(skyArray,env.radius)
    env.displayImage = displayImage

    cv.ShowImage('Image', displayImage)


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

        ui = GUI(gImage)
        cv.WaitKey (0)
        ui.save(os.path.basename(filename).split('.')[0])

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
