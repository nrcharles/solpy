#!/usr/bin/env python
# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

import numpy as np
import sys

def horizon(filename):
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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='horizon')
    parser.add_argument('-f', '--file',help='Pathfinder .hor file',required=True)
    args = vars(parser.parse_args())
    try:
        #start program
        f = horizon(args['file'])

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
