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
    print "2%% Max: %s C" % twopercentTemp

def micro_calcs(system,d,Vnominal=240):
    """page 4"""
    print ""
    print vd.vd(sum([i.Paco for i in system.shape])/Vnominal,d)
    pass


if __name__ == "__main__":
    plant = pv.system(pv.default* 24)
    plant.setZipcode(17601)
    micro_notes(plant)
    micro_calcs(plant,50)
    print ""
    plant = pv.system([inverters.sb8000us(modules.pvArray(modules.mage250(),13,3))])
    plant.setZipcode(44050)
    #plant.setZipcode(17601)
    string_notes(plant)

