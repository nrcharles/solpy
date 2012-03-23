from fisheye import * 
filename = 'out2LR.png'
gImage = cv.LoadImage(filename)
if not gImage:
    print "Error loading image '%s'" % filename
    sys.exit(1)

m = model(gImage, 0)
m.center = (337, 347)
m.threshold = 20
#m.cardinalOffset = 20
m.cardinalOffset = 40
m.radius = 302

m.calculate()

cv.WaitKey (0)
ofilename = os.path.basename(filename).split('.')[0]
m.save(ofilename, True)

import site_analysis as sa
import numpy as np

H = sa.load_horizon_array(magnitudeToTheta(m.polarArray,m.radius))
fig1 = sa.calc_solarpath(H.L,H.gamma,H.alpha)
fig1.savefig(ofilename+'-path.png')
fig1.canvas.draw()
# Now we can save it to a numpy array.
data = np.fromstring(fig1.canvas.tostring_rgb(), dtype=np.uint8, sep='')
data = data.reshape(fig1.canvas.get_width_height()[::-1] + (3,))

#ui.test(cv.fromarray(data))
"""
print "4,5 - 0 degrees", addVector((5,5),(0,1)) 
print "? - 45 degrees", addVector((5,5),(45,2)) 
print "5,7 - 90 degrees", addVector((5,5),(90,2)) 
print "8,5 - 180 degrees", addVector((5,5),(180,3)) 
print "5,1 - 270 degrees", addVector((5,5),(270,4)) 
print "0,5 - 360 degrees", addVector((5,5),(360,5)) 

#drawVector
vectorA = []
for i in range(0,360):
    vectorA.append((i,i))
for vector in vectorA:
    print vector,addVector((360,360),vector)
spiral = cv.CreateImage ((360*2,360*2), 8, 3)
drawVectors(spiral,(360,360),vectorA)
cv.Line(spiral,(0,0),(360,360),(255,255,255))
cv.NamedWindow("spiral")
cv.ShowImage("spiral",spiral)
cv.WaitKey (0)

render = cv.CreateImage((360*2,360*2), 8, 3)
cv.Zero(render)
for i in range(360):
    cv.Line(render, addVector((360,360),(i-1,i+1)), addVector((360,360),(i,i+2)) ,(255,0,0),2)
    #x,y = cv.GetSize(render)
    #render[x-i-1,i] = (255,255,255)
    #x,y = addVector((360,360),

cv.ShowImage("spiral",render)
cv.WaitKey (0)

radius = 360
cv.NamedWindow("temp")
rArray = distanceToEdge(render,(360,358),radius)
render = drawVectors(render,(360,358),rArray)
print rArray
cv.ShowImage("spiral",render)
cv.WaitKey (0)

#edgeTo...
"""
