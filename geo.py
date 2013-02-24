#    Copyright 2012 Nathan Charles
#
#
#    This is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This software is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with solpy. If not, see <http://www.gnu.org/licenses/>.

import csv
import math
import os
SPATH = os.path.dirname(os.path.abspath(__file__))

def closestUSAF(place, stationClass=3):
    latitude,longitude = place
    index = open(SPATH + '/StationsMeta.csv')
    index_data = csv.DictReader(index)
    d1 = 9999
    name = ''
    usaf = ''
    for i in index_data:
        d2 = math.sqrt(math.pow((float(i['Latitude']) - latitude),2) +math.pow((float(i['Longitude']) - longitude),2))
        uncertainty = len(i['Class'])
        if d2 < d1 and uncertainty <= stationClass:
            d1 = d2
            name = i['Site Name']
            usaf = i['USAF']
    index.close()
    return name, usaf

def zipToCoordinates(zipcode):
    """takes string"""
    index = open(SPATH + '/zipcode.csv')
    #read over license
    headerLen = 31
    for i in range(headerLen):
        index.readline()
    index_data = csv.DictReader(index)
    for i in index_data:
        if i['zip'] == zipcode:
            return float(i['latitude']),float( i['longitude'])

def zipToTZ(zipcode):
    index = open(SPATH + '/zipcode.csv')
    #read over license
    headerLen = 31
    for i in range(headerLen):
        index.readline()
    index_data = csv.DictReader(index)
    for i in index_data:
        if i['zip'] == zipcode:
            return int(i['timezone'])
