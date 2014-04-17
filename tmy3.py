import csv
# Copyright (C) 2012 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

import datetime
import os
import irradiation

#path to tmy3 data
#default = ~/tmp3/
path = os.environ['HOME'] + "/tmy3/"

SRC_PATH = os.path.dirname(os.path.abspath(__file__))

try:
    os.listdir(os.environ['HOME'] + '/tmy3')
except OSError:
    try:
        os.mkdir(os.environ['HOME'] + '/tmy3')
    except IOError:
        pass

def tmybasename(USAF):
    f = open(SRC_PATH + '/tmy3urls.csv')
    for line in f.readlines():
        if line.find(USAF) is not -1:
            return line.rstrip().partition(',')[0]

def downloadTMY(USAF):
    url = "http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3/"
    import urllib2
    tmyfile = tmybasename(USAF)
    u = urllib2.urlopen(url + tmyfile)
    localFile = open(path + tmyfile, 'w')
    localFile.write(u.read())
    localFile.close()

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
        self.csvfile = None
        try:
            self.csvfile = open(filename)
        except:
            print "File not found"
            print "Downloading ..."
            downloadTMY(USAF)
            self.csvfile = open(filename)
        header =  self.csvfile.readline().split(',')
        self.tmy_data = csv.DictReader(self.csvfile)
        self.latitude = float(header[4])
        self.longitude = float(header[5])
        self.tz = float(header[3])
        #print header[1]
        #print self.latitude, self.longitude
    def __iter__(self):
        return self

    def next(self):
        t = self.tmy_data.next()
        sd = t['Date (MM/DD/YYYY)'] +' '+ t['Time (HH:MM)']
        t['utc_datetime'] = strptime(sd,self.tz)
        t['datetime'] = strptime(sd)
        return t

    def __del__(self):
        self.csvfile.close()

def total(usaf, field='GHI (W/m^2)'):
    t = 0
    usafdata = data(usaf)
    for r in usafdata:
        t += float(r[field])
    return t/1000

if __name__ == "__main__":
    import geo
    tilt = 32.0
    #import matplotlib.pyplot as plt
    #place = zipToCoordinates('17601) #Lancaster
    place = geo.zipToCoordinates('19113') #Philadelphia
    name, usaf = geo.closestUSAF(place)
    t = 0
    for r in data(usaf):
        output = irradiation.irradiation(r,place,t=tilt)
        t += output

    print t/1000
    print t/(1000*365.0)
    print total(usaf)
