"""Calculate expedited permit process info"""

import modules
import inverters
import epw
import geo
import pv
import ee


def micro_notes(system, Vnominal=240.0):
    """page 5"""
    stationClass = 1
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(system.zipcode), stationClass)
    mintemp = epw.minimum(usaf)
    twopercentTemp = epw.twopercent(usaf)
    for i in set(system.shape):
        print "PV Module Ratings @ STC"
        print "Module Make:", i.array.make
        print "Module Model:", i.array.model
        print "Max Power-Point Current (Imp):",i.array.Impp
        print "Max Power-Point Voltage (Vmp):",i.array.Vmpp
        print "Open-Circuit Voltage (Voc):",i.array.Vmax(mintemp)
        print "Short-Circuit Current (Isc):",i.array.Isc
        print "Maximum Power (Pmax):",i.array.Pmax
        print "Module Rated Max Voltage:",i.array.Vrated
        print "Inverter Make:",i.make
        print "Inverter Model:",i.model
        print "Max Power", i.Paco
        print "Max AC Current: %s" % round(i.Paco/Vnominal,2)
        print "Max AC OCPD Rating: %s" % ee.ocpSize(i.Paco/Vnominal*1.25)
        print "Max System Voltage:",round(i.array.Vmax(mintemp),1)
    print "AC Output Current: %s" % \
            round(sum([i.Paco for i in system.shape])/Vnominal,2)
    print "Nominal AC Voltage: %s" % Vnominal

    print "Minimum Temperature: %s C" % mintemp
    print "2%% Max: %s C" % twopercentTemp

def string_notes(system, Vnominal=240.0):
    """page 5"""
    stationClass = 1
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(system.zipcode), stationClass)
    mintemp = epw.minimum(usaf)
    twopercentTemp = epw.twopercent(usaf)
    for i in set(system.shape):
        print "PV Module Ratings @ STC"
        print "Module Make:", i.array.make
        print "Module Model:", i.array.model
        print "Max Power-Point Current (Imp):",i.array.panel.Impp
        print "Max Power-Point Voltage (Vmp):",i.array.panel.Vmpp
        print "Open-Circuit Voltage (Voc):",i.array.panel.Vmax(mintemp)
        print "Short-Circuit Current (Isc):",i.array.panel.Isc
        print "Maximum Power (Pmax):",i.array.panel.Pmax
        print "Module Rated Max Voltage:",i.array.panel.Vrated
        print "Inverter Make:",i.make
        print "Inverter Model:",i.model
        print "Max Power:", i.Paco
        print "Max AC Current: %s" % round(i.Paco/Vnominal,2)
        print "Max AC OCPD Rating: %s" % ee.ocpSize(i.Paco/Vnominal*1.25)
        print "Max System Voltage:",round(i.array.Vmax(mintemp),1)
    print "AC Output Current: %s" % \
            round(sum([i.Paco for i in system.shape])/Vnominal,2)
    print "Nominal AC Voltage: %s" % Vnominal

    print "Minimum Temperature: %s C" % mintemp
    print "2%% Max: %s C" % twopercentTemp

if __name__ == "__main__":
    plant = pv.system(pv.default* 4)
    plant.setZipcode(17601)
    #micro_notes(plant)

    plant = pv.system([inverters.sb8000us(modules.pvArray(modules.mage250(),13,3))])
    plant.setZipcode(44050)
    string_notes(plant)

