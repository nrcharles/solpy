#!/usr/bin/env python
# Copyright (C) 2012 Nathan Charles
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
