import csv
import datetime
import os
import math
import irradiation
import solar
import pysolar as s

#path to tmy3 data
#default = ~/tmp3/
path = os.environ['HOME'] + "/tmy3/"

def strptime(string, tz=0):
    #necessary because of 24:00 end of day labeling
    Y = int(string[6:10])
    M = int(string[0:2])
    D = int(string[3:5])
    h = int(string[11:13])
    m = int(string[14:16])
    return datetime.datetime(Y, M, D) + datetime.timedelta(hours=h, minutes=m) - datetime.timedelta(hours=tz)

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
    def __init__(self, USAF):
        filename = path + USAF + 'TY.csv'
        self.csvfile = open(filename)
        header =  self.csvfile.readline().split(',')
        self.tmy_data = csv.DictReader(self.csvfile)
        self.latitude = float(header[4])
        self.longitude = float(header[5])
        print header[1]
        print self.latitude, self.longitude
    def __iter__(self):
        return self

    def next(self):
        t = self.tmy_data.next()
        sd = t['Date (MM/DD/YYYY)'] +' '+ t['Time (HH:MM)']
        tz = -5
        t['utc_datetime'] = strptime(sd,tz)
        t['datetime'] = strptime(sd)
        return t

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

def zipToTZ(zip):
    index = open('zipcode.csv')
    #read over license
    headerLen = 31
    for i in range(headerLen):
        index.readline()
    index_data = csv.DictReader(index)
    for i in index_data:
        if int(i['zip']) == zip:
            return int(i['timezone'])

if __name__ == "__main__":
    tilt = 32.0
    #import matplotlib.pyplot as plt
    #place = zipToCoordinates(17601) #Lancaster
    place = zipToCoordinates(19113) #Philadelphia
    name, usaf = closestUSAF(place)
    t = 0
    for r in data(usaf):
        output = irradiation.irradiation(r,place,tilt)
        t += output

    print t/1000
    print t/(1000*365.0)
