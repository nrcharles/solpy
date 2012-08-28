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
from inverters import *
from modules import *
import irradiation

default = [m215(mage250())]

def _calc(record):
    d = record['datetime']
    ins = irradiation.irradiation(record,irradiation.place, irradiation.tilt,
            irradiation.azimuth, irradiation.mname)
    year = 2000
    dt = tmy3.normalizeDate(d,year)
    return dt, ins

class system(object):
    def __init__(self,shape):
        #shape is a list of inverters with attached arrays
        self.zipcode = None
        self.place = None
        self.tilt = 32
        self.azimuth = 180
        self.shape = shape

    def setZipcode(self,zipcode):
        self.zipcode = zipcode
        #name, usaf = closestUSAF((38.17323,-75.370674))#Snow Hill,MD
        self.place= tmy3.zipToCoordinates(self.zipcode)
        self.name, self.usaf = tmy3.closestUSAF(self.place)

    def model(self,mname = 'p9'):
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from multiprocessing import Pool
        from multiprocessing import cpu_count
        import epw

        print self.shape[0].array.Vmax(epw.minimum(self.usaf))
        print self.shape[0].array.Vmin(epw.twopercent(self.usaf))

        #hack for threading
        #probably should be abstracted some other way
        irradiation.place = self.place
        irradiation.tilt = self.tilt
        irradiation.azimuth = self.azimuth
        irradiation.mname = mname

        pool = Pool(processes=cpu_count())
        insOutput = pool.map(_calc,tmy3.data(self.usaf))

        #create graph
        ts = np.array([])
        hins = np.array([])
        dts = np.array([])
        dins = np.array([])
        t = 0
        l = 0
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

        for dt,ins in insOutput:
            ts = np.append(ts,dt)
            hins = np.append(hins,ins)
            output = 0
            for i in self.shape:
                output += i.Pac(ins)
            if dt.day is day:
                do += output
            else:
                dmax = max(dmax,do)
                dts = np.append(dts,dt)
                dins = np.append(dins,do/1000)
                do = 0
            t += output
            day = dt.day
        ax.plot(dts,dins)

        print "Annual Output: %s kWh" % (round(t/10)/100)
        print "Daily Average: %s kWh" % (round(t/365/10)/100)
        return fig
