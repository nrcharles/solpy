import os
import tmy3
#path to epw data
#default = ~/epw/
path = os.environ['HOME'] + "/epw/"

def basename(USAF):
    files = os.listdir(path)
    for f in files:
        if f.find(USAF) is not -1:
            return f[0:f.rfind('.')]


def twopercent(USAF):
    try:
        fin = open('%s/%s.stat' % (path,basename(USAF)))
        flag = 0
        data = []
        for line in fin:
            if line.find('2%') is not -1:
                flag = 3
            if flag > 0:
                data.append(line.split('\t'))
                flag -= 1
        return float(data[2][5].strip())
    except:
        pass

def minimum(USAF):
    fin = open('%s/%s.stat' % (path,basename(USAF)))
    for line in fin:
        if line.find('Minimum Dry Bulb') is not -1:
            return float(line[37:-1].split('\xb0')[0])


zip = 27713

name, usaf = tmy3.closestUSAF( tmy3.zipToCoordinates(zip))
print name
print usaf
print basename(usaf)
print minimum(usaf)
print twopercent(usaf)
