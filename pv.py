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
import geo
import numpy as np
import inverters
import modules
import irradiation

class resultSet(object):
    def _init_(self):
        self.timeseries = None
        self.values = None
        self.dailyAve = 0
        self.annualOutput = 0
        self.clippingHours = 0

    def plot(self):
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        fig = plt.figure()
        ax = fig.add_subplot(111)
        months   = mdates.MonthLocator()
        mFormat = mdates.DateFormatter('%b')
        ax.xaxis.set_major_locator(months)
        ax.xaxis.set_major_formatter(mFormat)
        ax.plot(self.timeseries, self.values)
        return fig
        #plt.ion()
        #plt.show()

    def summary(self):
        print "Year 1 Annual Output: %s kWh" % self.annualOutput
        print "Year 1 Daily Average: %s kWh" % self.dailyAve
        print "Inverter hours clipping: %s" % self.clippingHours

def jsonToSystem(jsonDescription):
    """Load a system from a json description"""
    jsonShape = []
    for i in jsonDescription["array"]:
        jsonShape.append(inverters.inverter(i["inverter"], \
                modules.pvArray(modules.moduleJ(i["panel"]),\
                i["series"],i["parallel"])))
    plant = system(jsonShape)
    plant.setZipcode(jsonDescription["zipcode"])
    plant.tilt = jsonDescription["tilt"]
    plant.azimuth = jsonDescription["azimuth"]
    plant.phase = jsonDescription["phase"]
    plant.systemName = jsonDescription["system_name"]
    return plant

def _calc(record):
    insolation = irradiation.irradiation(record,irradiation.place, 
            irradiation.tilt, irradiation.azimuth, irradiation.mname)
    year = 2000
    timestamp = tmy3.normalizeDate(record['datetime'],year)
    drybulb = float(record['Dry-bulb (C)'])
    return timestamp, insolation, drybulb

class system(object):
    def __init__(self,shape):
        #shape is a list of inverters with attached arrays
        self.zipcode = None
        self.place = None
        self.tilt = 32
        self.azimuth = 180
        self.shape = shape
        self.phase = 1
        self.systemName = ""

    def setZipcode(self,zipcode):
        self.zipcode = zipcode
        self.place= geo.zipToCoordinates(self.zipcode)
        self.tz = geo.zipToTZ(self.zipcode)
        self.name, self.usaf = geo.closestUSAF(self.place)

    def model(self,mname = 'p9'):
        from multiprocessing import Pool
        from multiprocessing import cpu_count

        #hack for threading
        #probably should be abstracted some other way
        irradiation.place = self.place
        irradiation.tilt = self.tilt
        irradiation.azimuth = self.azimuth
        irradiation.mname = mname

        pool = Pool(processes=cpu_count())
        insolationOutput = pool.map(_calc,tmy3.data(self.usaf))

        houlyTimeseries = np.array([])
        hourlyInsolation = np.array([])

        dailyTimeseries = np.array([])
        dailyInsolation = np.array([])

        totalOutput = 0
        day = 0
        dailyOutput = 0
        dailyMax = 0
        clip = 0

        for timestamp,insolation,drybulb in insolationOutput:
            houlyTimeseries = np.append(houlyTimeseries,timestamp)
            hourlyInsolation = np.append(hourlyInsolation,insolation)
            output = 0
            for i in self.shape:
                iOut = i.Pac(insolation)
                output += iOut
                if iOut > .999 * i.Paco:
                    clip += 1

            #should probably have a flag for this to output CSV file
            #print timestamp,',', output
            if timestamp.day is day:
                dailyOutput += output
            else:
                dailyMax = max(dailyMax,dailyOutput)
                dailyTimeseries = np.append(dailyTimeseries,timestamp)
                dailyInsolation = np.append(dailyInsolation,dailyOutput/1000)
                dailyOutput = 0
            totalOutput += output
            day = timestamp.day

        rs = resultSet()

        rs.timeseries = dailyTimeseries
        rs.values = dailyInsolation

        rs.clippingHours = clip
        rs.dailyAve = (round(totalOutput/365/10)/100)
        rs.annualOutput = (round(totalOutput/10)/100)

        return rs

    def minRowSpace(self, delta, riseHour=9, setHour=15):
        """Row Space Function"""
        import datetime
        import pysolar
        import math

        riseTime = datetime.datetime(2000,12,22,riseHour-self.tz)
        altitudeRise = pysolar.Altitude(self.place[0],self.place[1],riseTime)
        azimuthRize = pysolar.Azimuth(self.place[0],self.place[1],riseTime)
        shadowLength = delta / math.tan(math.radians(altitudeRise))
        minimumSpaceRise = shadowLength * math.cos(math.radians(azimuthRize))

        setTime = datetime.datetime(2000,12,22,setHour-self.tz)
        altitudeSet = pysolar.Altitude(self.place[0],self.place[1],setTime)
        setAzimuth = pysolar.Azimuth(self.place[0],self.place[1],setTime)
        shadowLength = delta / math.tan(math.radians(altitudeSet))
        minimumSpaceSet = shadowLength * math.cos(math.radians(setAzimuth))

        return max(minimumSpaceRise,minimumSpaceSet)

    def describe(self):
        dp = {}
        di = {}
        for i in set(self.shape):
            di[i.model] = 0
            if hasattr(i.array,'model'):
                dp[i.array.model]=0
            else:
                dp[i.array.panel.model]=0
        for i in self.shape:
            di[i.model] += 1
            if hasattr(i.array,'model'):
                dp[i.array.model]+=1
            else:
                dp[i.array.panel.model]+=i.array.series*i.array.parallel
        return di,dp

