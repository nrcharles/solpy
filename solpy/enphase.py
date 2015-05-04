# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

"""This is a thin wrapper around the enphase energy api.
Import and then setting the APIKEY.

if ENPHASE environmental variable is set that will be used first.

import enphase
enphase.APIKEY = "key hash"

enphase.index()
"""

TCP_TIMEOUT = 5.0

import json
import urllib2
import numpy as np
import datetime
import matplotlib
import os

matplotlib.use('Agg')

APIURL = "https://api.enphaseenergy.com/api/systems"
APIURL2 = "https://api.enphaseenergy.com/api/v2/systems"

APIKEY = os.getenv('ENPHASE')

def seconds(temp_dt):
    """datetime seconds since epoch"""
    return (temp_dt - datetime.datetime(1970, 1, 1)).total_seconds()

if not APIKEY:
    print "WARNING: Enphase key not set."
    print "Realtime weather data not availible."

class ResultSet(object):
    """Result Set"""
    def __init__(self, ts, v):
        self.timeseries = ts
        self.values = v
    def plot(self):
        """plot data"""
        fig = matplotlib.pyplot.figure()
        subplot = fig.add_subplot(111)
        subplot.plot(self.timeseries, self.values)
        return fig
    def jsify(self):
        """return dict of unix timestamps and values"""
        return zip([int(seconds(obj)*1000) \
                for obj in self.timeseries.tolist()], self.values.tolist())

class System(object):
    """system(system_id) if called directly"""

    def gen_url(self, command = "", start_date=None, end_date=None, unix_epoch = False, callback=None ):
        """Generates a url for which to request data from Enphase"""
        url = (self.url + command + self.api_suffix) % self.__dict__
        if start_date:
            if unix_epoch:
                url += "&start_at=%s" % str(start_date)
            else:
                url += "&start_date=%s" % str(start_date)
        if end_date:
            if unix_epoch:
                url += "&end_at=%s" % str(end_date)
            else:
                url += "&end_date=%s" % str(end_date)
        if callback:
            url += "&callback=%s" % str(callback)
        print url
        return url

    def __init__(self, system_id, user_id, **sys_info):
        #deal with direct load

        self.system_id = str(system_id)
        self.user_id = str(user_id)
        self.key = APIKEY

        self.api_suffix = "?key=%(key)s&user_id=%(user_id)s"
        self.url = APIURL2

        if len(self.system_id) > 0 and len(self.user_id) > 0:
            url = self.gen_url("/%(system_id)s/summary")
            tsys = json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())
            self.__dict__.update(tsys)

        self.__dict__.update(sys_info)

    
    def summary(self, summary_date=None):
        """Returns summary information for the specified system."""
        url = self.gen_url("/%(system_id)s/summary")
        return json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())

    def alerts(self, level=None):
        """alerts (depricated in API2)"""
        url = self.gen_url("/%(system_id)s/alerts")
        return json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())

    def lifetime_energy(self):
        """Returns a time series of energy produced on the system over its lifetime. All measurements are in Watt hours."""
        url = self.gen_url("/%(system_id)s/energy_lifetime")
        return json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())

    def monthly_production(self, start_date):
        """Returns the energy production of the system for the month starting on the given date."""
        url = self.gen_url("/%(system_id)s/monthly_production", start_date)
        return json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())

    def power_today(self):
        """power produced so far today"""
        today =     datetime.date.today()
        midnight = datetime.datetime(today.year, today.month, today.day)
        start_at = int(seconds(midnight))
        production = []
        timeseries = []
        try:
            for i in self.stats(start_at)['intervals']:
                production.append(i['powr'])
                timeseries.append(datetime.datetime.utcfromtimestamp(i['end_at']))
        except:
            production.append(0)
            timeseries.append(datetime.datetime.utcfromtimestamp(start_at))
        return ResultSet(np.array(timeseries), np.array(production))

    def power_2days(self):
        """this function returns last two days to get at last 24 hours"""
        production = []
        timeseries = []

        #yesterday
        today = datetime.date.today()
        midnight = datetime.datetime(today.year, today.month, today.day)
        start_at = int(seconds(midnight-datetime.timedelta(days=1)))
        for i in self.stats(start_at)['intervals']:
            production.append(i['powr'])
            timeseries.append(datetime.datetime.utcfromtimestamp(i['end_at']))
        #today
        midnight = datetime.datetime(today.year, today.month, today.day)
        for i in self.stats(start_at)['intervals']:
            production.append(i['powr'])
            timeseries.append(datetime.datetime.utcfromtimestamp(i['end_at']))
        return ResultSet(np.array(timeseries), np.array(production))

    def power_week(self):
        #deprecated
        url = self.gen_url("/%(system_id)s/power_week")
        a = json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())
        production = np.array(a["production"])
        begin = _str_datetime(a["first_interval_end_date"])
        interval = datetime.timedelta(seconds=a["interval_length"])#: 300,
        timeseries = np.array([begin])
        for i in range(1, len(a["production"])):
            timeseries = np.append(timeseries, begin + interval * i)
        return ResultSet(timeseries, production)

    def power_week_i(self):
        #deprecated
        url = self.gen_url("/%(system_id)s/power_week")
        a = json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())
        begin = _str_datetime(a["first_interval_end_date"])
        interval = datetime.timedelta(seconds=a["interval_length"])#: 300,
        timeseries = np.array([begin])

        url = APIURL + "/%s/power_today?key=%s" % (self.system_id, APIKEY)
        ai = json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())
        production_i = a["production"] + ai["production"]
        production = np.array(production_i)
        for i in range(1, len(production_i)):
            timeseries = np.append(timeseries, begin + interval * i)
        return ResultSet(timeseries, production)

    def rgm_stats(self, start_date=None, end_date=None):
        """Returns performance statistics as measured by the revenue-grade meters installed on the specified system."""
        url = self.gen_url("/%(system_id)s/rgm_stats", start_date, end_date, True)
        return json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())

    def stats(self, start_at=None, end_at=None):
        """Returns performance statistics for the specified system as reported by microinverters installed on the system.
            start_at and end_at are unix epoch
            May return HTTP Error 422 specifically if the array hasn't produced any power yet today"""
        url = self.gen_url("/%(system_id)s/stats", start_at, end_at, True)
        return json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())

    def envoys(self):
        """Returns a listing of all active Envoys currently deployed on the system."""
        url = self.gen_url("/%(system_id)s/envoys")
        return json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())

    def performance_factor(self, tilt=0):
        a = self.summary()
        p = a['current_power']*1.0 / (a['modules']*215)
        return p

    def __repr__(self):
        return '%s: %s' % (self.system_id, self.system_name)

def _str_datetime(ts1):
    #yyyy-mm-ddThh:mm:ss-xx:y
    #reformat = ts1[0:22]+ts1[23:25]
    tsformat = "%Y-%m-%dT%H:%M:%S"
    timezone = ts1[19:22]+ts1[23:25]
    return datetime.datetime.strptime(ts1[0:19], tsformat)

def index(user_id):
    APIURL = "https://api.enphaseenergy.com/api/v2/systems/"
    url = (APIURL + "?key=%s&user_id=%s") % (APIKEY,user_id)
    a = json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())
    return [System(user_id=user_id,**i) for i in a["systems"]]

def power_today():
    ts = None
    b = []
    for i in index():
        a = i.power_today()
        ts = a.timeseries
        b.append(a.values)
    return ResultSet(ts, sum(b))

def power_week():
    ts = None
    b = []
    for i in index():
        a = i.power_week()
        ts = a.timeseries
        b.append(a.values)
    return ResultSet(ts, sum(b))

def power_week_i():
    #include today
    ts = None
    b = []
    for i in index():
        a = i.power_week_i()
        ts = a.timeseries
        b.append(a.values)
    return ResultSet(ts, sum(b))

#todo: determine relavence
#Analytical models of enphase parts.
class M215():
    def __init__(self, number, landscape=True, phase=1):
        self.phase = phase
        self.number = number
        self.a = .896
        self.v = 240
        self.w = 215
        self.wires = 4
        if phase is not 1:
            self.a = 1.0
            self.v = 208
            self.wires = 5
    def vd(self):
        n = self.number + 1
        if self.phase is 1:
            #1 phase theoretical
            #vd = 0.00707n(n+1)al
            l = 1.0
            return n*(n+1)*.00707*self.a*l
        elif self.phase is 3:
            #3 phase emperical
            #y = 0.0036x^2 + 0.0094x + 0.0209
            return 0.0036 * n*n + 0.0094 * n + 0.0209
        else:
            print "ERROR"

class Engage():
    def __init__(self, inverters, phase=1, landscape=True, endfed=False):
        self.endfed = endfed
        self.landscape = landscape
        self.phase = phase
        self.s1 = []
        self.s2 = []
        if endfed is True:
            self.s1 = [M215(i, self.landscape, self.phase) \
                    for i in range(0, inverters)]
        else:
            a = inverters/2
            self.s1 = [M215(i, self.landscape, self.phase) for i in range(0, a)]
            b = inverters - a
            self.s2 = [M215(i, self.landscape, self.phase) for i in range(0, b)]

    def vd(self):
        if self.endfed:
            return self.s1[-1].vd()
        else:
            return max(self.s1[-1].vd(), self.s2[-1].vd())
        #if self.phase is 1:
        #    return self.a[0].a * (len(self.a) + len(self.b)) * self.distance
    def a(self):
        if self.phase is 1:
            a = (len(self.s1)+len(self.s2)) * 0.895
            return a
        else:
            return (len(self.s1)+len(self.s2)) /1.732

if __name__ == "__main__":
    a = index()
    #print [i.system_name for i in a]
    print a[2].power_today().jsify()
    print a[2].stats()
    print a[2].power_2days().jsify()
