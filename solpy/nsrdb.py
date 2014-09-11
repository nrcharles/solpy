# Copyright (C) 2012 Nathan Charles
#
# This program is free software. See terms in LICENSE file.
"""look at NSRDB historical data"""
import csv
import datetime
import os
import numpy as np
from solpy import tools

#path to data defaults to cwd unless NCDCDATA enviromental variable is set
CWD = os.getcwd()
PATH = [os.getenv('NCDCDATA', CWD)]

def strptime(string, timezone=0):
    """necessary because of 24:00 end of day labeling"""
    year = int(string[0:4])
    month = int(string[5:7])
    day = int(string[8:10])
    hour = int(string[-5:-3])
    minute = int(string[-2:])
    ts = datetime.datetime(year, month, day) + datetime.timedelta(hours=hour, \
            minutes=minute) - datetime.timedelta(hours=timezone)
    return ts

def normalize_date(tmy_date, year):
    """change TMY3 date to an arbitrary year"""
    year = year
    month = tmy_date.month
    day = tmy_date.day - 1
    hour = tmy_date.hour
    minute = 0
    #hack to get around 24:00 notation
    if month is 1 and day is 0 and hour is 0:
        year += 1
    return datetime.datetime(year, month, 1) + datetime.timedelta(days=day, \
            hours=hour, minutes=minute)

class Data():
    """data generator"""
    def __init__(self, usaf, year=2010):
        basefile = "NSRDB_StationData_%s0101_%s1231_%s.csv" % (year, year, usaf)
        filename = tools.find_file(basefile, PATH)
        self.usaf_info = geo.station_info(usaf)
        self.timezone = int(self.usaf_info['TZ'])
        self.place = (float(self.usaf_info['Latitude']), \
                float(self.usaf_info['Longitude']))
        self.csvfile = None
        try:
            self.csvfile = open(filename)
        except:
            print "File not found"
        self.tmy_data = csv.DictReader(self.csvfile)
    def __iter__(self):
        return self

    def next(self):
        t = self.tmy_data.next()
        sd = t['YYYY-MM-DD'] + ' ' + t['HH:MM (LST)']
        t['utc_datetime'] = strptime(sd, self.timezone)
        t['datetime'] = strptime(sd)
        return t

    def __del__(self):
        self.csvfile.close()

def monthly(usaf, year, field='GHI (W/m^2)'):
    """monthly insolation"""
    m = []
    lastm = 1
    usafdata = Data(usaf, year)
    t = 0
    for r in usafdata:
        r['GHI (W/m^2)'] = r['Glo Mod (Wh/m^2)']
        r['DHI (W/m^2)'] = r['Dif Mod (Wh/m^2)']
        r['DNI (W/m^2)'] = r['Dir Mod (Wh/m^2)']
        if r['datetime'].month != lastm:
            m.append(t/1000.)
            t = 0
            lastm = r['utc_datetime'].month
        t += float(r[field])
    return m

def report(usaf):
    """generate report for usaf base"""
    fig = plt.figure()
    ax = fig.add_subplot(111)
    station_info = geo.station_info(usaf)
    y = {}
    for i in range(1991, 2011):
        monthData = monthly(usaf, i)
        t = sum(monthData)
        y[i] = t
        print t
    tmy3tot = tmy3.total(usaf)
    average = sum([v for k, v in y.items()])/20.
    s = sorted(y.items(), key=lambda t: t[1])
    o = sorted(y.items(), key=lambda t: t[0])
    twohigh = s[-1][1] + s[-2][1]
    twolow = s[0][1] + s[1][1]
    mintol = 1-twolow/2./average
    plustol = twohigh/2./average-1
    txt = ""
    txt += "%s\n" % station_info['Site Name']
    txt += 'TMY3/hist: %s/' % int(round(tmy3tot))
    txt += '%s\n' % int(round(average))
    txt += "high/low av: %s/" % int(round(twohigh/2.))
    txt += "%s\n" %  int(round(twolow/2.))
    txt += "+%s/-%s%% " % (round(plustol*100, 0), round(mintol*100, 0))
    txt += "(-%s%% of TMY3)" % round((1-twolow/2./tmy3tot)*100, 0)
    print txt
    x = np.array([k for k, v in o])
    y = np.array([v for k, v in o])

    rx = x[1:]
    ry = [(v + y[i+1])/2 for i, v in enumerate(y[:-1])]
    fit = pylab.polyfit(x, y, 3)
    fit_fn = pylab.poly1d(fit)
    f = interp1d(x, y, kind='cubic')
    f2 = interp1d(rx, ry, kind='cubic')
    xnew = np.linspace(min(x), max(x), 200)
    x2 = np.linspace(min(rx), max(rx), 200)
    #ax.plot(x,y)
    ax.plot(xnew, f(xnew), label="Annual GHI")
    ax.plot(xnew, fit_fn(xnew), label='trendline')
    ax.plot(x2, f2(x2), label='2 Year Ave')
    ax.plot([min(x), max(x)], [tmy3tot, tmy3tot], linestyle='--')
    leg = plt.legend(title=txt, loc=4, fancybox=True)
    leg.get_frame().set_alpha(0.5)
    #fig.text(min(x),min(y)-min(y)*.1,txt)
    #fig.text(.1,.1,txt)
    plt.tight_layout()
    fig.savefig('%s_annual_GHI.pdf' % (usaf), format='pdf')

if __name__ == "__main__":
    from solpy import geo
    from solpy import tmy3
    tilt = 32.0
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy.interpolate import interp1d
    #from scipy import stats
    import pylab
    usaf_stations = []
    usaf_stations.append('912850')
    usaf_stations.append('725115') #MDT
    usaf_stations.append('724290') #,DAYTON INTERNATIONAL AIRPORT
    usaf_stations.append('724070') #,ATLANTIC CITY INTL AP
    usaf_stations.append('724060') #,BALTIMORE BLT-WASHNGTN INT'L
    #
    for station in usaf_stations:
        report(station)
