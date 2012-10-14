import csv
import math

def closestUSAF(place):
    latitude,longitude = place
    index = open('StationsMeta.csv')
    index_data = csv.DictReader(index)
    d1 = 9999
    name = ''
    usaf = ''
    for i in index_data:
        d2 = math.sqrt(math.pow((float(i['Latitude']) - latitude),2) +math.pow((float(i['Longitude']) - longitude),2))
        if d2 < d1:
            d1 = d2
            name = i['Site Name']
            usaf = i['USAF']
    index.close()
    return name, usaf

def zipToCoordinates(zip):
    index = open('zipcode.csv')
    #read over license
    headerLen = 31
    for i in range(headerLen):
        index.readline()
    index_data = csv.DictReader(index)
    for i in index_data:
        if int(i['zip']) == zip:
            return float(i['latitude']),float( i['longitude'])

def zipToTZ(zip):
    index = open('zipcode.csv')
    #read over license
    headerLen = 31
    for i in range(headerLen):
        index.readline()
    index_data = csv.DictReader(index)
    for i in index_data:
        if int(i['zip']) == zip:
            return int(i['timezone'])
