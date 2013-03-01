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

"""Calculate expedited permit process info"""

import modules
import inverters
import epw
import geo
import pv
import ee
import vd


def micro_notes(system, Vnominal=240.0):
    """page 5"""
    stationClass = 3
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(system.zipcode), stationClass)
    mintemp = epw.minimum(usaf)
    twopercentTemp = epw.twopercent(usaf)
    ac_rated = 0
    dc_rated = 0
    for i in system.shape:
        dc_rated += i.array.Pmax
        ac_rated += i.Paco
    descrip = system.describe()
    #print descrip
    print "%s KW AC RATED" % round(ac_rated/1000.0,2)
    print "%s KW DC RATED" % round(dc_rated/1000.0,2)
    print ""
    print "AC Output Current: %s A" % \
            round(sum([i.Paco for i in system.shape])/Vnominal,2)
    print "Nominal AC Voltage: %s V" % Vnominal
    print "Weather Station: %s" % name
    print "Minimum Temperature: %s C" % mintemp
    print "2%% Max Temperature: %s C" % twopercentTemp
    for i in set(system.shape):
        print "PV Module Ratings @ STC"
        print "Module Make: %s" % i.array.make
        print "Module Model: %s" % i.array.model
        print "Quantity: %s" % descrip[i.array.model]
        print "Max Power-Point Current (Imp): %s A" % i.array.Impp
        print "Max Power-Point Voltage (Vmp): %s V" % i.array.Vmpp
        print "Open-Circuit Voltage (Voc): %s V" % i.array.Voc
        print "Short-Circuit Current (Isc): %s A" % i.array.Isc
        print "Maximum Power (Pmax): %s W" % i.array.Pmax
        print "Module Rated Max Voltage: %s V" % i.array.Vrated
        print ""
        print "Inverter Make: %s" % i.make
        print "Inverter Model: %s" % i.model
        print "Quantity: %s" % descrip[i.model]
        print "Max Power: %s W" % i.Paco
        print "Max AC Current: %s A" % round(i.Paco/Vnominal,2)
        #print "Max AC OCPD Rating: %s A" % ee.ocpSize(i.Paco/Vnominal*1.25)
        print "Max System DC Voltage: %s V" %round(i.array.Vmax(mintemp),1)

def string_notes(system):
    """page 5"""
    stationClass = 3
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(system.zipcode), stationClass)
    mintemp = epw.minimum(usaf)
    twopercentTemp = epw.twopercent(usaf)
    ac_rated = 0
    dc_rated = 0
    for i in system.shape:
        dc_rated += i.array.Pmax
        ac_rated += i.Paco
    notes = []
    notes.append("%s KW AC RATED" % round(ac_rated/1000.0,2))
    notes.append("%s KW DC RATED" % round(dc_rated/1000.0,2))
    notes.append("")
    di, dp = system.describe()
    aMax = 0
    for i in system.shape:
        if dp.has_key(i.array.panel.model):
            notes.append( "PV Module Ratings @ STC")
            notes.append("Module Make: %s" % i.array.panel.make)
            notes.append("Module Model: %s" % i.array.panel.model)
            notes.append("Quantity: %s" % dp[i.array.panel.model])
            notes.append("Max Power-Point Current (Imp): %s A" % i.array.panel.Impp)
            notes.append("Max Power-Point Voltage (Vmp): %s V" % i.array.panel.Vmpp)
            notes.append("Open-Circuit Voltage (Voc): %s V" % i.array.panel.Voc)
            notes.append("Short-Circuit Current (Isc): %s A" % i.array.panel.Isc)
            notes.append("Maximum Power (Pmax): %s W" % round(i.array.panel.Pmax,1))
            notes.append("Module Rated Max Voltage: %s V" % i.array.panel.Vrated)
            notes.append("")
            dp.pop(i.array.panel.model)
        if di.has_key(i.model):
            notes.append("Inverter Make: %s" % i.make)
            notes.append("Inverter Model: %s" % i.model)
            notes.append("Quantity: %s" % di[i.model])
            notes.append("Max Power: %s W" % i.Paco)
            notes.append("Max AC Current: %s A" % round(i.Paco*1.0/i.ac_voltage,1))
            #print "Max AC OCPD Rating: %s A" % ee.ocpSize(i.Paco/i.ac_voltage*1.25)
            notes.append("")
            di.pop(i.model)
        if i.array.Vmax(mintemp) > aMax:
            aMax = i.array.Vmax(mintemp)
    #BUG: This doesn't work for 3 phase
    if system.phase == 1:
        notes.append( "System AC Output Current: %s A" % \
                round(sum([i.Paco for i in system.shape])/i.ac_voltage,1))
    else:
        notes.append( "System AC Output Current: %s A" % \
                round(sum([i.Paco for i in system.shape])/i.ac_voltage/3**.5,1))

    notes.append("Nominal AC Voltage: %s V" % i.ac_voltage)

    notes.append("Minimum Temperature: %s C" % mintemp)
    notes.append("2 Percent Max Temperature: %s C" % twopercentTemp)
    notes.append("System Max DC Voltage: %s V" % round(aMax,1))
    print "\n".join(notes)
    return notes

def micro_calcs(system,d,Vnominal=240):
    """page 4"""
    print ""
    print vd.vd(sum([i.Paco for i in system.shape])/Vnominal,d)
    pass

def write_notes(system, Vnominal=240.0):
    stationClass = 1
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(system.zipcode), stationClass)
    mintemp = epw.minimum(usaf)
    twopercentTemp = epw.twopercent(usaf)
    fields = []
    for i in set(system.shape):
        print "PV Module Ratings @ STC"
        print "Module Make:", i.array.make
        fields.append(('Text1ModuleMake',i.array.make))
        print "Module Model:", i.array.model
        fields.append(('Text1ModuleModel',i.array.model))
        print "Max Power-Point Current (Imp):",i.array.Impp
        fields.append(('MAX POWERPOINT CURRENT IMP',i.array.Impp))
        print "Max Power-Point Voltage (Vmp):",i.array.Vmpp
        fields.append(('MAX POWERPOINT VOLTAGE VMP',i.array.Vmpp))
        print "Open-Circuit Voltage (Voc):",i.array.Voc
        fields.append(('OPENCIRCUIT VOLTAGE VOC',i.array.Voc))
        print "Short-Circuit Current (Isc):",i.array.Isc
        fields.append(('SHORTCIRCUIT CURRENT ISC',i.array.Isc))
        fields.append(('MAX SERIES FUSE OCPD','15'))
        print "Maximum Power (Pmax):",i.array.Pmax
        fields.append(('MAXIMUM POWER PMAX',i.array.Pmax))
        print "Module Rated Max Voltage:",i.array.Vrated
        fields.append(('MAX VOLTAGE TYP 600VDC',i.array.Vrated))
        fields.append(('VOC TEMP COEFF mVoC or oC',round(i.array.TkVoc,2)))
        fields.append(('VOC TEMP COEFF mVoC','On'))
        print "Inverter Make:",i.make
        fields.append(('INVERTER MAKE',i.make))
        print "Inverter Model:",i.model
        fields.append(('INVERTER MODEL',i.model))
        print "Max Power", i.Paco
        fields.append(('MAX POWER  40oC',i.model))
        fields.append(('NOMINAL AC VOLTAGE',240))
        print "Max AC Current: %s" % round(i.Paco/Vnominal,2)
        fields.append(('MAX AC CURRENT', round(i.Paco/Vnominal,2)))
        fields.append(('MAX DC VOLT RATING',i.model))
        print "Max AC OCPD Rating: %s" % ee.ocpSize(i.Paco/Vnominal*1.25)
        print "Max System Voltage:",round(i.array.Vmax(mintemp),1)
    print "AC Output Current: %s" % \
            round(sum([i.Paco for i in system.shape])/Vnominal,2)
    fields.append(('AC OUTPUT CURRENT', \
            round(sum([i.Paco for i in system.shape])/Vnominal,2)))
    print "Nominal AC Voltage: %s" % Vnominal
    fields.append(('NOMINAL AC VOLTAGE_2',i.ac_voltage))

    print "Minimum Temperature: %s C" % mintemp
    print "2 Percent Max: %s C" % twopercentTemp
    from fdfgen import forge_fdf
    fdf = forge_fdf("",fields,[],[],[])
    fdf_file = open("data.fdf","w")
    fdf_file.write(fdf)
    fdf_file.close()
    import shlex
    from subprocess import call
    cmd = shlex.split("pdftk Example2-Micro-Inverter.pdf fill_form data.fdf output output.pdf flatten")
    rc = call(cmd)

if __name__ == "__main__":
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser(description='Model a PV system. Currently displays annual output and graph')
    parser.add_argument('-f', '--file')
    args = vars(parser.parse_args())
    try:
        #start program
        plant = pv.jsonToSystem(json.loads(open(args['file']).read()))
        string_notes(plant)
        #graph = plant.model()
        #graph.savefig('pv_output_%s.png' % plant.zipcode)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
