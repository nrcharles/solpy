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

class ResultSet(object):
    """system moduling results"""
    def __init__(self):
        """object inits with no data"""
        self.timeseries = None
        self.values = None
        self.daily_ave = 0
        self.annual_output = 0
        self.clipping_hours = 0

    def dump(self):
        """returns list of python datetime timestamps and values in Watts"""
        return (self.timeseries, self.values)

    def dumps(self):
        """returns list of unix timestamps and values in Watts"""
        return ([int((i - datetime.datetime(1970, 1, 1)).total_seconds()) \
                for i in self.timeseries], self.values)

    def plotd(self):
        """plots graph of values"""
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        fig = plt.figure()
        sub_plot = fig.add_subplot(111)
        months = mdates.MonthLocator()
        mformat = mdates.DateFormatter('%b')
        sub_plot.xaxis.set_major_locator(months)
        sub_plot.xaxis.set_major_formatter(mformat)
        sub_plot.plot(self.timeseries, self.values)
        return fig

    def plot(self):
        """plots heatmap of values"""
        import matplotlib.pyplot as plt
        total = self.hourly_values
        mangled_a = []
        for i in range(0, len(self.hourly_values), 24):
            mangled_a.append(self.hourly_values[i:i+23])
        data = np.array(mangled_a)
        data = np.rot90(data)
        fig = plt.figure()
        sub_plot = fig.add_subplot(111)#plt.subplots()
        sub_plot.set_xlim([0, 365])
        sub_plot.set_ylim([0, 22])
        sub_plot.set_ylabel('Hour of Day')
        sub_plot.set_xlabel('Day of Year')
        heatmap = sub_plot.imshow(data, aspect='auto', cmap=plt.cm.OrRd)
        txt = "Year 1 output: %s KWh" % round(sum(total)/1000, 1)
        cbar = fig.colorbar(heatmap)
        cbar.set_label('output (W)')
        sub_plot.annotate(txt, xy=(10, 3))
        plt.tight_layout()
        return fig

    def summary(self):
        """prints summary"""
        #todo: should get rid of print statements
        print "Year 1 Annual _output: %s kWh" % self.annual_output
        print "Year 1 Daily Average: %s kWh" % self.daily_ave
        print "Inverter hours clipping: %s" % self.clipping_hours

def load_system(filename):
    """Load a system from a json file"""
    try:
        return json_system(json.loads(open(filename).read()))

    except:
        print "Error: file corrupt or not found:"


def json_system(json_description):
    """Load a system from a json description"""
    #todo: this is getting unweildy should probably be refactored
    json_shape = []
    orientations = []
    for i in json_description["array"]:
        o = {}
        scale = 1
        if "scale" in i:
            scale = i["scale"]
        if "quantity" in i:
            scale = i["quantity"]
        if "shape" in i:
            shape = i["shape"]
        elif "series" in i:
            if "parallel" in i:
                parallel = i["parallel"]
            else:
                parallel = 1
            shape = [{"series":i["series"],
                    "parallel":parallel}]
        else:
            shape = [{'series':1}]

        if "tilt" in i:
            o["tilt"] = i["tilt"]
        else:
            o["tilt"] = json_description["tilt"]
        if "azimuth" in i:
            o["azimuth"] = i["azimuth"]
        else:
            o["azimuth"] = json_description["azimuth"]
        orientations.append(o)

        block = inverters.Inverter(i["inverter"], \
                modules.Array(modules.Module(i["panel"]),\
                shape), (o["azimuth"], o["tilt"]))
                #i["series"],i["parallel"]))
        if "derate" in i:
            block.derate = i["derate"]
        json_shape += [block] * scale
    plant = System(json_shape)
    plant.set_zipcode(json_description["zipcode"])
    if "address" in json_description:
        plant.address = json_description["address"]
    try:
        geocoder = geocoders.GoogleV3()
        place, (lat, lng) = geocoder.geocode(plant.address)
        plant.place = lat, lng
    except:
        pass
        #print "%s, %s location from zipcode" % plant.place
    #print orientations
    #print set(["%s_%s" % (i['azimuth'],i['tilt']) for i in orientations])
    if len(set(["%s_%s" % (i['azimuth'], i['tilt']) for i in orientations])) \
            > 1:
        print "WARNING: multiple tilts not implimented"
        plant.tilt = o[0]["tilt"]
        plant.azimuth = o[0]["azimuth"]
    elif "tilt" in json_description and "azimuth" in json_description:
        plant.tilt = json_description["tilt"]
        plant.azimuth = json_description["azimuth"]
    else:
        #"maybe incomplete"
        plant.tilt = orientations[0]["tilt"]
        plant.azimuth = orientations[0]["azimuth"]
    if 'shade' in json_description:
        plant.hourly_shade = pathfinder.hourly(json_description['shade'])

    plant.phase = json_description["phase"]
    plant.voltage = json_description["voltage"]
    plant.system_name = json_description["system_name"]
    return plant

def _calc(record):
    """internal fuction for multiprocessing hack"""
    properties, record = record
    horizon = None
    insolation = irradiation.irradiation(record, properties['place'], \
            horizon, properties['tilt'], properties['azimuth'], \
            properties['model_name'])
    year = 2000
    timestamp = tmy3.normalizeDate(record['datetime'], year)
    return timestamp, insolation, record

class System(object):
    """PV System"""
    def __init__(self, shape):
        #shape is a list of inverters with attached arrays
        self.zipcode = None
        self.place = None
        self.tilt = 32
        self.azimuth = 180
        self.shape = shape
        self.phase = 1
        self.system_name = ""
        self.clip = 0

    def set_zipcode(self, zipcode):
        """update zipcode"""
        self.zipcode = zipcode
        self.place = geo.zip_coordinates(self.zipcode)
        self.tz = geo.zip_tz(self.zipcode)
        self.name, self.usaf = geo.closest_usaf(self.place)

    def model(self, model_name='p9', single_thread=False):
        """model pv system performance"""
        #hack for threading
        #probably should be abstracted some other way
        properties = {}
        properties['place'] = self.place
        properties['tilt'] = self.tilt
        properties['azimuth'] = self.azimuth
        properties['model_name'] = model_name

        if single_thread:
            insolation_output = map(_calc, [(properties, i) \
                    for i in tmy3.data(self.usaf)])
        else:
            from multiprocessing import Pool
            from multiprocessing import cpu_count
            pool = Pool(processes=cpu_count())
            #still a hack
            insolation_output = pool.map(_calc, [(properties, i) \
                    for i in tmy3.data(self.usaf)])
            pool.close()

        houly_timeseries = np.array([])
        hourly_insolation = np.array([])

        daily_timeseries = np.array([])
        daily_insolation = np.array([])

        total_output = 0
        day = 0
        daily_output = 0
        daily_max = 0
        clip = 0

        #cache
        noload = self.p_ac(0)

        for timestamp, insolation, record in insolation_output:
            if insolation > 0:
                houly_timeseries = np.append(houly_timeseries, timestamp)
                t_amb = float(record['Dry-bulb (C)'])
                windspeed = float(record['Wspd (m/s)'])
                t_cell = .945 * t_amb +.028*insolation - 1.528*windspeed + 4.3
                if hasattr(self, 'hourly_shade'):
                    insolation = insolation * self.hourly_shade.shade(timestamp)
                output = self.p_ac(insolation, t_cell)
            else:
                output = noload
            #output = self.p_ac(insolation)
            hourly_insolation = np.append(hourly_insolation, output)

            #should probably have a flag for this to output CSV file
            #print timestamp,',', output
            if timestamp.day is day:
                daily_output += output
            else:
                daily_max = max(daily_max, daily_output)
                daily_timeseries = np.append(daily_timeseries, timestamp)
                daily_insolation = np.append(daily_insolation, \
                        daily_output/1000)
                daily_output = 0
            total_output += output
            day = timestamp.day

        resultset = ResultSet()

        resultset.timeseries = daily_timeseries
        resultset.values = daily_insolation
        resultset.htimeseries = houly_timeseries
        resultset.hourly_values = hourly_insolation

        resultset.clipping_hours = clip
        resultset.daily_ave = (round(total_output/365/10)/100)
        resultset.annual_output = (round(total_output/10)/100)

        return resultset

    def p_ac(self, ins, t_cell=25):
        """ac power output"""
        output = 0
        for i in self.shape:
            inverter_output = i.p_ac(ins, t_cell)
            output += inverter_output
            if inverter_output > .999 * i.p_aco:
                self.clip += 1
        return output

    def p_dc(self, ins, t_cell=25):
        """dc power output"""
        total_dc = 0
        for i in self.shape:
            total_dc += i.array.output(ins, t_cell)
        return total_dc

    def solstice(self, hour):
        """position on winter soltice (Dec 21)"""
        import ephem
        o = ephem.Observer()
        o.date = '2000/12/21 %s:00:00' % (hour - self.tz)
        o.lat = math.radians(self.place[0])
        o.lon = math.radians(self.place[1])
        az = ephem.Sun(o).az
        alt = ephem.Sun(o).alt

        return alt, az

    def min_row_space(self, delta, rise_hour=9, set_hour=15):
        """Row Space Function"""
        altitude_rise, azimuth_rise = self.solstice(rise_hour)
        shadow_length = delta / math.tan(altitude_rise)
        minimum_space_rise = shadow_length * abs(math.cos(azimuth_rise))

        altitude_set, azimuth_set = self.solstice(set_hour)
        shadow_length = delta / math.tan(altitude_set)
        #abs to deal with -cos
        minimum_space_set = shadow_length * abs(math.cos(azimuth_set))

        return max(minimum_space_rise, minimum_space_set)

    def min_setback(self, delta, rise_hour=9, set_hour=15):
        """East West _setback"""
        altitude_rise, azimuth_rise = self.solstice(rise_hour)
        shadow_length = delta / math.tan(altitude_rise)
        minimum_space_rise = shadow_length * math.sin(azimuth_rise)

        altitude_set, azimuth_set = self.solstice(set_hour)
        shadow_length = delta / math.tan(altitude_set)
        minimum_space_set = shadow_length * math.sin(azimuth_set)

        return max(minimum_space_rise, minimum_space_set)

    def describe(self):
        """describe system"""
        #todo: fix this garbage
        dp = {}
        di = {}
        for i in set(self.shape):
            di[i.model] = 0
            idict = i.dump()
            if hasattr(i.array, 'model'):
                dp[i.array.model] = 0
            else:
                dp[idict['panel']] = 0
        for i in self.shape:
            di[i.model] += 1
            idict = i.dump()
            if hasattr(i.array, 'model'):
                dp[i.array.model] += 1
            else:
                dp[idict['panel']] += i.array.mcount()
        return di, dp

    def now(self, timestamp=None, weather_data=None, model='STC'):
        """Preditive power output"""
        if timestamp is None:
            timestamp = datetime.datetime.now() - \
                    datetime.timedelta(hours=self.tz)

        if model != 'STC' and  weather_data == None:
            weather_data = forecast.data(self.place)['currently']

        if model == 'CC':
            record = irradiation.blave(timestamp, self.place, self.tilt,
                    self.azimuth, cloudCover=weather_data['cloudCover'])
        else:
            record = irradiation.blave(timestamp, self.place, self.tilt,
                    self.azimuth)

        irradiance = irradiation.irradiation(record, self.place, self.horizon,\
                t=self.tilt, array_azimuth=self.azimuth, model='p9')

        if model == 'STC':
            return self.p_ac(irradiance)
        else:
            t_cell = irradiation.moduleTemp(irradiance, weather_data)
            return self.p_ac(irradiance, t_cell)

    def virr(self, p_ac, timestamp=None, weather_data=None):
        """calculate virtual irradiation"""
        girr = 1000.
        gp_ac = self.p_ac(girr)
        if p_ac > gp_ac:
            print "WARNING: Edge effect?"
        iteration = 2
        while round(p_ac, -1) != round(gp_ac, -1):
            #todo: improve non linear search routine
            t_cell = irradiation.moduleTemp(girr, weather_data)
            gp_ac = self.p_ac(girr, t_cell)
            if gp_ac <= p_ac:
                girr = girr + 1000./(iteration**2)
            else:
                girr = girr - 1000./(iteration**2)
            iteration += 1
            if iteration > 25:
                raise Exception('too many iterations')
        solar_az, solar_alt = irradiation.ephemSun(self.place, timestamp)
        irrRec = irradiation.irrGuess(timestamp, girr, solar_alt, solar_az,\
                self.tilt, self.azimuth)
        irrRec['girr'] = round(girr, 0)
        return irrRec

    def forecast_output(self, daylightSavings=False, source=None, hours=24):
        """forecast output of system"""
        #default is forecast with solpy.blave
        #this is ugly code... sorry
        d = datetime.date.today()
        endTimeUTC = datetime.datetime(d.year, d.month, d.day)\
                + datetime.timedelta(hours=hours-self.tz)
        if source == 'noaa':
            wseries = noaa.herpDerpInterp(self.place)
            ts = []
            irr = []
            for i in wseries:
                if i['utc_datetime'] > endTimeUTC:
                    break
                rec = irradiation.blave(i['utc_datetime'], self.place, \
                        self.tilt, self.azimuth, cloudCover=i['cloudCover'])
                irradiance = irradiation.irradiation(rec, self.place,\
                        t=self.tilt, array_azimuth=self.azimuth, model='p90')
                t_cell = irradiation.moduleTemp(irradiance, i)
                irr.append(self.p_ac(irradiance, t_cell))
                ts.append(i['utc_datetime'])

            resultset = ResultSet()
            resultset.values = irr
            resultset.timeseries = ts
            return resultset

        if source == 'forecast':
            wseries = forecast.hourly(self.place)
            ts = []
            irr = []
            for i in wseries:
                if i['utc_datetime'] > endTimeUTC:
                    break
                irradiance = irradiation.irradiation(i, self.place,\
                        t=self.tilt, array_azimuth=self.azimuth, model='p90')
                t_cell = irradiation.moduleTemp(irradiance, i)
                irr.append(self.p_ac(irradiance, t_cell))
                ts.append(i['utc_datetime'])

            resultset = ResultSet()
            resultset.values = irr
            resultset.timeseries = ts
            return resultset

        if source == 'blave':
            wseries = forecast.hourly(self.place)
            ts = []
            irr = []
            for i in wseries:
                if i['utc_datetime'] > endTimeUTC:
                    break
                rec = irradiation.blave(i['utc_datetime'], self.place, \
                        self.tilt, self.azimuth, cloudCover=i['cloudCover'])
                irradiance = irradiation.irradiation(rec, self.place,\
                        t=self.tilt, array_azimuth=self.azimuth, model='p90')
                t_cell = irradiation.moduleTemp(irradiance, i)
                irr.append(self.p_ac(irradiance, t_cell))
                ts.append(i['utc_datetime'])

            rs = ResultSet()
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
            initTime = datetime.datetime(stime[0], stime[1], stime[2]) - tzOff
            timeseries = []
            values = []
            ts = initTime
            while ts < datetime.datetime.now()-tzOff:
                ts += datetime.timedelta(minutes=5)
                currentPower = self.now(ts)
                values.append(currentPower)
                timeseries.append(ts)
            rs = ResultSet()
            rs.values = values
            rs.timeseries = timeseries
            return rs

    def dump(self):
        """dump to dict"""
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
        if hasattr(self, "address"):
            d['address'] = self.address
        d['zipcode'] = self.zipcode
        d['system_name'] = self.system_name
        return d

    def __repr__(self):
        return '\n'.join([i for i in self.shape])
