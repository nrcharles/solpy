# Copyright (C) 2013 Nathan Charles
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

"""This is a thin wrapper around the enphase energy api.  Use simply requires 
importing and then setting the apikey.

import enphase
enphase.apikey = "key hash"

enphase.index()

"""


import json
import urllib2
import numpy as np
import datetime
import matplotlib
import time
import os

matplotlib.use('Agg')

apiurl = "https://api.enphaseenergy.com/api/systems/"

apikey = os.getenv('ENPHASE')
if not apikey:
    print "WARNING: forecast.io key not set."
    print "Realtime weather data not availible."

class resultSet(object):
    def __init__(self,ts,v):
        self.timeseries = ts
        self.values = v
    def plot(self):
        fig = matplotlib.pyplot.figure()
        ax = fig.add_subplot(111)
        ax.plot(self.timeseries, self.values)
        return fig
    def jsify(self):
        return zip([ int(time.mktime(obj.timetuple())*1000 - 4*3600000 ) \
                for obj in self.timeseries.tolist()],self.values.tolist())


class system(object):
    def __init__(self, **sys_info):
        self.__dict__.update(sys_info)

    def summary(self, summary_date=None):
        url = apiurl + "%s/summary?key=%s" % (self.system_id,apikey)
        return json.loads(urllib2.urlopen(url).read())

    def alerts(self,level=None):
        url = apiurl + "%s/alerts?key=%s" % (self.system_id,apikey)
        return json.loads(urllib2.urlopen(url).read())

    def energy_lifetime(self):
        url = apiurl + "%s/energy_lifetime?key=%s" % (self.system_id,apikey)
        return json.loads(urllib2.urlopen(url).read())

    def monthly_production(self, start_date):
        url = apiurl + "%s/monthly_production?key=%s&start=%s" % \
                (self.system_id,apikey,start_date)
        return json.loads(urllib2.urlopen(url).read())

    def power_today(self):
        url = apiurl + "%s/power_today?key=%s" % (self.system_id,apikey)
        a = json.loads(urllib2.urlopen(url).read())
        production = np.array(a["production"])
        begin = strToDatetime(a["first_interval_end_date"])
        interval = datetime.timedelta(seconds=a["interval_length"])#: 300,
        timeseries = np.array([begin]) 
        for i in range(1,len(a["production"])):
            timeseries = np.append(timeseries,begin + interval * i)
        return resultSet(timeseries,production)

    def power_week(self):
        url = apiurl + "%s/power_week?key=%s" % (self.system_id,apikey)
        a = json.loads(urllib2.urlopen(url).read())
        production = np.array(a["production"])
        begin = strToDatetime(a["first_interval_end_date"])
        interval = datetime.timedelta(seconds=a["interval_length"])#: 300,
        timeseries = np.array([begin]) 
        for i in range(1,len(a["production"])):
            timeseries = np.append(timeseries,begin + interval * i)
        return resultSet(timeseries,production)

    def power_week_i(self):
        url = apiurl + "%s/power_week?key=%s" % (self.system_id,apikey)
        a = json.loads(urllib2.urlopen(url).read())
        begin = strToDatetime(a["first_interval_end_date"])
        interval = datetime.timedelta(seconds=a["interval_length"])#: 300,
        timeseries = np.array([begin]) 
        url = apiurl + "%s/power_today?key=%s" % (self.system_id,apikey)
        ai = json.loads(urllib2.urlopen(url).read())
        production_i = a["production"]+ai["production"]
        production = np.array(production_i)
        for i in range(1,len(production_i)):
            timeseries = np.append(timeseries,begin + interval * i)
        return resultSet(timeseries,production)

    def rgm_stats(self, start_date=None,end_date=None):
        url = apiurl + "%s/rgm_stats?key=%s" % (self.system_id,apikey)
        return json.loads(urllib2.urlopen(url).read())

    def stats(self,start_date=None,end_date=None):
        url = apiurl + "%s/stats?key=%s" % (self.system_id,apikey)
        return json.loads(urllib2.urlopen(url).read())

    def envoys(self):
        url = apiurl + "%s/envoys?key=%s" % (self.system_id,apikey)
        return json.loads(urllib2.urlopen(url).read())

    def performance_factor(self, tilt=0):
        a = self.summary()
        p = a['current_power']*1.0/(a['modules']*215)
        return p

def strToDatetime(ts1):
    #yyyy-mm-ddThh:mm:ss-xx:y
    #reformat = ts1[0:22]+ts1[23:25]
    tsformat = "%Y-%m-%dT%H:%M:%S"
    tz = ts1[19:22]+ts1[23:25]
    return datetime.datetime.strptime(ts1[0:19],tsformat)

def index():
    url = "https://api.enphaseenergy.com/api/systems?key=%s" % apikey
    a = json.loads(urllib2.urlopen(url).read())
    return [system(**i) for i in a["systems"]]

def power_today():
    ts = None
    b = []
    for i in index():
        a = i.power_today()
        ts = a.timeseries
        b.append(a.values)
    return resultSet(ts,sum(b))

def power_week():
    ts = None
    b = []
    for i in index():
        a = i.power_week()
        ts = a.timeseries
        b.append(a.values)
    return resultSet(ts,sum(b))

def power_week_i():
    #include today
    ts = None
    b = []
    for i in index():
        a = i.power_week_i()
        ts = a.timeseries
        b.append(a.values)
    return resultSet(ts,sum(b))

if __name__ == "__main__":
    print index()
