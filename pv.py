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
from tmy3 import *
#import numpy as np
from numpy import *
from inverters import *
from modules import *

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

def model_pv(zipcode, tilt, azimuth, array_shape):
    #import matplotlib.pyplot as plt
    #import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    ts = array([])
    hins = array([])
    dts = array([])
    dins = array([])

    #name, usaf = closestUSAF((38.17323,-75.370674))#Snow Hill,MD
    name, usaf = closestUSAF(zipToCoordinates(17601)) #Lancaster
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
    p = mage250()
    e = m215(p)
    s = pvArray(p,14,2)
    si = sunny6000us(s)
    #print e.Pac(950)
    #print e.I(960,240)
    #print si.Pac(800)
    "Print modeling array and inverter: currently hardcoded to Enphase m215 and Mage 250"

    for d,ins in data(usaf, tilt):
        dt = normalizeDate(d,year)
        ts = append(ts,dt)
        hins = append(hins,ins)
        #output = si.Pac(ins)
        output = e.Pac(ins) * array_shape 
        if d.day is day:
            do += output
        else:
            dmax = max(dmax,do)
            dts = append(dts,dt)
            dins = append(dins,do/1000)
            do = 0
        t += output
        day = d.day
    ax.plot(dts,dins)
    plt.savefig('pv_output_%s.png' % zipcode)

    print t/1000
    print t/(1000*365.0)

if __name__ == "__main__":
    import argparse
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
        model_pv(args['zipcode'], args['tilt'], args['azimuth'], args['shape'])

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
