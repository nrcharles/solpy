"""TMY3 data set library: thin wrapper around csv files"""
import csv
# Copyright (C) 2012 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

import datetime
import os
from solpy import irradiation

#path to tmy3 data
#default = ~/tmp3/
TMY_PATH = os.environ['HOME'] + "/tmy3/"

SRC_PATH = os.path.dirname(os.path.abspath(__file__))

try:
    os.listdir(os.environ['HOME'] + '/tmy3')
except OSError:
    try:
        os.mkdir(os.environ['HOME'] + '/tmy3')
    except IOError:
        pass

def tmybasename(usaf):
    """get basename for USAF base"""
    url_file = open(SRC_PATH + '/tmy3urls.csv')
    for line in url_file.readlines():
        if line.find(usaf) is not -1:
            return line.rstrip().partition(',')[0]

def download_tmy(usaf):
    """download TMY3 file"""
    url = "http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3/"
    import urllib2
    tmybase = tmybasename(usaf)
    tmydata = urllib2.urlopen(url + tmybase)
    local_file = open(TMY_PATH + tmybase, 'w')
    local_file.write(tmydata.read())
    local_file.close()

def strptime(string, timezone=0):
    """custom strptime - necessary because of 24:00 end of day labeling"""
    year = int(string[6:10])
    month = int(string[0:2])
    day = int(string[3:5])
    hour = int(string[11:13])
    minute = int(string[14:16])
    return datetime.datetime(year, month, day) + \
            datetime.timedelta(hours=hour, minutes=minute) - \
            datetime.timedelta(hours=timezone)

def normalize_date(tmy_date, year):
    """change TMY3 date to an arbitrary year"""
    month = tmy_date.month
    day = tmy_date.day - 1
    hour = tmy_date.hour
    #hack to get around 24:00 notation
    if month is 1 and day is 0 and hour is 0:
        year = year + 1
    return datetime.datetime(year, month, 1) + \
            datetime.timedelta(days=day, hours=hour, minutes=0)

class data(object):
    """TMY3 iterator"""
    def __init__(self, usaf):
        filename = TMY_PATH + usaf + 'TY.csv'
        self.csvfile = None
        try:
            self.csvfile = open(filename)
        except IOError:
            print "File not found"
            print "Downloading ..."
            download_tmy(usaf)
            self.csvfile = open(filename)
        header = self.csvfile.readline().split(',')
        self.tmy_data = csv.DictReader(self.csvfile)
        self.latitude = float(header[4])
        self.longitude = float(header[5])
        self.tz = float(header[3])
        #print header[1]
        #print self.latitude, self.longitude
    def __iter__(self):
        return self

    def next(self):
        """iterator handle"""
        record = self.tmy_data.next()
        _sd = record['Date (MM/DD/YYYY)'] +' '+ record['Time (HH:MM)']
        record['utc_datetime'] = strptime(_sd, self.tz)
        record['datetime'] = strptime(_sd)
        return record

    def __del__(self):
        self.csvfile.close()

def total(usaf, field='GHI (W/m^2)'):
    """total annual insolation, defaults to GHI"""
    running_total = 0
    usafdata = data(usaf)
    for record in usafdata:
        running_total += float(record[field])
    return running_total/1000.

if __name__ == "__main__":
    from solpy import geo
    TILT = 32.0
    #import matplotlib.pyplot as plt
    #place = zipToCoordinates('17601) #Lancaster
    PLACE = geo.zip_coordinates('19113') #Philadelphia
    DUMMY, USAF = geo.closest_usaf(PLACE)
    TOTAL_INS = 0
    for i in data(USAF):
        output = irradiation.irradiation(i, PLACE, t=TILT)
        TOTAL_INS += output

    print TOTAL_INS/1000
    print TOTAL_INS/(1000*365.0)
    print total(USAF)
