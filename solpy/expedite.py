#!/usr/bin/env python
# coding=utf-8
# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

"""Calculate expedited permit process info"""
import logging
logger = logging.getLogger(__name__)

from math import degrees
import sys

from solpy import eere
from solpy import geo
from solpy import pv
from solpy import ee
from solpy import vd
from solpy import modules
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

try:
    import geomag
except Exception:
    logger.warning("geomag not loaded.  Magnetic declination unavailible")

def string_notes(system, run=0.0, station_class=3):
    """page 5"""

    name, usaf = geo.closest_usaf(geo.zip_coordinates(system.zipcode), \
            station_class)
    mintemp = eere.minimum(usaf)
    twopercent_temp = eere.twopercent(usaf)
    ac_kva_rated = 0.0
    dc_rated = 0.0
    ac_kw = 0.0
    for i in system.shape:
        dc_rated += i.array.p_max
        try:
            if i.phase == 1:
                ac_kva_rated += i.current * i.ac_voltage
            else:
                ac_kva_rated += i.phase * i.current * i.ac_voltage / 3**.5
        except Exception:
            ac_kva_rated += i.p_aco
        ac_kw += i.p_aco
    notes = []
    notes.append("%s KVA AC RATED" % round(ac_kva_rated/1000.0, 2))
    notes.append("%s KW AC RATED" % round(ac_kw/1000.0, 2))
    notes.append("%s KW DC RATED" % round(dc_rated/1000.0, 2))
    #BUG: This doesn't work for unbalanced 3 phase
    if system.phase == 1:
        a_ac = round(ac_kva_rated/i.ac_voltage, 1)
    else:
        a_ac = round(ac_kva_rated/i.ac_voltage/3**.5, 1)
    notes.append("System AC Output Current: %s A" % a_ac)

    notes.append("Nominal AC Voltage: %s V" % i.ac_voltage)
    notes.append("")
    notes.append("Minimum Temperature: %s C" % mintemp)
    notes.append("2 Percent Max Temperature: %s C" % twopercent_temp)
    notes.append("Weather Source: %s %s" % (name, usaf))
    notes.append("")
    d_inverters, d_panels = system.describe()
    a_max = 0
    for i in system.shape:
        module_name = i.array.dump()['panel']
        if d_panels.has_key(module_name):
            module = modules.Module(module_name)
            notes.append("PV Module Ratings @ STC")
            notes.append("Module Make: %s" % module.make)
            notes.append("Module Model: %s" % module.model)
            notes.append("Quantity: %s" % d_panels[module_name])
            notes.append("Max Power-Point Current (Imp): %s A" % module.i_mpp)
            notes.append("Max Power-Point Voltage (Vmp): %s V" % module.v_mpp)
            notes.append("Open-Circuit Voltage (Voc): %s V" % module.v_oc)
            notes.append("Short-Circuit Current (Isc): %s A" % module.i_sc)
            notes.append("Maximum Power (Pmax): %s W" % round(module.p_max, 1))

            notes.append("")
            d_panels.pop(module_name)
        if d_inverters.has_key(i.model):
            notes.append("Inverter Make: %s" % i.make)
            notes.append("Inverter Model: %s" % i.model)
            notes.append("Quantity: %s" % d_inverters[i.model])
            notes.append("Max Power: %s KW" % round(i.p_aco/1000.0, 1))
            #this is hack... This should be calculated based upon power cores
            if hasattr(i, 'current'):
                notes.append("Max AC Current: %s A" % round(i.current, 1))
            elif i.ac_voltage == 480:
                notes.append("Max AC Current: %s A" % \
                        round(i.p_aco*1.0/i.ac_voltage/3**.5, 1))
            else:
                notes.append("Max AC Current: %s A" % \
                        round(i.p_aco*1.0/i.ac_voltage, 1))
            #greater than 1 in parallel
            if i.array.mcount() > 1:
                notes.append("DC Operating Current: %s A" % \
                        round(i.array.i_mpp(), 1))
                notes.append("DC Short Circuit Current: %s A" % \
                        round(i.array.i_sc(), 1))
            #greater than 1 in series
            if i.array.mcount() > 1:
                notes.append("DC Operating Voltage: %s V" % \
                        round(i.array.v_dc(), 1))
                notes.append("System Max DC Voltage: %s V" % \
                        round(i.array.v_max(mintemp), 1))
                if i.array.v_max(mintemp) > 600:
                    logger.warning("WARNING: Array exceeds 600V DC")
                notes.append("Pnom Ratio: %s" % \
                        round((i.array.p_max/i.p_aco), 2))
                if (i.array.v_dc(twopercent_temp) * .9) < i.mppt_low:
                    logger.warning("WARNING: " \
                            "Array IV Knee drops out of Inverter range")
                if (i.array.p_max/i.p_aco) < 1.1:
                    logger.warning("WARNING: Array potentially undersized")
            notes.append("")
            d_inverters.pop(i.model)
        if i.array.v_max(mintemp) > a_max:
            a_max = i.array.v_max(mintemp)

    notes.append("Array Azimuth: %s Degrees" % system.azimuth)
    notes.append("Array Tilt: %s Degrees" % system.tilt)
    sols_9 = system.solstice(9)
    sols_15 = system.solstice(15)
    notes.append("December 21 9:00 AM Sun Azimuth: %s Degrees" % \
            (round(degrees(sols_9[1]), 1)))
    notes.append("December 21 9:00 AM Sun Altitude: %s Degrees" % \
            (round(degrees(sols_9[0]), 1)))
    notes.append("December 21 3:00 PM Sun Azimuth: %s Degrees" % \
            (round(degrees(sols_15[1]), 1)))
    notes.append("December 21 3:00 PM Sun Altitude: %s Degrees" % \
            (round(degrees(sols_9[0]), 1)))
    if 'geomag' in sys.modules:
        notes.append("Magnetic declination: %s Degrees" % \
                round(geomag.declination(dlat=system.place[0], \
                dlon=system.place[1])))
    notes.append("Minimum Row space ratio: %s" % \
            round(system.min_row_space(1.0), 2))
    if __name__ == '__main__':
        print "\n".join(notes)
    else:
        logger.info("Plant Details:\n" + "\n".join(notes))

    print ""
    print "Minimum Bundle"
    min_c = vd.vd(a_ac, 5, verbose=False)
    try:
        ee.assemble(min_c, a_ac, conduit='STEEL')
        if run > 0:
            print "Long Run"
            min_c = vd.vd(a_ac, run, v=i.ac_voltage, t_amb=15, pf=.95, \
                    material='AL', verbose=False)
            ee.assemble(min_c, a_ac, conduit='PVC')
    except:
        print "Warning: Multiple sets of conductors"
    return notes

def micro_calcs(system, drop, v_nominal=240):
    """page 4"""
    print ""
    print vd.vd(sum([i.p_aco for i in system.shape])/v_nominal, drop)

def write_notes(system, filename='output', v_nominal=240.0):
    """file out expedited permit form with system details"""
    station_class = 1
    dummy, usaf = geo.closest_usaf(geo.zip_coordinates(system.zipcode), \
            station_class)
    mintemp = eere.minimum(usaf)
    twopercent_temp = eere.twopercent(usaf)
    fields = []
    for i in set(system.shape):
        module_name = i.array.dump()['panel']
        module = modules.Module(module_name)
        print "PV Module Ratings @ STC"
        print "Module Make:", module.make
        fields.append(('Text1ModuleMake', module.make))
        print "Module Model:", module.model
        fields.append(('Text1ModuleModel', module.model))
        print "Max Power-Point Current (Imp):", module.i_mpp
        fields.append(('MAX POWERPOINT CURRENT IMP', module.i_mpp))
        print "Max Power-Point Voltage (Vmp):", module.v_mpp
        fields.append(('MAX POWERPOINT VOLTAGE VMP', module.v_mpp))
        print "Open-Circuit Voltage (v_oc):", module.v_oc
        fields.append(('OPENCIRCUIT VOLTAGE VOC', module.v_oc))
        print "Short-Circuit Current (i_sc):", module.i_sc
        fields.append(('SHORTCIRCUIT CURRENT ISC', module.i_sc))
        fields.append(('MAX SERIES FUSE OCPD', '15'))
        print "Maximum Power (p_max):", module.p_max
        fields.append(('MAXIMUM POWER PMAX', module.p_max))
        print "Module Rated Max Voltage:", module.Vrated
        fields.append(('MAX VOLTAGE TYP 600VDC', module.Vrated))
        fields.append(('VOC TEMP COEFF mVoC or oC', round(module.tk_v_oc, 2)))
        fields.append(('VOC TEMP COEFF mVoC', 'On'))
        print "Inverter Make:", i.make
        fields.append(('INVERTER MAKE', i.make))
        print "Inverter Model:", i.model
        fields.append(('INVERTER MODEL', i.model))
        print "Max Power", i.p_aco
        fields.append(('MAX POWER  40oC', i.p_aco))
        fields.append(('NOMINAL AC VOLTAGE', 240))
        print "Max AC Current: %s" % round(i.p_aco/v_nominal, 2)
        fields.append(('MAX AC CURRENT', round(i.p_aco/v_nominal, 2)))
        fields.append(('MAX DC VOLT RATING', i.mppt_hi))
        print "Max AC OCPD Rating: %s" % ee.ocp_size(i.p_aco/v_nominal*1.25)
        print "Max System Voltage:", round(module.v_max(mintemp), 1)
    print "AC Output Current: %s" % \
            round(sum([i.p_aco for i in system.shape])/v_nominal, 2)
    fields.append(('AC OUTPUT CURRENT', \
            round(sum([i.p_aco for i in system.shape])/v_nominal, 2)))
    print "Nominal AC Voltage: %s" % v_nominal
    fields.append(('NOMINAL AC VOLTAGE_2', i.ac_voltage))

    print "Minimum Temperature: %s C" % mintemp
    print "2 Percent Max: %s C" % twopercent_temp
    from fdfgen import forge_fdf
    fdf = forge_fdf("", fields, [], [], [])
    fdf_file = open("data.fdf", "w")
    fdf_file.write(fdf)
    fdf_file.close()
    import shlex
    from subprocess import call
    cmd = shlex.split("pdftk Example2-Micro-Inverter.pdf fill_form data.fdf" \
            "%s output.pdf flatten" % filename)
    rc = call(cmd)
    return rc

if __name__ == "__main__":
    import argparse
    import json
    PARSER = argparse.ArgumentParser(description="Model a PV system. " \
            "Currently displays annual output and graph")
    PARSER.add_argument('-f', '--file')
    ARGS = vars(PARSER.parse_args())
    try:
        #start program
        JSON_P = json.loads(open(ARGS['file']).read())
        if 'address' in JSON_P:
            print '%s - %s %s' % \
                (JSON_P['system_name'].upper(), JSON_P['address'], \
                JSON_P['zipcode'])
        PLANT = pv.json_system(JSON_P)
        if "run" in JSON_P:
            string_notes(PLANT, JSON_P["run"])
        else:

            string_notes(PLANT)
        #graph = plant.model()
        #graph.savefig('pv_output_%s.png' % plant.zipcode)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
