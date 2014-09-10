#!/usr/bin/env python
# Copyright (C) 2012 Nathan Charles
#
# This program is free software. See terms in LICENSE file.
"""voltage drop"""

def usage():
    """Prints usage options when called without or invalid arguments"""
    print """usage: [options]
   -a    current
   -l    length
   -p    phase [default 1]
   -v    voltage [default 240]
   -s    size
   -h    help
    """

from solpy import ee
from solpy import nec

def vd(amperage, length, size=None, v=240, pf=-1, t_amb=30, percent=1, \
        material='CU', c='STEEL', verbose=True):
    """calculate voltage drop"""
    oc = amperage * 1.25
    ocp = ee.ocp_size(oc)
    vdrop = v * percent/100.0
    if size:
        conductor = ee.Conductor(size, material)
        conductor = ee.check_ampacity(conductor, ocp, t_amb)
        vdrop = conductor.vd(amperage, length, v=v, pf=pf, t_amb=t_amb, c=c)
        vdp = (vdrop * 100/v)
        if verbose:
            print "Percent drop: %s%%" % round(vdp, 2)
        return conductor
    else:
        if verbose:
            print "Allowed Voltage drop: %sV" % vdrop
        sets = 0
        conductor = None
        #todo: refactor for recursive. should take away the need for nec import
        while conductor is None:
            sets += 1
            for s in nec.CONDUCTOR_STANDARD_SIZES:
                #print s, material
                conductor = ee.Conductor(s, material)
                #print conductor
                if conductor.vd(amperage*1.0/sets, length, v=v, pf=pf, \
                        t_amb=t_amb, c=c) < vdrop:
                    break
                else:
                    conductor = None

        if sets > 1:
            print "%s sets of %s" % (sets, conductor)
            #print "EGC Size: %s" % incEGC(conductor,egc,ratio)
            return [conductor] * sets
            #return [conductor for i in range(sets)]
        else:
            if verbose:
                print "Conductor %s" % conductor
            conductor = ee.check_ampacity(conductor, ocp/sets, t_amb)
            if verbose:
                print "Drop: %s V" % round(conductor.vd(amperage*1.0/sets, \
                        length, v=v, pf=pf, t_amb=t_amb, c=c), 2)
            return conductor

if __name__ == "__main__":
    import argparse
    import sys
    PARSER = argparse.ArgumentParser(description='Voltage Drop/Rise Calculator')
    PARSER.add_argument('-a', '--aluminum', action='store_true')
    PARSER.add_argument('-c', '--current', required=True, \
            help="accepts basic math") #evaluated to allow command line math
    PARSER.add_argument('-d', '--drop', type=float, default=1, \
            help="Voltage Drop/Rise in percent")
    PARSER.add_argument('-v', '--voltage', type=float, default=240)
    PARSER.add_argument('-f', '--powerfactor', default="-1")
    PARSER.add_argument('-l', '--length', required=True, \
            help="accepts basic math") #evaluated to allow command line math
    PARSER.add_argument('-p', '--conduit', type=str, default='PVC')
    PARSER.add_argument('-s', '--size', type=str, help="wire size")
    PARSER.add_argument('-t', '--temp', type=float, help="ambient", default=30)
    #PARSER.print_help()
    ARGS = vars(PARSER.parse_args())
    MATERIAL = 'CU'
    if ARGS['aluminum']:
        MATERIAL = 'AL'
    try:
        DC = 'DC'
        dc = 'DC'
        vd(eval(ARGS['current']), eval(ARGS['length']), ARGS['size'], \
                ARGS['voltage'], eval(ARGS['powerfactor']), ARGS['temp'], \
                ARGS['drop'], material=MATERIAL, c=ARGS['conduit'])

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
