import urllib2
import xml.etree.ElementTree as ET
from scipy.interpolate import interp1d
import datetime
import time

def forecast(place, forecast = True):
    lat,lon = place
    url = """http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?whichClient=NDFDgen&lat=%s&lon=%s&Unit=e&temp=temp&wspd=wspd&sky=sky&wx=wx&rh=rh&product=time-series&Submit=Submit""" % (lat,lon)
    print url
    res =  urllib2.urlopen(url).read()
    root = ET.fromstring(res)

    timeSeries = [(i.text) for i in root.findall('./data/time-layout')[0].iterfind('start-valid-time')]
    #knots to mph
    print res
    windSpd = [eval(i.text)*1.15 for i in root.findall('./data/parameters/wind-speed')[0].iterfind('value')]
    cloudCover = [eval(i.text)/100.0 for i in root.findall('./data/parameters/cloud-amount')[0].iterfind('value')]
    temperature = [eval(i.text) for i in root.findall('./data/parameters/temperature')[0].iterfind('value')]
    if not forecast:
        return {'cloudCover':cloudCover[0],
            'temperature':temperature[0],
            'windSpeed':windSpd[0],
            'start-valid-time':timeSeries[0]}
    else:
        return {'cloudCover':cloudCover,
            'temperature':temperature,
            'windSpeed':windSpd,
            'start-valid-time':timeSeries}

def strToTime(str):
    fmt='%Y-%m-%dT%H:%M:00'
    return datetime.datetime.strptime(str[0:19],fmt)

def castFloat(d):
    """returns utc timestamp"""
    if type(d) == str:
        fmt='%Y-%m-%dT%H:%M:00'
        lt= d[0:19]
        tz = eval(d[19:22])
        d = datetime.datetime.strptime(lt,fmt) - datetime.timedelta(hours=tz)
    return (d - datetime.datetime(1970,1,1)).total_seconds()

def herpDerpInterp(place):
    lat,lon = place
    #begin=2014-02-14T00%3A00%3A00&end=2018-02-22T00%3A00%3A00
    fmt='%Y-%m-%dT00:00:00'
    fmt='%Y-%m-%dT%H:%M:00'
    begin=(datetime.datetime.now()-datetime.timedelta(hours=12)).strftime(fmt)
    #end=(datetime.datetime.now()+datetime.timedelta(hours=48)).strftime(fmt)
    url = """http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?whichClient=NDFDgen&lat=%s&lon=%s&Unit=e&temp=temp&wspd=wspd&sky=sky&wx=wx&rh=rh&product=time-series&begin=%s&end=2018-02-22T00:00:00&Submit=Submit""" % (lat, lon, begin)
    res =  urllib2.urlopen(url).read()
    root = ET.fromstring(res)

    timeSeries = [castFloat(i.text) for i in root.findall('./data/time-layout')[0].iterfind('start-valid-time')]
    #knots to mph
    windSpd = [eval(i.text)*1.15 for i in root.findall('./data/parameters/wind-speed')[0].iterfind('value')]
    cloudCover = [eval(i.text)/100.0 for i in root.findall('./data/parameters/cloud-amount')[0].iterfind('value')]
    temperature = [eval(i.text) for i in root.findall('./data/parameters/temperature')[0].iterfind('value')]

    ws = interp1d(timeSeries, windSpd, kind='cubic')
    cc = interp1d(timeSeries, cloudCover, kind='cubic')
    t  = interp1d(timeSeries, temperature, kind='cubic')
    startD = datetime.datetime.utcfromtimestamp(timeSeries[0])

    series = []
    for i in range(48):
        try:
            temp_dict = {}
            b = startD + datetime.timedelta(hours=i)
            temp_dict['utc_datetime'] = b
            temp_dict['windSpeed'] = ws(castFloat(b)).item()
            temp_dict['temperature'] = t(castFloat(b)).item()
            temp_dict['cloudCover'] = cc(castFloat(b)).item()
            series.append(temp_dict)
        except:
            pass
    return series

if __name__ == '__main__':
    import geo
    place = geo.zipToCoordinates('17603')
    #print forecast(place)
    print herpDerpInterp(place)
    #print windSpd, len(windSpd)
    #print cloudCover, len(cloudCover)
    #print temperature, len(temperature)
    
