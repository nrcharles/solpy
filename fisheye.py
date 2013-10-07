#! /usr/bin/env python
# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

import sys
import cv
from math import sin
from math import cos
from math import radians
import os.path

def usage():
    """Prints usage options when called with no arguments or with invalid 
    arguments
    """
    print """usage: [options]
   -h    help
   -c    output cropped &rotated image
   -f    filename of fisheye panorama 
   -n    North = 180 [default is North = 0]
    """

class model():
    def __init__(self, initialImage, NORTH = 180):
        #model
        self.cImage = initialImage
        self.res = cv.GetSize(self.cImage)
        x,y = self.res
        self.radius = min(self.res)/2
        self.center = (x/2,y/2)
        self.cardinalOffset = 90
        self.threshold = 0
        self.polarArray = []
        self.north = NORTH

    def render(self):
        """draw Vectors, North, then Horizon"""
        displayImage = cv.CloneImage(self.cImage)
        #vectors
        for vector in self.polarArray:
            a,m = vector
            cv.Line(displayImage, self.center, addVector(self.center,
                (a+self.cardinalOffset + self.north, m)) ,(255,0,0))

        #north
        point = self.center
        offset = self.cardinalOffset
        cv.Line(displayImage, point, addVector(point,(offset,self.radius)),
                (0,0,255))
        cv.Line(displayImage, point, addVector(point,((offset+180) % 360,
            self.radius)), (255,255,255))

        #horizon
        cv.Circle(displayImage, self.center, self.radius, (255,255,255))
        return displayImage

    def calculate(self):
        res = cv.GetSize(self.cImage)
        col_edge = cv.CreateImage(res, 8, 3)
        cv.SetZero(col_edge)
        edge = getCannyMask(self.cImage,self.threshold)
        cv.Copy(self.cImage, col_edge, edge)
        cv.Circle(col_edge, self.center, self.radius, (255,255,255))
        x,y = self.center
        #point is in pixel cordinates, but comparision is right hand cordinates
        rPoint = (y,x)
        vectors = []
        for i in range(360):
            j = 0
            while pixelCompare(col_edge,addVectorR(rPoint,(i,j)),rPoint) \
                    and j < self.radius:
                j += 1
            vectors.append(((1080 + 90 -i -self.cardinalOffset -self.north) \
                    % 360 ,j))
        #return vectors
        self.polarArray = vectors

    def save(self, filename, cropFlag = False):
        """save cropped and rotated image"""
        if not cropFlag:
            cv.SaveImage(filename +'-vectors.png',self.render())
        else:
            tmp = rotate(self.cImage, self.center, self.cardinalOffset +\
                    self.north)
            #mask horizon
            mask = cv.CreateImage(self.res, 8, 1)
            cv.Zero(mask)
            cv.Circle(mask, self.center, self.radius, (255,255,255))
            cv.FloodFill(mask,(1,1),(0,0,0))
            cv.FloodFill(mask, self.center,
                    (255,255,255),lo_diff=cv.RealScalar(5))
            masked = cv.CloneImage(tmp)
            cv.Zero(masked)
            cv.Copy(tmp, masked, mask)
            cv.SaveImage(filename +'-cropped.png',crop(masked, self))
        #CSV output
        array = magnitudeToTheta(self.polarArray,self.radius)
        f = open(filename + '.csv', 'w')
        f.write('00\n')
        f.write(','.join([str(v[0]) for v in array]))
        f.write('\n')
        f.write(','.join([str(v[1]) for v in array]))
        f.write('\n')
        f.flush()
        f.close()


def crop(src, sky):
    x,y  = sky.center
    left = x - sky.radius
    top = y - sky.radius
    new_width = 2 * sky.radius
    new_height = 2 * sky.radius
    cropped = cv.GetSubRect(src, (left, top, new_width, new_height) )
    return cropped

def rotate(src, center, angle):
    mapMatrix = cv.CreateMat(2,3,cv.CV_64F)
    #cv.GetRotationMatrix2D( center, 450 - angle, 1.0, mapMatrix)
    cv.GetRotationMatrix2D( center, 270 - angle, 1.0, mapMatrix)
    dst = cv.CreateImage( cv.GetSize(src), src.depth, src.nChannels)
    cv.SetZero(dst)
    cv.WarpAffine(src, dst, mapMatrix)
    return dst

class controller():
    def __init__(self, cModel):
        self.model = cModel
        windowName = "Fisheye"
        cv.NamedWindow(windowName,cv.CV_WINDOW_NORMAL)
        cv.NamedWindow('Image')
        cv.MoveWindow('Image',1,220)
        x,y = self.model.res

        cv.CreateTrackbar ("Threshold", windowName, 1, 100,
                self.onThresholdChange)
        cv.CreateTrackbar ("Horizon", windowName, 10,
                min(self.model.res)/2, self.onRadiusChange)
        cv.CreateTrackbar ("North", windowName, 90, 360, self.onNorthChange)
        cv.CreateTrackbar ('x', windowName, x/2, x, self.on_Xchange)
        cv.CreateTrackbar ('y', windowName, y/2, y, self.on_Ychange)
        cv.ResizeWindow(windowName, 1200,200)
        self.onThresholdChange (0)

    def onThresholdChange(self, pos):
        self.model.threshold = pos
        self.draw()

    def onRadiusChange(self, rad):
        self.model.radius = min(self.model.res)/2 - rad
        self.draw()

    def onNorthChange(self, offset):
        self.model.cardinalOffset = offset
        self.draw()

    def on_Xchange(self, newx):
        x,y = self.model.center
        self.model.center = (newx,y)
        self.draw()

    def on_Ychange(self, newy):
        x,y = self.model.center
        self.model.center = (x,newy)
        self.draw()

    def draw(self):
        self.model.calculate()
        self.displayImage = self.model.render()
        cv.ShowImage('Image', self.displayImage)

    def test(self,img):
        cv.ShowImage('Image',img)

    def onSave(self):
        pass

#Measurement
def addVectorR(point, vector):
    """Warning!: righthanded cordinate system
    given a vector returns gImage array cordinates
    """
    angle,magnitude = vector
    x,y = point
    dx = int(magnitude * cos(radians(angle)))
    dy = int(magnitude * sin(radians(angle)))
    return (x - dx,y + dy)

def pixelCompare(image, p1, p2):
    x1,y1 = p1
    x2,y2 = p2
    if (image[x1,y1] == image[x2,y2]):
        return True
    else:
        return False

def magnitudeToTheta(array, radius):
    theta = []
    for vector in array:
        a,m = vector
        t = (float(radius - m)/float(radius)) * 90
        theta.append((a,t))
    return theta

#Drawing
def addVector(point, vector):
    """Warning!: pixel based system
    given a vector returns point wise cordinates
    """
    angle,magnitude = vector
    x,y = point
    dx = int(magnitude * cos(radians(angle)))
    dy = int(magnitude * sin(radians(angle)))
    return (x + dx, y - dy)

def getCannyMask(image, threshold):
    """convert image to gray scale run the edge dector returns mask
    """
    res = cv.GetSize(image) 
    gray = cv.CreateImage (res, 8, 1)
    mask = cv.CreateImage (res, 8, 1)
    cv.CvtColor(image, gray, cv.CV_BGR2GRAY)
    cv.Smooth (gray, mask, cv.CV_BLUR, 3, 3, 0)
    cv.Not(gray, mask)
    cv.Canny(gray, mask, threshold, threshold * 3, 3)
    return mask

if __name__ == "__main__":
    import getopt
    import sys
    opts, args = getopt.getopt(sys.argv[1:], 'cf:hn')
    filename = None
    saveCropped = False
    NORTH = 0

    if opts:
        for o,a in opts:
            if o == '-c':
                saveCropped = True
            if o == '-h':
                usage()
                sys.exit(1)
            if o == '-f':
                filename = a
            if o == '-n':
                NORTH = 180
    else:
        usage()
        sys.exit(1)

    try:
        gImage = cv.LoadImage(filename)
        if not gImage:
            print "Error loading image '%s'" % filename
            sys.exit(1)

        m = model(gImage, NORTH)
        ui = controller(m)
        cv.WaitKey (0)
        ofilename = os.path.basename(filename).split('.')[0]
        m.save(ofilename, saveCropped)

        #import site_analysis as sa
        #import numpy as np
        #H = sa.load_horizon_array(magnitudeToTheta(m.polarArray,m.radius))
        #fig1 = sa.calc_solarpath(H.L,H.gamma,H.alpha)
        #fig1.savefig(ofilename+'-path.png')

        #fig1.canvas.draw()
        #data = np.fromstring(fig1.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        #data = data.reshape(fig1.canvas.get_width_height()[::-1] + (3,))
        #ui.test(cv.fromarray(data))
        #cv.WaitKey (0)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise

