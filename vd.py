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

def usage():
    """Prints usage options when called with no arguments or with invalid arguments
    """
    print """usage: [options]
   -a    current
   -l    length
   -p    phase [default 1]
   -v    voltage [default 240]
   -s    size
   -h    help
    """

import ee

#def solve()
#def vd(args, **kwargs):

def incEGC(egc,ratio):
    if ratio > 0:
        increased = ee.CMIL[egc]*ratio
        for c in ee.CONDUCTOR_STANDARD_SIZES:
            if ee.CMIL[c] >= increased:
                return c
    else: 
        return egc

def vd(a,l,size= None,v = 240, pf=-1, t=75, percent=1, material='CU', c='PVC'):
    #a =  eval(args['current'])
    #l = eval(args['length'])
    #size = args['size']
    #v = args['voltage']
    #pf = eval(args['powerfactor'])
    #t = args['temp']
    #c = args['conduit']
    #percent = args['drop']
    #material = 'CU'
    oc = a * 1.25
    print "Continous Current: %s" % a
    ocp = ee.findOCP(oc)
    print "OCP Size: %s" % ocp
    egc = ee.findEGC(ocp,material)
    vd = v * percent/100.0
    r = 0
    ratio = ee.CMIL[ee.findConductorA(a,material).size]*1.0/ee.CMIL[ee.findEGC(ocp)]
    print "Ratio: ",ratio
    if size:
        tconductor = ee.conductor(size, material)
        r = ee.resistance( tconductor,c,pf, t)
        print r
        vd = 2.0* a * r * l/1000.0
        print "Voltage drop: %sV" % vd
        print "Percent drop: %s%%" % (vd * 100/v)
        tconductor = ee.checkAmpacity(tconductor, ocp)
        print "EGC Size: %s" % incEGC(egc,ratio)
        return tconductor

    else:
        print "Allowed Voltage drop: %sV" % vd
        #vd = 2*a*l*r/1000
        r = (vd*1000)/(2.0 * a*l)
        print "Resistance: %s" % r
        sets = 1
        conductor = None
        while 1:
            conductor = ee.findConductor((r*sets),material,c,pf,t)
            if conductor:
                break
            sets +=1

        if sets > 1:
            print "WARNING: %s sets of conductors" % sets
            print "EGC Size: %s" % incEGC(egc,ratio)
            return [conductor for i in range(sets)]
        else:
            print "Conductor %s" % conductor
            conductor = ee.checkAmpacity(conductor, ocp/sets)
            print "EGC Size: %s" % incEGC(egc,ratio)
            return conductor

if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Voltage Drop/Rise Calculator')
    parser.add_argument('-a', '--aluminum',action='store_true')
    parser.add_argument('-c', '--current',required=True,help="accepts basic math") #evaluated to allow command line math
    parser.add_argument('-d', '--drop',type=float,default=1,help="Voltage Drop/Rise in percent")
    parser.add_argument('-v', '--voltage',type=float,default=240)
    parser.add_argument('-f', '--powerfactor',default="-1")
    parser.add_argument('-l', '--length',required=True,help="accepts basic math")#evaluated to allow command line math
    parser.add_argument('-p', '--conduit',type=str,default='PVC')
    parser.add_argument('-s', '--size',type=str,help="wire size")
    parser.add_argument('-t', '--temp',type=float,help="actual conductor temp",default=75)
    #parser.print_help()
    args = vars(parser.parse_args())
    material = 'CU'
    if args['aluminum']:
        material = 'AL'
    #solve(args['current'],args['length'],args['voltage'],args['drop'])
    #print args

    try:
        #start program
        #vd(args)
        #vd(current,length,size= None,v = 240, pf="-1",temp = 75,percent = 1,material = 'CU', c = 'PVC')
        DC = 'DC'
        dc = 'DC'
        vd(eval(args['current']),eval(args['length']),args['size'],
                args['voltage'],eval(args['powerfactor']),args['temp'],
                args['drop'],material,args['conduit'])

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
