#!/usr/bin/env python
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
import tmy3
import numpy as np
#from numpy import *
from inverters import *
from modules import *
import irradiation
import matplotlib

default = [m215(mage250())]

def usage():
    """Prints usage options when called with no arguments or with invalid arguments
    """
    print """usage: [options]
   -a    current
   -l    length
   -p    phase [default 1]
   -v    voltage [default 240]
   -s    size
   -h    help
    """

class system(object):
    def __init__(self,shape):
        #shape is a list of inverters with attached arrays
        self.zipcode = None
        self.place = None
        self.tilt = 0
        self.azimuth = 180
        self.shape = shape 

    def setZipcode(self,zipcode):
        self.zipcode = zipcode
        #name, usaf = closestUSAF((38.17323,-75.370674))#Snow Hill,MD
        self.place= tmy3.zipToCoordinates(self.zipcode)
        self.name, self.usaf = tmy3.closestUSAF(self.place)

    def model(self,mname = 'lj'):
        #import matplotlib.pyplot as plt
        #import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        ts = np.array([])
        hins = np.array([])
        dts = np.array([])
        dins = np.array([])

        t = 0
        l = 0
        #derate = dc_ac_derate()
        day = 0
        do = 0
        dmax = 0
        fig = plt.figure()
        ax = fig.add_subplot(111)
        year = 2000
        months   = mdates.MonthLocator()
        mFormat = mdates.DateFormatter('%b')
        ax.xaxis.set_major_locator(months)
        ax.xaxis.set_major_formatter(mFormat)

        for record in tmy3.data(self.usaf):
            d = record['datetime']
            ins = irradiation.irradiation(record,self.place,self.tilt,self.azimuth,mname)
            dt = tmy3.normalizeDate(d,year)
            ts = np.append(ts,dt)
            hins = np.append(hins,ins)
            #output = si.Pac(ins)
            output = 0 
            for i in self.shape:
                output += i.Pac(ins)
            if d.day is day:
                do += output
            else:
                dmax = max(dmax,do)
                dts = np.append(dts,dt)
                dins = np.append(dins,do/1000)
                do = 0
            t += output
            day = d.day
        ax.plot(dts,dins)

        print t/1000
        print t/(1000*365.0)
        return plt
if __name__ == "__main__":
    import argparse
    matplotlib.use('Agg')
    parser = argparse.ArgumentParser(description='Model a PV system. Currently displays annual output and graph')
    #import sys
    #opts, args = getopt.getopt(sys.argv[1:], 'f:h')
    parser.add_argument('-o', '--output')
    parser.add_argument('-z', '--zipcode',type=int)
    parser.add_argument('-t', '--tilt', type=float)
    parser.add_argument('-s', '--shape', type=int, help='Array Shape, currently number of microinverters', default=1)
    parser.add_argument('-a', '--azimuth',type=float, default=180,help='array azimuth')
    args = vars(parser.parse_args())
    #print args

    try:
        #start program
        p = mage250()
        e = m215(p)
        s = pvArray(p,14,2)
        si = sunny6000us(s)
        array = [e] * args['shape']
        #print e.Pac(950)
        #print e.I(960,240)
        #print si.Pac(800)
        "Print modeling array and inverter: currently hardcoded to Enphase m215 and Mage 250"
        a = system(array)
        a.setZipcode(args['zipcode'])
        a.tilt = args['tilt']
        a.azimuth =  args['azimuth']
        graph = a.model()
        graph.savefig('pv_output_%s.png' % args['zipcode'])

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
