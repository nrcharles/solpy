import csv
import datetime
import os
import math
import radiation

#path to tmy3 data
#default = ~/tmp3/
path = os.environ['HOME'] + "/tmy3/"

def strptime(string):
    #necessary because of 24:00 end of day labeling
    Y = int(string[6:10])
    M = int(string[0:2])
    D = int(string[3:5])
    h = int(string[11:13])
    m = int(string[14:16])
    return datetime.datetime(Y, M, D) + datetime.timedelta(hours=h, minutes=m)

class data():
    def __init__(self, USAF, tilt = 0.0):
        filename = path + USAF + 'TY.csv'
        self.csvfile = open(filename)
        header =  self.csvfile.readline().split(',')
        self.tmy_data = csv.DictReader(self.csvfile)
        self.latitude = float(header[4])
        self.longitude = float(header[5])
        self.tilt = tilt 
    def __iter__(self):
        return self
    def next(self):
        i = self.tmy_data.next()
        #['Date (MM/DD/YYYY)', 'Time (HH:MM)'
        sd = i['Date (MM/DD/YYYY)'] +' '+ i['Time (HH:MM)']
        ghi = int(i['GHI (W/m^2)'])
        dhi = int(i['DHI (W/m^2)'])
        dni = int(i['DNI (W/m^2)'])
        #etrn = i['ETR (W/m^2)']

        d = strptime(sd)

        if self.tilt > 0:
            #ghi, dni, dhi = radiation
            #calculate total radiation
            gth = radiation.tilt(self.latitude, self.longitude, d, (ghi, dni, dhi), self.tilt)
            return d, gth
        else:
            return d, ghi

    def __del__(self):
        self.csvfile.close()

def closestUSAF(latitude,longitude):
    index = open(path + 'TMY3_StationsMeta.csv')
    index_data = csv.DictReader(index)
    d1 = 9999
    name = ''
    usaf = ''
    for i in index_data:
        d2 = math.sqrt(math.pow((float(i['Latitude']) - latitude),2) +math.pow((float(i['Longitude']) - longitude),2))
        if d2 < d1:
            d1 = d2
            name = i['Site Name']
            usaf = i['USAF']
    index.close()
    return name, usaf

if __name__ == "__main__":
    x = 40.22
    y = -76.85
    tilt = 39.0
    #name, usaf = closestUSAF(40,-76.2) #Lancaster
    name, usaf = closestUSAF(39.867,-75.233)#Philadelphia
    #name, usaf = closestUSAF(40.22,-76.85) #Harrisburg
    #name, usaf = closestUSAF(39.88,-75.25)
    #name, usaf = closestUSAF(42.1649,-72.779)
    t = 0
    l = 0
    #derate = dc_ac_derate()
    for d,ins in data(usaf, tilt):
        #print d, dni, int(dni) * .770
        #t += (ins + l)/2.0
        t += ins #tiltAdjust(x,y,d,ins) #* derate
        l = ins
    print t/1000
    print t/(1000*365.0)
    print "print should be ~ 4.57 at 39.9 degree tilt"
