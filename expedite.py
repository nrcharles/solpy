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
    for i in set(system.shape):
        print "PV Module Ratings @ STC"
        print "Module Make: %s" % i.array.make
        print "Module Model: %s" % i.array.model
        print "Max Power-Point Current (Imp): %s A" % i.array.Impp
        print "Max Power-Point Voltage (Vmp): %s V" % i.array.Vmpp
        print "Open-Circuit Voltage (Voc): %s V" % i.array.Voc
        print "Short-Circuit Current (Isc): %s A" % i.array.Isc
        print "Maximum Power (Pmax): %s W" % i.array.Pmax
        print "Module Rated Max Voltage: %s V" % i.array.Vrated
        print "Inverter Make: %s" % i.make
        print "Inverter Model: %s" % i.model
        print "Max Power: %s W" % i.Paco
        print "Max AC Current: %s A" % round(i.Paco/Vnominal,2)
        print "Max AC OCPD Rating: %s A" % ee.ocpSize(i.Paco/Vnominal*1.25)
        print "Max System Voltage: %s V" %round(i.array.Vmax(mintemp),1)
    print "AC Output Current: %s A" % \
            round(sum([i.Paco for i in system.shape])/Vnominal,2)
    print "Nominal AC Voltage: %s V" % Vnominal

    print "Minimum Temperature: %s C" % mintemp
    print "2%% Max: %s C" % twopercentTemp

def string_notes(system, Vnominal=240.0):
    """page 5"""
    stationClass = 3
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(system.zipcode), stationClass)
    mintemp = epw.minimum(usaf)
    twopercentTemp = epw.twopercent(usaf)
    for i in set(system.shape):
        print "PV Module Ratings @ STC"
        print "Module Make: %s" % i.array.make
        print "Module Model: %s" % i.array.model
        print "Max Power-Point Current (Imp): %s A" % i.array.panel.Impp
        print "Max Power-Point Voltage (Vmp): %s V" % i.array.panel.Vmpp
        print "Open-Circuit Voltage (Voc): %s V" % i.array.panel.Voc
        print "Short-Circuit Current (Isc): %s A" % i.array.panel.Isc
        print "Maximum Power (Pmax): %s W" % i.array.panel.Pmax
        print "Module Rated Max Voltage: %s V" % i.array.panel.Vrated
        print "Inverter Make: %s" % i.make
        print "Inverter Model: %s" % i.model
        print "Max Power: %s W" % i.Paco
        print "Max AC Current: %s A" % round(i.Paco/Vnominal,2)
        print "Max AC OCPD Rating: %s A" % ee.ocpSize(i.Paco/Vnominal*1.25)
        print "Max System Voltage: %s V" % round(i.array.Vmax(mintemp),1)
    print "AC Output Current: %s A" % \
            round(sum([i.Paco for i in system.shape])/Vnominal,2)
    print "Nominal AC Voltage: %s V" % Vnominal
    

    print "Minimum Temperature: %s C" % mintemp
    print "2%% Max Temperature: %s C" % twopercentTemp

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
    fields.append(('NOMINAL AC VOLTAGE_2',240))

    print "Minimum Temperature: %s C" % mintemp
    print "2%% Max: %s C" % twopercentTemp
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
    plant = pv.system(pv.default* 100)
    print pv.__file__
    import os
    (filepath, filename) = os.path.split(pv.__file__)
    print filepath
    plant.setZipcode(21863)
    #write_notes(plant)
    micro_notes(plant)
    micro_calcs(plant,220)
    print ""
    #plant = pv.system([inverters.sb7000us(modules.pvArray(modules.mage250(),14,2))]*4 \
    #        +[inverters.sb6000us(modules.pvArray(modules.mage250(),14,2))]*11)
    #plant.setZipcode(21863)
    #plant.setZipcode(17601)
    #string_notes(plant)

