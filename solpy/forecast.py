"""Forecast IO API"""
import json
import urllib2
import os
import datetime

APIKEY = os.getenv('FORECASTIO')
if not APIKEY:
    print "WARNING: forecast.io key not set."
    print "Realtime weather data not availible."

def data(place):
    """get forecast data"""
    lat, lon = place
    url = "https://api.forecast.io/forecast/%s/%s,%s?solar" % (APIKEY, lat, lon)
    w_data = json.loads(urllib2.urlopen(url).read())
    return w_data

def mangle(data_point):
    """mangle data into expected format"""
    temp_dict = {}
    temp_dict.update(data_point)
    temp_dict['utc_datetime'] = \
            datetime.datetime.utcfromtimestamp(temp_dict['time'])
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
    lat, lon = place
    url = "https://api.forecast.io/forecast/%s/%s,%s?solar" % (APIKEY, lat, lon)
    w_data = json.loads(urllib2.urlopen(url).read())
    hourly_data = w_data['hourly']['data']
    mangled = []
    for i in hourly_data:
        mangled.append(mangle(i))
    return mangled

def current(place):
    """return data as list of dicts with all data filled in"""
    lat, lon = place
    url = "https://api.forecast.io/forecast/%s/%s,%s?solar" % (APIKEY, lat, lon)
    w_data = json.loads(urllib2.urlopen(url).read())
    currently = w_data['currently']
    return mangle(currently)

if __name__ == '__main__':
    LAT, LON = (40., -78.0)
    URL = "https://api.forecast.io/forecast/%s/%s,%s" % (APIKEY, LAT, LON)
    print URL
    print hourly((LAT, LON))
    print current((LAT, LON))
