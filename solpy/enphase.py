# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

"""This is a thin wrapper around the enphase energy api.

Import and then set the APIKEY.

if ENPHASE environmental variable is set that will be used first.

import enphase
enphase.APIKEY = "key hash"

enphase.index()
"""

TCP_TIMEOUT = 5.0

import json
import logging
import urllib2
import numpy as np
import datetime
import matplotlib
import os
import time

logger = logging.getLogger(__name__)

matplotlib.use('Agg')

APIURL = "https://api.enphaseenergy.com/api/v2/systems"

APIKEY = os.getenv('ENPHASE')
MAX_WAIT = 60


def validate_enphase_date(date):
    """validate enphase date."""
    from datetime import datetime

    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError as e:
        print e
        return False
    return True


def seconds(temp_dt):
    """datetime seconds since epoch."""
    return (temp_dt - datetime.datetime(1970, 1, 1)).total_seconds()

if not APIKEY:
    print "WARNING: Enphase key not set."
    print "Realtime weather data not availible."


def run_query(url):
    """Handle Errors for querying the ENPHASE api."""
    while True:
        try:
            logger.debug(url)
            j = json.loads(urllib2.urlopen(url, timeout=TCP_TIMEOUT).read())
            break
        except urllib2.HTTPError as e:
            errordata = json.loads(e.read())
            print url
            print e
            print errordata
            if errordata['reason'] == '409':
                diff = datetime.datetime.fromtimestamp(errordata['period_end'])\
                    - datetime.datetime.now()
                if diff.total_seconds() < MAX_WAIT:
                    print 'Waiting %d seconds' % diff.total_seconds()
                    time.sleep(diff.total_seconds())
                else:
                    raise urllib2.HTTPError(e.url, e.code, e.msg, e.hdrs, e.fp)
    return j


class ResultSet(object):

    """Result set."""

    def __init__(self, ts, v):
        """initialize ResultSet with timeseries and values."""
        self.timeseries = ts
        self.values = v

    def plot(self):
        """plot data."""
        import matplotlib.pyplot
        fig = matplotlib.pyplot.figure()
        subplot = fig.add_subplot(111)
        subplot.plot(self.timeseries, self.values)
        return fig

    def jsify(self):
        """return dict of unix timestamps and values."""
        return zip([int(seconds(obj)*1000)
                   for obj in self.timeseries.tolist()], self.values.tolist())


class System(object):

    """Represents an interface to collect Enphase data about a system."""

    def gen_url(self, command="", start_date=None, end_date=None,
                unix_epoch=False, callback=None):
        """Generate a url for which to request data from Enphase.

        Keyword arguments:
        command -- The Enphase API command to call.
        start_date -- Either a unix timestamp or a date for the beginning of
                      the range.
        end_date -- Either a unix timestamp or a date for the of the end range.
        unix_epoch -- If True the *_date arguments are timestamps else dates.
        callback -- The function to call upon returning data from the server.
        if unix_epoch is false the dates must be in format '%Y-%m-%d'
        """
        url = (self.url + command + self.api_suffix) % self.__dict__
        if start_date:
            if unix_epoch:
                url += "&start_at=%s" % int(start_date)
            else:
                if validate_enphase_date(start_date):
                    url += "&start_date=%s" % str(start_date)
                else:
                    raise ValueError('start_date format invalid')
        if end_date:
            if unix_epoch:
                url += "&end_at=%s" % int(end_date)
            else:
                if validate_enphase_date(end_date):
                    url += "&end_date=%s" % str(end_date)
                else:
                    raise ValueError('end_date format invalid')
        if callback:
            url += "&callback=%s" % str(callback)
        return url

    def __eq__(self, other):
        """check equality."""
        return self.system_id == other.system_id

    def __init__(self, system_id, user_id, **sys_info):
        """Create an Enphase interface object.

        system_id -- The Enphase system number.
        user_id -- An authorized user key value to access data for the system.
        sys_info -- A dictionary of relevant information to the system.
        """
        # deal with direct load
        self.system_id = str(system_id)
        self.user_id = str(user_id)
        self.key = APIKEY

        self.api_suffix = "?key=%(key)s&user_id=%(user_id)s"
        self.url = APIURL

        self.__dict__.update(sys_info)

    def summary(self, summary_date=None):
        """Return summary information for the specified system."""
        url = self.gen_url("/%(system_id)s/summary")

        if summary_date:
            if validate_enphase_date(summary_date):
                url += '&summary_date=%s' % summary_date
        return run_query(url)

    def alerts(self, level=None):
        """(depricated in API2)."""
        url = self.gen_url("/%(system_id)s/alerts")
        return run_query(url)

    def energy_lifetime(self, start_date=None, end_date=None):
        """Return the energy produced by the system over its lifetime."""
        url = self.gen_url("/%(system_id)s/energy_lifetime",
                           start_date, end_date)
        return run_query(url)

    def monthly_production(self, start_date):
        """Return the energy produced for the month."""
        from datetime import datetime

        start = datetime.strptime(start_date, '%Y-%m-%d')
        t = datetime(*datetime.now().timetuple()[0:3])

        if (t-start).days < 30:
            raise ValueError('start_date must be at least one month ago')

        url = self.gen_url("/%(system_id)s/monthly_production", start_date)
        return run_query(url)

    def stats(self, start_at=None, end_at=None):
        """Return performance statistics for the specified system.

        Statistics are eported by installed microinverters.

        start_at -- Unix timestamp for the beginning range.
        end_at -- Unix timestamp for the end range.
        May return HTTP Error 422 specifically if the array hasn't
        produced any power yet today
        """
        if end_at is not None:
            if end_at < start_at:
                raise ValueError('end_at must be after start_at if specified')
            if start_at is None:
                raise TypeError(
                    'start_at must be specified if end_at is specified')
            else:
                if end_at - start_at > 60*60*24:
                    raise ValueError('enphase will not return more then'
                                     '24 hours of stats regardless of what the'
                                     'documentation says')

        url = self.gen_url("/%(system_id)s/stats", start_at, end_at, True)
        return run_query(url)

    def rgm_stats(self, start_date=None, end_date=None):
        """Return revenue-grade meter performance statistics for system."""
        url = self.gen_url("/%(system_id)s/rgm_stats",
                           start_date, end_date, True)
        return run_query(url)

    def inventory(self):
        """Return a listing of active devices on the system."""
        url = self.gen_url("/%(system_id)s/inventory")
        return run_query(url)

    def get_date_range(self, start, end):
        """Return the stats for a range of days."""
        if type(start) != int:
            raise TypeError('start must be int')
        if type(end) != int:
            raise TypeError('end must be int')
        if start < 0 or end < 1:
            raise ValueError('Negative offsets not allowed')

        from datetime import datetime
        from datetime import timedelta
        production = []
        timeseries = []
        t = datetime(*datetime.now().timetuple()[0:3])-datetime(1970, 1, 1)
        for start_at in [(t - timedelta(days=x)).total_seconds()
                         for x in xrange(start, end)]:
            for i in self.stats(start_at)['intervals']:
                production.append(i['powr'])
                timeseries.append(datetime.utcfromtimestamp(i['end_at']))

        return ResultSet(np.array(timeseries), np.array(production))

    def power_today(self):
        """Return the power produced so far today."""
        return self.get_date_range(0, 1)

    def power_2days(self):
        """Return the last two days to get at last 24 hours."""
        return self.get_date_range(0, 2)

    def power_week(self):
        """Return the power generated for the previous six complete days."""
        # deprecated
        return self.get_date_range(1, 7)

    def power_week_i(self):
        """Return power generated for previous six days and today."""
        # deprecated
        return self.get_date_range(0, 7)

    def envoys(self):
        """listing of all active Envoys currently deployed on the system."""
        url = self.gen_url("/%(system_id)s/envoys")
        return run_query(url)

    def performance_factor(self, tilt=0):
        """Return guess of performance factor of system."""
        a = self.summary()
        p = a['current_power']*1.0 / (a['modules']*215)
        return p

    def __repr__(self):
        """repr."""
        return '%s: %s' % (self.system_id, self.system_name)


def _str_datetime(ts1):
    # yyyy-mm-ddThh:mm:ss-xx:y
    # reformat = ts1[0:22]+ts1[23:25]
    tsformat = "%Y-%m-%dT%H:%M:%S"
    # timezone = ts1[19:22]+ts1[23:25]
    return datetime.datetime.strptime(ts1[0:19], tsformat)


def index(user_id=None, **kwargs):
    """Query Enphase regarding the systems accessable by this user_id.

    user_id -- The user_id to query
    Optional arguments are the following
    Search criteria may be any or all of the following:
        system_id, system_name, status, reference, installer, connection_type
        Additionally limit will limit the number of systems returned per batch
        However multiple url requests will be made until all relevant systems
        have been retreived from Enphase.
    """
    query = ""
    solo = ['next', 'limit']
    if kwargs is not None:
        if len(kwargs) > 1 + len([x for x in solo if x in kwargs]):
            queryStr = "&%s[]=%s"
        else:
            queryStr = "&%s=%s"
        for item in kwargs.iteritems():
            if item[0] in solo:
                query += "&%s=%s" % item
            else:
                query += (queryStr % item)

    if user_id:
        url = (APIURL + "?key=%s&user_id=%s") % (APIKEY, user_id)
    else:
        url = (APIURL + "?key=%s") % (APIKEY)

    url += query

    a = run_query(url)

    systems = [System(user_id=user_id, **i) for i in a["systems"]]

    if 'next' in a.keys():
        kwargs['next'] = a['next']
        systems.extend(index(user_id, **kwargs))

    return systems


def power_today(user_id):
    """Return the power produced today by all accessable systems."""
    ts = None
    b = []
    for i in index(user_id):
        a = i.power_today()
        ts = a.timeseries
        b.append(a.values)
    return ResultSet(ts, sum(b))


def power_week(user_id):
    """Power for all accessible systems produced in the last six days."""
    ts = None
    b = []
    for i in index(user_id):
        a = i.power_week()
        ts = a.timeseries
        b.append(a.values)
    return ResultSet(ts, sum(b))


def power_week_i(user_id):
    """power_week and power so far today."""
    # include today
    ts = None
    b = []
    for i in index(user_id):
        a = i.power_week_i()
        ts = a.timeseries
        b.append(a.values)
    return ResultSet(ts, sum(b))


# todo: determine relavence
# Analytical models of enphase parts.
class M215():

    """M215 Analytical model."""

    def __init__(self, number, landscape=True, phase=1):
        """Initialize system topology."""
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
        """Voltage drop."""
        n = self.number + 1
        if self.phase is 1:
            # 1 phase theoretical
            # vd = 0.00707n(n+1)al
            l = 1.0
            return n*(n+1)*.00707*self.a*l
        elif self.phase is 3:
            # 3 phase emperical
            # y = 0.0036x^2 + 0.0094x + 0.0209
            return 0.0036 * n*n + 0.0094 * n + 0.0209
        else:
            print "ERROR"


class Engage():

    """Engage cable analytical model."""

    def __init__(self, inverters, phase=1, landscape=True, endfed=False):
        """Initialize engage cable topology."""
        self.endfed = endfed
        self.landscape = landscape
        self.phase = phase
        self.s1 = []
        self.s2 = []
        if endfed is True:
            self.s1 = [M215(i, self.landscape, self.phase)
                       for i in range(0, inverters)]
        else:
            a = inverters/2
            self.s1 = [M215(i, self.landscape, self.phase)
                       for i in range(0, a)]
            b = inverters - a
            self.s2 = [M215(i, self.landscape, self.phase)
                       for i in range(0, b)]

    def vd(self):
        """Voltage drop."""
        if self.endfed:
            return self.s1[-1].vd()
        else:
            return max(self.s1[-1].vd(), self.s2[-1].vd())
        # if self.phase is 1:
        #    return self.a[0].a * (len(self.a) + len(self.b)) * self.distance

    def a(self):
        """Amperage."""
        if self.phase is 1:
            a = (len(self.s1)+len(self.s2)) * 0.895
            return a
        else:
            return (len(self.s1)+len(self.s2)) / 1.732

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser('Information for Enphase Energy systems.')
    parser.add_argument('user_id', type=str, help='The user id to query')

    args = parser.parse_args()

    a = index(args.user_id)

    for i in a:
        print i.system_name
        print i.power_today().jsify()
        print i.stats()
        print i.power_2days().jsify()
