"""Forecast IO API"""
import json
import urllib2
import os
import datetime

apikey = os.getenv('FORECASTIO')
if not apikey:
    print "WARNING: forecast.io key not set."
    print "Realtime weather data not availible."

def data(place):
    lat,lon = place
    url = "https://api.forecast.io/forecast/%s/%s,%s?solar" % (apikey, lat,lon)
#url = apiurl + "%s/summary?key=%s" % (self.system_id,apikey)
    a = json.loads(urllib2.urlopen(url).read())
    return a

def mangle(data_point):
    temp_dict = {}
    temp_dict.update(data_point) 
    temp_dict['utc_datetime'] = datetime.datetime.utcfromtimestamp(temp_dict['time'])
    if 'solar' in data_point:
        temp_dict['GHI (W/m^2)'] = data_point['solar']['ghi']
        temp_dict['DNI (W/m^2)'] = data_point['solar']['dni']
        temp_dict['DHI (W/m^2)'] = data_point['solar']['dhi']
        temp_dict['ETR (W/m^2)'] = data_point['solar']['etr']
        del temp_dict['solar']
    else:
        temp_dict['GHI (W/m^2)'] = 0.0
        temp_dict['DNI (W/m^2)'] = 0.0
        temp_dict['DHI (W/m^2)'] = 0.0
        temp_dict['ETR (W/m^2)'] = 0.0
    return temp_dict

#these functions should probably be class methods
def hourly(place):
    """return data as list of dicts with all data filled in"""
    #time in utc?
    lat,lon = place
    url = "https://api.forecast.io/forecast/%s/%s,%s?solar" % (apikey, lat,lon)
    a = json.loads(urllib2.urlopen(url).read())
    hourly = a['hourly']['data']
    mangled = []
    for i in hourly:
        mangled.append(mangle(i))
    return mangled

def current(place):
    """return data as list of dicts with all data filled in"""
    lat,lon = place
    url = "https://api.forecast.io/forecast/%s/%s,%s?solar" % (apikey, lat,lon)
    a = json.loads(urllib2.urlopen(url).read())
    current = a['currently']
    return mangle(current)

if __name__ == '__main__':
    lat,lon = (40. ,-78.0)
    url = "https://api.forecast.io/forecast/%s/%s,%s" % (apikey, lat,lon)
    print url
    print hourly((lat,lon))
    print current((lat,lon))
