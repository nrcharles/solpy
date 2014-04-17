import csv
# Copyright (C) 2012 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

import datetime
import os
import tools

#path to data defaults to cwd unless NCDCDATA enviromental variable is set
CWD = os.getcwd()
PATH = [os.getenv('NCDCDATA',CWD)]

def strptime(string, tz=0):
    #necessary because of 24:00 end of day labeling
    Y = int(string[0:4])
    M = int(string[5:7])
    D = int(string[8:10])
    h = int(string[-5:-3])
    m = int(string[-2:])
    ts = datetime.datetime(Y, M, D) + datetime.timedelta(hours=h, minutes=m) - datetime.timedelta(hours=tz)
    return ts

def normalizeDate(tmyDate, year):
    """change TMY3 date to an arbitrary year"""
    Y = year
    M = tmyDate.month
    D = tmyDate.day -1
    h = tmyDate.hour
    m = 0
    #hack to get around 24:00 notation
    if M is 1 and D is 0 and h is 0:
        Y = Y + 1
    return datetime.datetime(Y, M, 1) + datetime.timedelta(days=D, hours=h, minutes=m)

class data():
    def __init__(self, USAF, year = 2010):
        basefile = "NSRDB_StationData_%s0101_%s1231_%s.csv" % (year, year, USAF)
        filename = tools.find_file(basefile, PATH)
        self.USAFinfo = geo.stationInfo(USAF)
        self.tz = int(self.USAFinfo['TZ'])
        self.place = (float(self.USAFinfo['Latitude']),float(self.USAFinfo['Longitude']))
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
        sd = t['YYYY-MM-DD'] +' '+ t['HH:MM (LST)']
        t['utc_datetime'] = strptime(sd,self.tz)
        t['datetime'] = strptime(sd)
        return t

    def __del__(self):
        self.csvfile.close()

def monthly(usaf, year, field='GHI (W/m^2)'):
    m = []
    lastm = 1
    usafdata = data(usaf,year)
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
    fig = plt.figure()
    ax = fig.add_subplot(111)
    stationInfo = geo.stationInfo(usaf)
    y = {} 
    for i in range(1991,2011):
        monthData = monthly(usaf,i)
        t = sum(monthData)
        y[i] = t
        print t
    tmy3tot = tmy3.total(usaf)
    average = sum([v for k,v in y.items()])/20.
    s = sorted(y.items(),key=lambda t: t[1]) 
    o = sorted(y.items(),key=lambda t: t[0]) 
    twohigh = s[-1][1] + s[-2][1]
    twolow = s[0][1] + s[1][1]
    mintol = 1-twolow/2./average
    plustol =twohigh/2./average-1
    txt = ""
    txt += "%s\n" % stationInfo['Site Name']
    txt += 'TMY3/hist: %s/' % int(round(tmy3tot))
    txt += '%s\n' % int(round(average))
    txt += "high/low av: %s/" % int(round(twohigh/2.))
    txt += "%s\n" %  int(round(twolow/2.))
    txt += "+%s/-%s%% " % (round(plustol*100,0), round(mintol*100,0))
    txt += "(-%s%% of TMY3)" % round((1-twolow/2./tmy3tot)*100,0)
    print txt
    import numpy as np
    x= np.array([k for k,v in o])
    y= np.array([v for k,v in o])

    rx = x[1:]
    ry = [(v + y[i+1])/2 for i,v in enumerate(y[:-1])]
    fit = pylab.polyfit(x,y,3)
    fit_fn = pylab.poly1d(fit)
    f = interp1d(x, y, kind='cubic')
    f2 = interp1d(rx, ry, kind='cubic')
    xnew = np.linspace(min(x), max(x),200)
    x2 = np.linspace(min(rx), max(rx),200)
    #ax.plot(x,y)
    ax.plot(xnew,f(xnew),label="Annual GHI")
    ax.plot(xnew,fit_fn(xnew),label='trendline')
    ax.plot(x2,f2(x2),label='2 Year Ave')
    ax.plot([min(x),max(x)],[tmy3tot,tmy3tot],linestyle='--')
    leg = plt.legend(title=txt,loc=4,fancybox=True)
    leg.get_frame().set_alpha(0.5)
    #fig.text(min(x),min(y)-min(y)*.1,txt) 
    #fig.text(.1,.1,txt) 
    plt.tight_layout()
    fig.savefig('%s_annual_GHI.pdf' % (usaf),format='pdf')

if __name__ == "__main__":
    import geo
    import tmy3
    tilt = 32.0
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy.interpolate import interp1d
    #from scipy import stats
    import pylab
    usafA = []
    usafA.append('912850')
    usafA.append('725115') #MDT
    usafA.append('724290') #,DAYTON INTERNATIONAL AIRPORT
    usafA.append('724070') #,ATLANTIC CITY INTL AP
    usafA.append('724060') #,BALTIMORE BLT-WASHNGTN INT'L
    #
    for usaf in usafA:
        report(usaf)
