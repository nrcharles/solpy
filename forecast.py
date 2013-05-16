"""Forecast IO API"""
import json
import geo
import urllib2
import os

apikey = os.getenv('FORECASTIO')
if not apikey:
    print "WARNING: forecast.io key not set."
    print "Realtime weather data not availible."

def data(zipcode):
    place = geo.zipToCoordinates(zipcode)
    lat,lon = place
    url = "https://api.forecast.io/forecast/%s/%s,%s" % (apikey, lat,lon)
#url = apiurl + "%s/summary?key=%s" % (self.system_id,apikey)
    a = json.loads(urllib2.urlopen(url).read())
    return a
