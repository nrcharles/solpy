# coding=utf-8
# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.
"""EPW weather data file wrapper"""

import os
import re
import csv
import urllib2
import zipfile
#path to epw data
#default = ~/epw/
EPW_PATH = os.environ['HOME'] + "/epw/"
SPATH = os.path.dirname(os.path.abspath(__file__))

try:
    os.listdir(os.environ['HOME'] + '/epw')
except OSError:
    try:
        os.mkdir(os.environ['HOME'] + '/epw')
    except IOError:
        pass

def basename(usaf):
    """usaf basename"""
    files = os.listdir(EPW_PATH)
    for filen in files:
        if filen.find(usaf) is not -1:
            return filen[0:filen.rfind('.')]

def epwbasename(usaf):
    """find epw url basename"""
    urlfile = open(SPATH + '/epwurls.csv')
    for line in urlfile.readlines():
        if line.find(usaf) is not -1:
            return line.rstrip()

def download_epw(usaf):
    """download epw data for usaf"""
    url = ("http://apps1.eere.energy.gov/buildings/energyplus/weatherdata/" \
            "4_north_and_central_america_wmo_region_4/1_usa/")
    epwfile = epwbasename(usaf)
    epwdata = urllib2.urlopen(url + epwfile)
    local_file = open(EPW_PATH + epwfile, 'w')
    local_file.write(epwdata.read())
    local_file.close()
    epw = zipfile.ZipFile(EPW_PATH + epwfile, 'r')
    epw.extractall(EPW_PATH)
    os.remove(EPW_PATH + epwfile)

def twopercent(usaf):
    """two percent Temperature"""
    #(DB=>MWB) 2%, MaxDB=
    temp = None
    try:
        fin = open('%s/%s.ddy' % (EPW_PATH, basename(usaf)))
        for line in fin:
            value = re.search("""2%, MaxDB=(\\d+\\.\\d*)""", line)
            if value:
                temp = float(value.groups()[0])
    except IOError:
        pass

    if not temp:
        #(DB=>MWB) 2%, MaxDB=
        try:
            fin = open('%s/%s.stat' % (EPW_PATH, basename(usaf)))
            flag = 0
            tdata = []
            for line in fin:
                if line.find('2%') is not -1:
                    flag = 3
                if flag > 0:
                    tdata.append(line.split('\t'))
                    flag -= 1
            temp = float(tdata[2][5].strip())
        except IOError:
            pass
    if temp:
        return temp
    else:
        print "Warning: 2% High Temperature not found, using worst case"
        return 38.0

def minimum(usaf):
    """minimum temperature"""
    #(DB=>MWB) 2%, MaxDB=
    temp = None
    fin = None
    try:
        fin = open('%s/%s.ddy' % (EPW_PATH, basename(usaf)))
    except IOError:
        print "File not found"
        print "Downloading ..."
        download_epw(usaf)
        fin = open('%s/%s.ddy' % (EPW_PATH, basename(usaf)))
    for line in fin:
        value = re.search('Max Drybulb=(-?\\d+\\.\\d*)', line)
        if value:
            temp = float(value.groups()[0])
    if not temp:
        try:
            fin = open('%s/%s.stat' % (EPW_PATH, basename(usaf)))
            for line in fin:
                if line.find('Minimum Dry Bulb') is not -1:
                    return float(line[37:-1].split('\xb0')[0])
        except IOError:
            pass
    if temp:
        return temp
    else:
        print "Warning: Minimum Temperature not found, using worst case"
        return -23.0

class data(object):
    """EPW weather generator"""
    def __init__(self, usaf):
        #filename = path + usaf + 'TY.csv'
        filename = '%s/%s.epw' % (EPW_PATH, basename(usaf))
        self.csvfile = None
        try:
            self.csvfile = open(filename)
        except IOError:
            print "File not found"
            print "Downloading ..."
            download_epw(usaf)
            self.csvfile = open(filename)
        fieldnames = ["Year", "Month", "Day", "Hour", "Minute", "DS", \
                "Drybulb (C)", "Dewpoint (C)", "Relative Humidity", \
                "Pressure (Pa)", "ETR (W/m^2)", "ETRN (W/m^2)", "HIR (W/m^2)", \
                "GHI (W/m^2)", "DNI (W/m^2)", "DHI (W/m^2)", "GHIL (lux)", \
                "DNIL (lux)", "DFIL (lux)", "Zlum (Cd/m2)", "Wdir (degrees)", \
                "Wspd (m/s)", "Ts cover", "O sky cover", "CeilHgt (m)", \
                "Present Weather", "Pw codes", "Pwat (cm)", "AOD (unitless)", \
                "Snow Depth (cm)", "Days since snowfall"]
        header = ""
        for i in range(8):
            header += self.csvfile.readline()
        self.epw_data = csv.DictReader(self.csvfile, fieldnames=fieldnames)
        #print self.latitude, self.longitude
    def __iter__(self):
        return self

    def next(self):
        record = self.epw_data.next()
        #sd = t['Date (MM/DD/YYYY)'] +' '+ t['Time (HH:MM)']
        #tz = -5
        #t['utc_datetime'] = strptime(sd,tz)
        #t['datetime'] = strptime(sd)
        return record 

    def __del__(self):
        self.csvfile.close()


def hdd(usaf, base=18):
    """Heating degree days in C"""
    total = 0.0
    for record in data(usaf):
        delta = base - float(record['Drybulb (C)'])
        if delta > 0:
            total += delta
    return round(total/24.0, 1)

def cdd(usaf, base=18):
    """cooling degree days in C"""
    total = 0.0
    for record in data(usaf):
        delta = float(record['Drybulb (C)']) - base
        if delta > 0:
            total += delta
    return round(total/24.0, 1)


if __name__ == "__main__":
    import argparse
    import sys
    from solpy import geo
    from solpy import modules
    PARSER = argparse.ArgumentParser(description='Model a PV system. '\
            'Currently displays annual output and graph')
    #import sys
    #opts, ARGS = getopt.getopt(sys.argv[1:], 'f:h')
    PARSER.add_argument('-z', '--zipcode', required=True)
    PARSER.add_argument('-m', '--mname')
    PARSER.add_argument('-v', '--voltage', type=int, default=600)
    ARGS = vars(PARSER.parse_args())
    #print ARGS

    try:
        #start program
        ZIPCODE = ARGS['zipcode']
        MAX_VOLTAGE = ARGS['voltage']
        STATION_CLASS = 1
        NAME, USAF = geo.closest_usaf(geo.zip_coordinates(ZIPCODE), \
                STATION_CLASS)
        print "%s usaf: %s" %  (NAME, USAF)
        print "Minimum Temperature: %s C" % minimum(USAF)
        print "2%% Max: %s C" % twopercent(USAF)
        print "Heating Degree days: %s" %  hdd(USAF)
        print "Cooling Degree days: %s" %  cdd(USAF)
        if ARGS['mname']:
            print ""
            MODELS = modules.model_search(ARGS['mname'].split(' '))
            MODULE = None
            if len(MODELS) > 1:
                for i in MODELS:
                    print i
                sys.exit(1)
            elif len(MODELS) == 1:
                print MODELS[0]
                MODULE = modules.Module(MODELS[0])
            else:
                print "Model not found"
                sys.exit(1)

            print "Maximum: %sV" % MODULE.v_max(minimum(USAF))
            print "Max in series", int(MAX_VOLTAGE/MODULE.v_max(minimum(USAF)))
            print "Minimum: %sV" % MODULE.v_min(twopercent(USAF))

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
