import urllib2
import xml.etree.ElementTree as ET
def forecast(place, forecast = True):
    lat,lon = place
    url = """http://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php?whichClient=NDFDgen&lat=%s&lon=%s&Unit=e&temp=temp&wspd=wspd&sky=sky&wx=wx&rh=rh&Submit=Submit""" % (lat,lon)
    res =  urllib2.urlopen(url).read()
    root = ET.fromstring(res)

    timeSeries = [(i.text) for i in root.findall('./data/time-layout')[0].iterfind('start-valid-time')]
    #knots to mph
    windSpd = [eval(i.text)*1.15 for i in root.findall('./data/parameters/wind-speed')[0].iterfind('value')]
    cloudCover = [eval(i.text)/100.0 for i in root.findall('./data/parameters/cloud-amount')[0].iterfind('value')]
    temperature = [eval(i.text) for i in root.findall('./data/parameters/temperature')[0].iterfind('value')]
    if forecast:
        return {'cloudCover':cloudCover[0],
            'temperature':temperature[0],
            'windSpeed':windSpd[0],
            'start-valid-time':timeSeries[0]}
    else:
        return {'cloudCover':cloudCover,
            'temperature':temperature,
            'windSpeed':windSpd,
            'start-valid-time':timeSeries}

if __name__ == '__main__':
    import geo
    place = geo.zipToCoordinates('17603')
    print forecast(place)
    #print windSpd, len(windSpd)
    #print cloudCover, len(cloudCover)
    #print temperature, len(temperature)
