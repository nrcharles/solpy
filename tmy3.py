import csv
import datetime
import os
import math
import irradiation

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

def normalizeDate(tmyDate, year):
    """change TMY3 date to an arbitrary year"""
    Y = year
    M = tmyDate.month
    D = tmyDate.day -1
    h = tmyDate.hour
    m = 0
    #hack to get around 24:00 notation
    if M is 1 and D is 0 and h is 0:
        Y = Y + 1
    return datetime.datetime(Y, M, 1) + datetime.timedelta(days=D, hours=h, minutes=m)

class data():
    def __init__(self, USAF, tilt = 0.0):
        filename = path + USAF + 'TY.csv'
        self.csvfile = open(filename)
        header =  self.csvfile.readline().split(',')
        self.tmy_data = csv.DictReader(self.csvfile)
        self.latitude = float(header[4])
        self.longitude = float(header[5])
        print self.latitude, self.longitude
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
        etr = int(i['ETR (W/m^2)'])

        d = strptime(sd)

        if self.tilt > 0:
            #ghi, dni, dhi = radiation
            #calculate total radiation
            gth = irradiation.tilt(self.latitude, self.longitude, d, (etr, ghi, dni, dhi), self.tilt)
            return d, gth
        else:
            return d, ghi

    def __del__(self):
        self.csvfile.close()

def closestUSAF(place):
    latitude,longitude = place
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

def zipToCoordinates(zip):
    index = open('zipcode.csv')
    #read over license
    headerLen = 31
    for i in range(headerLen):
        index.readline()
    index_data = csv.DictReader(index)
    for i in index_data:
        if int(i['zip']) == zip:
            return float(i['latitude']),float( i['longitude'])

if __name__ == "__main__":
    tilt = 50.0
    #import matplotlib.pyplot as plt
    from inverters import m215
    from modules import mage250

    p = mage250()
    e = m215(p)
    #s = ee.junction([(ee.wire(3,"8"),e)])
    #s1 = ee.junction(s,[(ee.wire(3,"8"),e)])
    #print "s1"
    #print s1.a()

    #name, usaf = closestUSAF((40,-76.2)) #Lancaster
    name, usaf = closestUSAF(zipToCoordinates(17601)) #Lancaster
    t = 0
    for d,ins in data(usaf, tilt):
        output = ins
        t += output

    print t/1000
    print t/(1000*365.0)
