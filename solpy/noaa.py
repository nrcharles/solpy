"""wrapper around NOAA GFS api"""
import logging
logger = logging.getLogger(__name__)

import urllib2
import xml.etree.ElementTree as ET
from scipy.interpolate import interp1d
import datetime

def forecast(place, series=True):
    """NOAA weather forecast for a location"""
    lat, lon = place
    url = "http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?" + \
            "whichClient=NDFDgen&" + "lat=%s&lon=%s&" % (lat, lon) + \
            "Unit=e&temp=temp&wspd=wspd&sky=sky&wx=wx&rh=rh&" + \
            "product=time-series&Submit=Submit"
    logger.debug(url)
    res = urllib2.urlopen(url).read()
    root = ET.fromstring(res)
    time_series = [(i.text) for i in \
            root.findall('./data/time-layout')[0].iterfind('start-valid-time')]
    logger.debug(res)
    #knots to mph
    wind_speed = [eval(i.text)*1.15 for i in \
            root.findall('./data/parameters/wind-speed')[0].iterfind('value')]
    cloud_cover = [eval(i.text)/100.0 for i in \
            root.findall('./data/parameters/cloud-amount')[0].iterfind('value')]
    temperature = [eval(i.text) for i in \
            root.findall('./data/parameters/temperature')[0].iterfind('value')]
    if not series:
        return {'cloudCover':cloud_cover[0], \
                'temperature':temperature[0], \
                'windSpeed':wind_speed[0], \
                'start-valid-time':time_series[0]}
    else:
        return {'cloudCover':cloud_cover, \
                'temperature':temperature, \
                'windSpeed':wind_speed, \
                'start-valid-time':time_series}

def _str_time(string):
    """unused fuction?"""
    fmt = '%Y-%m-%dT%H:%M:00'
    return datetime.datetime.strptime(string[0:19], fmt)

def _cast_float(temp_dt):
    """returns utc timestamp"""
    if type(temp_dt) == str:
        fmt = '%Y-%m-%dT%H:%M:00'
        base_dt = temp_dt[0:19]
        tz_offset = eval(temp_dt[19:22])
        temp_dt = datetime.datetime.strptime(base_dt, fmt) - \
                datetime.timedelta(hours=tz_offset)
    return (temp_dt - datetime.datetime(1970, 1, 1)).total_seconds()

def herp_derp_interp(place):
    """simple interpolation of GFS forecast"""
    lat, lon = place
    #begin=2014-02-14T00%3A00%3A00&end=2018-02-22T00%3A00%3A00
    fmt = '%Y-%m-%dT00:00:00'
    fmt = '%Y-%m-%dT%H:%M:00'
    begin = (datetime.datetime.now()-datetime.timedelta(hours=12)).strftime(fmt)
    #end=(datetime.datetime.now()+datetime.timedelta(hours=48)).strftime(fmt)
    url = "http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?" + \
            "whichClient=NDFDgen&lat=%s&lon=%s&" % (lat, lon) + \
            "Unit=e&temp=temp&wspd=wspd&sky=sky&wx=wx&rh=rh&" + \
            "product=time-series&begin=%s&end=2018-02-22T00:00:00" % begin + \
            "&Submit=Submit"""
    res = urllib2.urlopen(url).read()
    root = ET.fromstring(res)

    time_series = [_cast_float(i.text) for i in \
            root.findall('./data/time-layout')[0].iterfind('start-valid-time')]
    #knots to mph
    wind_speed = [eval(i.text)*1.15 for i in \
            root.findall('./data/parameters/wind-speed')[0].iterfind('value')]
    cloud_cover = [eval(i.text)/100.0 for i in \
            root.findall('./data/parameters/cloud-amount')[0].iterfind('value')]
    temperature = [eval(i.text) for i in \
            root.findall('./data/parameters/temperature')[0].iterfind('value')]

    ws_interp = interp1d(time_series, wind_speed, kind='cubic')
    cc_interp = interp1d(time_series, cloud_cover, kind='cubic')
    t_interp = interp1d(time_series, temperature, kind='cubic')
    start_date = datetime.datetime.utcfromtimestamp(time_series[0])

    series = []
    for i in range(48):
        try:
            temp_dict = {}
            forecast_dt = start_date + datetime.timedelta(hours=i)
            temp_dict['utc_datetime'] = forecast_dt
            temp_dict['windSpeed'] = ws_interp(_cast_float(forecast_dt)).item()
            temp_dict['temperature'] = t_interp(_cast_float(forecast_dt)).item()
            temp_dict['cloudCover'] = cc_interp(_cast_float(forecast_dt)).item()
            series.append(temp_dict)
        except:
            pass
    return series

if __name__ == '__main__':
    from solpy import geo
    PLACE = geo.zip_coordinates('17603')
    #print forecast(place)
    print herp_derp_interp(PLACE)
    #print wind_speed, len(wind_speed)
    #print cloudCover, len(cloudCover)
    #print temperature, len(temperature)
