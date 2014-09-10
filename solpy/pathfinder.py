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
    shade_file = open(filename)
    headings = np.array(-180.0)
    elevations = np.array(0.0)
    for line in shade_file.readlines():
        azimuth, elevation = line.split(' ')
        headings = np.append(headings, float(azimuth))
        elevations = np.append(elevations, float(elevation))
    headings = np.append(headings, 180.0)
    elevations = np.append(elevations, 0.0)

    return interp1d(headings, elevations)

#write as class
#round to halfhour
def load_dict(filename):
    """load pathfinder month by hour shading data"""
    month = {}
    with open(filename) as csvfile:
        for line in csvfile:
            if line.find('Month') is not -1:
                break
        reader = csv.reader(csvfile)
        for line_no, line in enumerate(reader):
            if line_no >= 12:
                break
            month[str(line_no)] = [float(hour)/100 for hour in line[1:]]
    return month

class Hourly(object):
    """Hourly Shade Object"""
    def __init__(self, shade_dict):
        self.month = shade_dict
    def shade(self, _datetime):
        """return percentage of full sun for a datetime"""
        hoffset = int(_datetime.hour * 2 + round(_datetime.minute/60.))
        moffset = str(_datetime.month - 1)
        return self.month[moffset][hoffset]


if __name__ == "__main__":
    import argparse
    import datetime
    PARSER = argparse.ArgumentParser(description='horizon')
    PARSER.add_argument('-f', '--horizon', help='Pathfinder .hor file')
    PARSER.add_argument('-c', '--hourly', help='Pathfinder hourly .csv file')
    ARGS = vars(PARSER.parse_args())
    try:
        #start program
        print ARGS['horizon']
        if ARGS['horizon']:
            HORIZON = horizon(ARGS['file'])
        if ARGS['hourly']:
            HOURLY_SHADE = Hourly(load_dict(ARGS['hourly']))
            for i in range(1, 13):
                for j in range(0, 24):
                    for k in range(0, 2):
                        dt = datetime.datetime(2012, i, 1, j, k*30)
                        print dt, HOURLY_SHADE.shade(dt)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
