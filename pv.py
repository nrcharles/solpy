#!/usr/bin/env python
# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.
"""
Photovoltaic System Performance Monitoring

"""

import tmy3
import geo
import numpy as np
import inverters
import modules
import irradiation
import json
import math
import datetime
import forecast
import noaa
import pathfinder
from collections import Counter
from geopy import geocoders

class resultSet(object):
    def _init_(self):
        self.timeseries = None
        self.values = None
        self.dailyAve = 0
        self.annualOutput = 0
        self.clippingHours = 0

    def dump(self):
        return (self.timeseries, self.values)
    def dumps(self):
        return ([int((i - datetime.datetime(1970,1,1)).total_seconds()) \
                for i in self.timeseries],self.values)

    def plotd(self):
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

    def plot(self):
        import matplotlib.pyplot as plt
        total = self.hourlyValues
        a = []
        for i in range(0,len(self.hourlyValues),24):
            a.append(self.hourlyValues[i:i+23])
        data = np.array(a)
        data = np.rot90(data)
        fig = plt.figure()
        ax = fig.add_subplot(111)#plt.subplots()
        ax.set_xlim([0,365])
        ax.set_ylim([0,22])
        ax.set_ylabel('Hour of Day')
        ax.set_xlabel('Day of Year')
        heatmap = ax.imshow(data,aspect='auto',cmap=plt.cm.OrRd)
        txt =  "Year 1 Output: %s KWh" % round(sum(total)/1000,1)
        cbar = fig.colorbar(heatmap) 
        cbar.set_label('Output (W)')
        ax.annotate(txt, xy=(10,3))
        plt.tight_layout()
        return fig

    def summary(self):
        print "Year 1 Annual Output: %s kWh" % self.annualOutput
        print "Year 1 Daily Average: %s kWh" % self.dailyAve
        print "Inverter hours clipping: %s" % self.clippingHours

def fileToSystem(filename):
    """Load a system from a json file"""
    try:
        return jsonToSystem(json.loads(open(filename).read()))

    except:
        print "Error: file corrupt or not found:"


def jsonToSystem(jsonDescription):
    """Load a system from a json description"""
    #todo: this is getting unweildy should probably be refactored
    jsonShape = []
    orientations = []
    for i in jsonDescription["array"]:
        o = {}
        scale = 1
        if "scale" in i:
            scale = i["scale"]
        if "quantity" in i:
            scale = i["quantity"]
        if "shape" in i:
            shape = i["shape"]
        elif "series" in i:
            shape = [{"series":i["series"],
                    "parallel":i["parallel"] or 1}]
        else:
            shape = [{'series':1}]

        if "tilt" in i:
            o["tilt"] = i["tilt"]
        else:
            o["tilt"] = jsonDescription["tilt"]
        if "azimuth" in i:
            o["azimuth"] = i["azimuth"]
        else:
            o["azimuth"] = jsonDescription["azimuth"]
        orientations.append(o)

        block = inverters.inverter(i["inverter"], \
                modules.pvArray(modules.module(i["panel"]),\
                shape),(o["azimuth"],o["tilt"]))
                #i["series"],i["parallel"]))
        if "derate" in i:
                block.derate = i["derate"]
        jsonShape += [ block ] * scale
    plant = system(jsonShape)
    plant.setZipcode(jsonDescription["zipcode"])
    if "address" in jsonDescription:
        plant.address = jsonDescription["address"]
    try:
        g = geocoders.GoogleV3()
        place, (lat, lng) = g.geocode(plant.address)
        plant.place = lat,lng
        #print "%s, %s Geolocated" % plant.place
    except:
        pass
        #print "%s, %s location from zipcode" % plant.place
    #print orientations
    #print set(["%s_%s" % (i['azimuth'],i['tilt']) for i in orientations])
    if len(set(["%s_%s" % (i['azimuth'],i['tilt']) for i in orientations])) > 1:
        print "WARNING: multiple tilts not implimented"
        plant.tilt = o[0]["tilt"]
        plant.azimuth = o[0]["azimuth"]
    elif ("tilt" in jsonDescription and "azimuth" in jsonDescription):
        plant.tilt = jsonDescription["tilt"]
        plant.azimuth = jsonDescription["azimuth"]
    else:
        "maybe incomplete"
        plant.tilt = orientations[0]["tilt"]
        plant.azimuth = orientations[0]["azimuth"]
    if 'shade' in jsonDescription:
        plant.hourlyShade = pathfinder.hourly(jsonDescription['shade'])

    plant.phase = jsonDescription["phase"]
    plant.voltage = jsonDescription["voltage"]
    plant.systemName = jsonDescription["system_name"]
    return plant

def _calc(record):
    properties,record = record
    horizon = None
    insolation = irradiation.irradiation(record, properties['place'], \
            horizon, properties['tilt'], properties['azimuth'], \
            properties['modelName'])
    year = 2000
    timestamp = tmy3.normalizeDate(record['datetime'],year)
    return timestamp, insolation, record

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
        self.clip = 0

    def setZipcode(self,zipcode):
        self.zipcode = zipcode
        self.place= geo.zipToCoordinates(self.zipcode)
        self.tz = geo.zipToTZ(self.zipcode)
        self.name, self.usaf = geo.closestUSAF(self.place)

    def model(self,modelName = 'p9',singleThread=False):

        #hack for threading
        #probably should be abstracted some other way
        properties = {}
        properties['place'] = self.place
        properties['tilt'] = self.tilt
        properties['azimuth'] = self.azimuth
        properties['modelName'] = modelName

        if singleThread:
            insolationOutput = map(_calc,[(properties, i) for i in tmy3.data(self.usaf)])
        else:
            from multiprocessing import Pool
            from multiprocessing import cpu_count
            pool = Pool(processes=cpu_count())
            #still a hack
            insolationOutput = pool.map(_calc,[(properties, i) for i in tmy3.data(self.usaf)])
            pool.close()

        houlyTimeseries = np.array([])
        hourlyInsolation = np.array([])

        dailyTimeseries = np.array([])
        dailyInsolation = np.array([])

        totalOutput = 0
        day = 0
        dailyOutput = 0
        dailyMax = 0
        clip = 0

        #cache
        NOLOAD = self.Pac(0)

        for timestamp,insolation,record in insolationOutput:
            if insolation > 0:
                houlyTimeseries = np.append(houlyTimeseries,timestamp)
                tAmb = float(record['Dry-bulb (C)'])
                windSpd = float(record['Wspd (m/s)'])
                tModule = .945*tAmb +.028*insolation - 1.528*windSpd + 4.3
                if hasattr(self,'hourlyShade'):
                    insolation = insolation * self.hourlyShade.shade(timestamp)
                output = self.Pac(insolation,tModule)
            else:
                output = NOLOAD
            #output = self.Pac(insolation)
            hourlyInsolation = np.append(hourlyInsolation,output)

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
        rs.htimeseries = houlyTimeseries
        rs.hourlyValues = hourlyInsolation

        rs.clippingHours = clip
        rs.dailyAve = (round(totalOutput/365/10)/100)
        rs.annualOutput = (round(totalOutput/10)/100)

        return rs

    def Pac(self, ins, tCell = 25):
        output = 0
        for i in self.shape:
            iOut = i.Pac(ins, tCell)
            output += iOut
            if iOut > .999 * i.Paco:
                self.clip += 1
        return output

    def Pdc(self, ins, tCell = 25):
        dc = 0
        for i in self.shape:
            dc += i.array.output(ins,tCell)
        return dc

    def solstice(self, hour):
        #position on winter soltice (Dec 21)
        import ephem
        o = ephem.Observer()
        o.date = '2000/12/21 %s:00:00' % (hour - self.tz)
        o.lat = math.radians(self.place[0])
        o.lon = math.radians(self.place[1])
        az = ephem.Sun(o).az
        alt = ephem.Sun(o).alt

        return alt, az

    def minRowSpace(self, delta, riseHour=9, setHour=15):
        """Row Space Function"""
        altitudeRise,azimuthRise = self.solstice(riseHour)
        shadowLength = delta / math.tan(altitudeRise)
        minimumSpaceRise = shadowLength * abs(math.cos(azimuthRise))

        altitudeSet,azimuthSet = self.solstice(setHour)
        shadowLength = delta / math.tan(altitudeSet)
        #abs to deal with -cos
        minimumSpaceSet = shadowLength * abs(math.cos(azimuthSet))

        return max(minimumSpaceRise,minimumSpaceSet)

    def minSetback(self, delta, riseHour=9, setHour=15):
        """East West Setback"""
        altitudeRise,azimuthRise = self.solstice(riseHour)
        shadowLength = delta / math.tan(altitudeRise)
        minimumSpaceRise = shadowLength * math.sin(azimuthRise)

        altitudeSet,azimuthSet = self.solstice(setHour)
        shadowLength = delta / math.tan(altitudeSet)
        minimumSpaceSet = shadowLength * math.sin(azimuthSet)

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
                dp[i.array.panel.model]+=sum(i.array.shape)#.series*i.array.parallel
        return di,dp

    def now(self, timestamp = None, weatherData = None, model = 'STC'):
        #Preditive
        if timestamp is None:
            timestamp = datetime.datetime.now() - datetime.timedelta(hours=self.tz)

        if model != 'STC' and  weatherData == None:
                weatherData = forecast.data(self.place)['currently']

        if model == 'CC':
            record = irradiation.blave(timestamp,self.place,self.tilt,
                    self.azimuth, cloudCover=weatherData['cloudCover'])
        else:
            record = irradiation.blave(timestamp,self.place,self.tilt,
                    self.azimuth)

        irradiance = irradiation.irradiation(record, self.place, self.horizon,\
                t = self.tilt, array_azimuth = self.azimuth, model = 'p9')

        if model == 'STC':
            return self.Pac(irradiance)
        else:
            tModule = irradiation.moduleTemp(irradiance, weatherData)
            return self.Pac(irradiance, tModule)

    def virr(self, Pac, timestamp = None, weatherData = None):
        girr = 1000.
        gPac =  self.Pac(girr)
        if Pac > gPac:
            print "WARNING: Edge effect?"
        iteration = 2
        while round(Pac,-1) != round(gPac,-1):
            #todo: improve non linear search routine
            tModule = irradiation.moduleTemp(girr, weatherData)
            gPac =  self.Pac(girr, tModule)
            if gPac <= Pac:
                girr = girr + 1000./(iteration**2)
            else:
                girr = girr - 1000./(iteration**2)
            iteration += 1
            if iteration > 25:
                raise Exception('too many iterations')
        solarAz, solarAlt = irradiation.ephemSun(self.place,timestamp)
        irrRec = irradiation.irrGuess(timestamp,girr, solarAlt, solarAz, self.tilt, self.azimuth)
        irrRec['girr'] = round(girr,0)
        return irrRec

    def forecastOutput(self, daylightSavings = False, source = None, hours = 24):
    #def powerToday(self, daylightSavings = False, source = None, hours = 24):
        #default is forecast with solpy.blave 
        #this is ugly code... sorry
        d = datetime.date.today()
        endTimeUTC = datetime.datetime(d.year,d.month,d.day)\
                + datetime.timedelta(hours=hours-self.tz)
        if source == 'noaa':
            wseries = noaa.herpDerpInterp(self.place)
            ts = []
            irr = []
            for i in wseries:
                if i['utc_datetime'] > endTimeUTC:
                    break
                rec = irradiation.blave(i['utc_datetime'],self.place, \
                        self.tilt, self.azimuth, cloudCover = i['cloudCover'])
                irradiance = irradiation.irradiation(rec,self.place,\
                        t=self.tilt, array_azimuth=self.azimuth, model='p90')
                tModule = irradiation.moduleTemp(irradiance, i)
                irr.append(self.Pac(irradiance,tModule))
                ts.append(i['utc_datetime'])

            rs = resultSet()
            rs.values = irr
            rs.timeseries = ts
            return rs

        if source == 'forecast':
            wseries = forecast.hourly(self.place)
            ts = []
            irr = []
            for i in wseries:
                if i['utc_datetime'] > endTimeUTC:
                    break
                irradiance = irradiation.irradiation(i,self.place,\
                        t=self.tilt, array_azimuth=self.azimuth, model='p90')
                tModule = irradiation.moduleTemp(irradiance, i)
                irr.append(self.Pac(irradiance,tModule))
                ts.append(i['utc_datetime'])

            rs = resultSet()
            rs.values = irr
            rs.timeseries = ts
            return rs

        if source =='blave':
            wseries = forecast.hourly(self.place)
            ts = []
            irr = []
            for i in wseries:
                if i['utc_datetime'] > endTimeUTC:
                    break
                rec = irradiation.blave(i['utc_datetime'],self.place, \
                        self.tilt, self.azimuth, cloudCover = i['cloudCover'])
                irradiance = irradiation.irradiation(rec,self.place,\
                        t=self.tilt, array_azimuth=self.azimuth, model='p90')
                tModule = irradiation.moduleTemp(irradiance, i)
                irr.append(self.Pac(irradiance,tModule))
                ts.append(i['utc_datetime'])

            rs = resultSet()
            rs.values = irr
            rs.timeseries = ts
            return rs
        else:
            #blave
            stime = datetime.datetime.today().timetuple()
            tzOff = datetime.timedelta(hours=self.tz)
            if daylightSavings:
                tzOff += datetime.timedelta(hours=1)
            else:
                tzOff += datetime.timedelta(hours=0)
            initTime = datetime.datetime(stime[0],stime[1],stime[2]) - tzOff
            timeseries = []
            values = []
            ts = initTime
            while ts < datetime.datetime.now()-tzOff:
                ts +=  datetime.timedelta(minutes=5)
                currentPower = self.now(ts)
                values.append(currentPower)
                timeseries.append(ts)
            rs = resultSet()
            rs.values = values
            rs.timeseries = timeseries
            return rs

    def dump(self):
        d = {}
        #hack to simply
        s = [str(i.dump()) for i in self.shape]
        s = Counter(s)
        shape = []
        for i in s.iterkeys():
            t = eval(i)
            t['quantity'] = s[i]
            shape.append(t)
        d['array'] = shape
        d['tilt'] = self.tilt
        d['azimuth'] = self.azimuth
        d['phase'] = self.phase
        d['voltage'] = self.voltage
        if hasattr(self,"address"):
            d['address'] = self.address
        d['zipcode'] = self.zipcode
        d['system_name'] = self.systemName
        return d
