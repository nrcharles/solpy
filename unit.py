from fisheye import * 

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
