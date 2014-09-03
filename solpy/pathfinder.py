#!/usr/bin/env python
# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.
"""This module has some functions to deal with Solar pathfinder files"""

import numpy as np
import sys
import csv

def horizon(filename):
    """load pathfinder horizon file into scipy interpolate object"""
    from scipy.interpolate import interp1d
    a = open(filename)
    b = np.array(-180.0)
    c = np.array(0.0)
    for i in a.readlines():
        azimuth, elevation = i.split(' ')
        b = np.append(b,float(azimuth))
        c = np.append(c,float(elevation))
    b = np.append(b,180.0)
    c = np.append(c,0.0)

    return interp1d(b,c)

#write as class
#round to halfhour
def loadDict(filename):
    """load pathfinder month by hour shading data"""
    month = {}
    with open(filename) as csvfile:
        for i in csvfile:
            if i.find('Month') is not -1:
                break
        reader = csv.reader(csvfile)
        for i,line in enumerate(reader):
            if i >= 12:
                break
            month[str(i)] = [float(k)/100 for k in line[1:]]
    return month 

class hourly(object):
    def __init__(self, shadeDict):
        self.month = shadeDict
    def shade(self, dt):
        """return decimal of full sun fraction for a datetime"""
        hoffset = int(dt.hour * 2 + round(dt.minute/60.))
        moffset = str(dt.month - 1)
        return self.month[moffset][hoffset]
        #return float(self.blah[moffset][hoffset])/100


if __name__ == "__main__":
    import argparse
    import datetime
    parser = argparse.ArgumentParser(description='horizon')
    parser.add_argument('-f', '--horizon',help='Pathfinder .hor file')
    parser.add_argument('-c', '--hourly',help='Pathfinder hourly .csv file')
    args = vars(parser.parse_args())
    try:
        #start program
        print args['horizon']
        if args['horizon']:
            f = horizon(args['file'])
        if args['hourly']:
            blah = hourly(loadDict(args['hourly']))
            for i in range(1,13):
                pass
                for j in range(0,24):
                    for k in range (0,2):
                        dt = datetime.datetime(2012,i,1,j,k*30)
                        print dt,blah.shade(dt)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
