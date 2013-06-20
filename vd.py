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

def vd(a,l,size= None,v = 240, pf=-1, tAmb=30, percent=1, material='CU', c='STEEL'):
    oc = a * 1.25
    ocp = ee.ocpSize(oc)
    #print "OCP Size: %s" % ocp
    #egc = ee.findEGC(ocp,material)
    vdrop = v * percent/100.0
    #ratio = ee.CMIL[ee.conductorAmpacity(a,material).size]*1.0/ee.CMIL[ee.findEGC(ocp)]
    if size:
        conductor  = ee.conductor(size,material)
        conductor = ee.checkAmpacity(conductor, ocp, tAmb)
        vdrop = conductor.vd(a,l, v = v, pf=pf, tAmb=tAmb,c=c)
        vdp=(vdrop * 100/v)
        print "Percent drop: %s%%" % round(vdp,2)
        #print "EGC Size: %s" % incEGC(conductor,egc,ratio)
        return conductor
    else:
        print "Allowed Voltage drop: %sV" % vdrop
        sets = 0
        conductor = None
        while conductor is None:
            sets += 1
            for s in ee.CONDUCTOR_STANDARD_SIZES:
                #print s, material
                conductor = ee.conductor(s,material)
                #print conductor
                if conductor.vd(a*1.0/sets,l, v = v, pf=pf, tAmb=tAmb,c=c) < vdrop:
                    break
                else:
                    conductor = None

        if sets > 1:
            print "%s sets of %s" % (sets, conductor)
            #print "EGC Size: %s" % incEGC(conductor,egc,ratio)
            return [conductor for i in range(sets)]
        else:
            print "Conductor %s" % conductor
            conductor = ee.checkAmpacity(conductor, ocp/sets, tAmb)
            #print "EGC Size: %s %s" % ( incEGC(conductor,egc,ratio),'CU'#conductor.material)
            print "Drop: %s V" % round(conductor.vd(a*1.0/sets,l, v = v, pf=pf, tAmb=tAmb,c=c),2)
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
    parser.add_argument('-t', '--temp',type=float,help="ambient",default=30)
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
                args['drop'],material=material,c = args['conduit'])

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
