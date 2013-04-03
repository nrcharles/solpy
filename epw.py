# coding=utf-8
# Copyright (C) 2012 Nathan Charles
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import geo
import csv
#path to epw data
#default = ~/epw/
path = os.environ['HOME'] + "/epw/"
SPATH = os.path.dirname(os.path.abspath(__file__))

try:
    os.listdir(os.environ['HOME'] + '/epw')
except OSError:
    try:
        os.mkdir(os.environ['HOME'] + '/epw')
    except IOError:
        pass

def basename(USAF):
    files = os.listdir(path)
    for f in files:
        if f.find(USAF) is not -1:
            return f[0:f.rfind('.')]
def epwbasename(USAF):
    f = open(SPATH + '/epwurls.csv')
    for line in f.readlines():
        if line.find(USAF) is not -1:
            return line.rstrip()

def downloadEPW(USAF):
    import os
    url = "http://apps1.eere.energy.gov/buildings/energyplus/weatherdata/4_north_and_central_america_wmo_region_4/1_usa/"
    import urllib2
    import zipfile
    epwfile = epwbasename(USAF)
    u = urllib2.urlopen(url + epwfile)
    localFile = open(path + epwfile, 'w')
    localFile.write(u.read())
    localFile.close()
    epw = zipfile.ZipFile(path + epwfile, 'r')
    epw.extractall(path)
    os.remove(path + epwfile)

def twopercent(USAF):
    #(DB=>MWB) 2%, MaxDB=
    temp = None
    try:
        fin = open('%s/%s.ddy' % (path,basename(USAF)))
        for line in fin:
            m = re.search('2%, MaxDB=(\d+\.\d*)',line)
            if m:
                temp = float(m.groups()[0])
    except:
        pass
    if not temp:
        #(DB=>MWB) 2%, MaxDB=
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
            temp = float(data[2][5].strip())
        except:
            pass
    if temp:
        return temp
    else:
        print "Warning: 2% High Temperature not found, using worst case"
        return 38.0

def minimum(USAF):
    #(DB=>MWB) 2%, MaxDB=
    temp = None
    fin = None
    try:
        fin = open('%s/%s.ddy' % (path,basename(USAF)))
    except:
        print "File not found"
        print "Downloading ..."
        downloadEPW(USAF)
        fin = open('%s/%s.ddy' % (path,basename(USAF)))
    for line in fin:
        m = re.search('Max Drybulb=(-?\d+\.\d*)',line)
        if m:
            temp = float(m.groups()[0])
    if not temp:
        try:
            fin = open('%s/%s.stat' % (path,basename(USAF)))
            for line in fin:
                if line.find('Minimum Dry Bulb') is not -1:
                    return float(line[37:-1].split('\xb0')[0])
        except:
            pass
    if temp:
        return temp
    else:
        print "Warning: Minimum Temperature not found, using worst case"
        return -23.0

class data():
    def __init__(self, USAF):
        #filename = path + USAF + 'TY.csv'
        filename = '%s/%s.epw' % (path,basename(USAF))
        self.csvfile = None
        try:
            self.csvfile = open(filename)
        except:
            print "File not found"
            print "Downloading ..."
            downloadEPW(USAF)
            self.csvfile = open(filename)
        header = ""
        fieldnames = ["Year","Month","Day","Hour","Minute","DS","Drybulb (C)",
                "Dewpoint (C)", "Relative Humidity", "Pressure (Pa)",
                "ETR (W/m^2)","ETRN (W/m^2)","HIR (W/m^2)","GHI (W/m^2)",
                "DNI (W/m^2)","DHI (W/m^2)","GHIL (lux)","DNIL (lux)",
                "DFIL (lux)","Zlum (Cd/m2)","Wdir (degrees)","Wspd (m/s)",
                "Ts cover", "O sky cover","CeilHgt (m)","Present Weather", 
                "Pw codes","Pwat (cm)","AOD (unitless)","Snow Depth (cm)", 
                "Days since snowfall"]
        for i in range(8):
            header +=  self.csvfile.readline()
        self.epw_data = csv.DictReader(self.csvfile,fieldnames=fieldnames)
        print header
        #print self.latitude, self.longitude
    def __iter__(self):
        return self

    def next(self):
        t = self.epw_data.next()
        #sd = t['Date (MM/DD/YYYY)'] +' '+ t['Time (HH:MM)']
        #tz = -5
        #t['utc_datetime'] = strptime(sd,tz)
        #t['datetime'] = strptime(sd)
        return t

    def __del__(self):
        self.csvfile.close()


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Model a PV system. Currently displays annual output and graph')
    #import sys
    #opts, args = getopt.getopt(sys.argv[1:], 'f:h')
    parser.add_argument('-z', '--zipcode',required=True)
    parser.add_argument('-m', '--mname')
    parser.add_argument('-v', '--voltage',type=int,default=600)
    args = vars(parser.parse_args())
    #print args

    try:
        #start program
        zip = args['zipcode']
        maxVoltage = args['voltage']
        stationClass = 1
        name, usaf = geo.closestUSAF( geo.zipToCoordinates(zip), stationClass)
        import modules
        models = modules.model_search(args['mname'].split(' '))
        m = None
        if len(models) > 1:
            for i in models:
                print i
            sys.exit(1)
        elif len(models) == 1:
            print models[0]
            m = modules.moduleJ(models[0])
        else:
            print "Model not found"
            sys.exit(1)

        #= getattr(modules,args['mname'])()
        print "%s USAF: %s" %  (name, usaf)
        print "Minimum Temperature: %s C" % minimum(usaf)
        print "Maximum: %sV" % m.Vmax(minimum(usaf))
        print "Max in series", int(maxVoltage/m.Vmax(minimum(usaf)))
        print "2%% Max: %s C" % twopercent(usaf)
        print "Minimum: %sV" % m.Vmin(twopercent(usaf))


    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
