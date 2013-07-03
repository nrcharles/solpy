import urllib, urllib2
import xml.etree.ElementTree as ET
#url = """http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?whichClient=NDFDgen&lat=38.99&lon=-77.01&listLatLon=&lat1=&lon1=&lat2=&lon2=&resolutionSub=&listLat1=&listLon1=&listLat2=&listLon2=&resolutionList=&endPoint1Lat=&endPoint1Lon=&endPoint2Lat=&endPoint2Lon=&listEndPoint1Lat=&listEndPoint1Lon=&listEndPoint2Lat=&listEndPoint2Lon=&zipCodeList=&listZipCodeList=&centerPointLat=&centerPointLon=&distanceLat=&distanceLon=&resolutionSquare=&listCenterPointLat=&listCenterPointLon=&listDistanceLat=&listDistanceLon=&listResolutionSquare=&citiesLevel=&listCitiesLevel=&sector=&gmlListLatLon=&featureType=&requestedTime=&startTime=&endTime=&compType=&propertyName=&product=time-series&begin=2013-07-01T00%3A00%3A00&end=2013-07-14T00%3A00%3A00&Unit=m&maxt=maxt&temp=temp&dew=dew&wspd=wspd&sky=sky&wx=wx&rh=rh&Submit=Submit"""
def forecast(place, forecast = True):
    lat,lon = place
    #url = """http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?whichClient=NDFDgen&lat=%s&lon=%s&listLatLon=&lat1=&lon1=&lat2=&lon2=&resolutionSub=&listLat1=&listLon1=&listLat2=&listLon2=&resolutionList=&endPoint1Lat=&endPoint1Lon=&endPoint2Lat=&endPoint2Lon=&listEndPoint1Lat=&listEndPoint1Lon=&listEndPoint2Lat=&listEndPoint2Lon=&zipCodeList=&listZipCodeList=&centerPointLat=&centerPointLon=&distanceLat=&distanceLon=&resolutionSquare=&listCenterPointLat=&listCenterPointLon=&listDistanceLat=&listDistanceLon=&listResolutionSquare=&citiesLevel=&listCitiesLevel=&sector=&gmlListLatLon=&featureType=&requestedTime=&startTime=&endTime=&compType=&propertyName=&product=time-series&begin=2013-07-01T00%%3A00%%3A00&end=2013-07-14T00%%3A00%%3A00&Unit=m&maxt=maxt&temp=temp&dew=dew&wspd=wspd&sky=sky&wx=wx&rh=rh&Submit=Submit""" % (lat,lon)
    #url = """http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?whichClient=NDFDgen&lat=%s&lon=%s&Unit=m&temp=temp&dew=dew&wspd=wspd&sky=sky&wx=wx&rh=rh&Submit=Submit""" % (lat,lon)
    #url = """http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?whichClient=NDFDgen&lat=%s&lon=%s&Unit=m&temp=temp&wspd=wspd&sky=sky&wx=wx&rh=rh&Submit=Submit""" % (lat,lon)
    url = """http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?whichClient=NDFDgen&lat=%s&lon=%s&Unit=e&temp=temp&wspd=wspd&sky=sky&wx=wx&rh=rh&Submit=Submit""" % (lat,lon)
    #http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?whichClient=NDFDgen&lat=38.99&lon=-77.01&listLatLon=&lat1=&lon1=&lat2=&lon2=&resolutionSub=&listLat1=&listLon1=&listLat2=&listLon2=&resolutionList=&endPoint1Lat=&endPoint1Lon=&endPoint2Lat=&endPoint2Lon=&listEndPoint1Lat=&listEndPoint1Lon=&listEndPoint2Lat=&listEndPoint2Lon=&zipCodeList=&listZipCodeList=&centerPointLat=&centerPointLon=&distanceLat=&distanceLon=&resolutionSquare=&listCenterPointLat=&listCenterPointLon=&listDistanceLat=&listDistanceLon=&listResolutionSquare=&citiesLevel=&listCitiesLevel=&sector=&gmlListLatLon=&featureType=&requestedTime=&startTime=&endTime=&compType=&propertyName=&product=time-series&begin=2004-01-01T00%3A00%3A00&end=2017-07-03T00%3A00%3A00&Unit=e&temp=temp&wspd=wspd&sky=sky&Submit=Submit
    res =  urllib2.urlopen(url).read()
    root = ET.fromstring(res)

    windSpd = [eval(i.text) for i in root.findall('./data/parameters/wind-speed')[0].iterfind('value')]
    cloudCover = [eval(i.text)/100.0 for i in root.findall('./data/parameters/cloud-amount')[0].iterfind('value')]
    temperature = [eval(i.text) for i in root.findall('./data/parameters/temperature')[0].iterfind('value')]
    if forecast:
        return {'cloudCover':cloudCover[0],
            'temperature':temperature[0],
            'windSpeed':windSpd[0]}

if __name__ == '__main__':
    import geo
    place = geo.zipToCoordinates('17601')
    print forecast(place)
    #print windSpd, len(windSpd)
    #print cloudCover, len(cloudCover)
    #print temperature, len(temperature)
