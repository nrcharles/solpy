"""summerize pv systems"""
import argparse
import pv
import os
import datetime
parser = argparse.ArgumentParser()
parser.add_argument('--verbose', '-v', action='count')
parser.add_argument('files', nargs='*')
args = parser.parse_args()

total_dc = 0
sdate = datetime.datetime(2014,6,16)

for i in args.files:
    try:
        plant = pv.load_system(i)
        ctime = os.path.getmtime(i)
        cdt = datetime.datetime.fromtimestamp(ctime)
        if cdt > sdate:
            total_dc += plant.p_dc(1000)/1000.
            print '%s, %s - %s, %s KW DC, %s KW AC' % (cdt, plant.system_name , \
                    plant.phase, round(plant.p_dc(1000)/1000,1), \
                    round(plant.p_ac(1000)/1000,1))
    except:
        print "error in %s" % i

print 'total: %s' % total_dc
