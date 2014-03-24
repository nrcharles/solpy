"""
Parametric Design tools
"""
# This program is free software. See terms in LICENSE file.

import copy
import geo
import epw
import pv
import json


def fill(inverter, zipcode, acDcRatio = 1.2, mount="Roof", stationClass = 1, \
        Vmax = 600, bipolar= True):
    """String sizing"""
    tDerate = {"Roof":30,
            "Ground":25,
            "Pole":20}
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(zipcode), stationClass)
    maxV = inverter.array.panel.Vmax(epw.minimum(usaf))
    #NREL suggests that long term degradation is primarily current not voltage
    derate20 = .97
    minV = inverter.array.panel.Vmin(epw.twopercent(usaf),tDerate[mount]) * \
            derate20
    #print "MinV", minV
    if inverter.vdcmax != 0:
         Vmax = inverter.vdcmax
    smax = int(Vmax/maxV)
    #range to search
    pTol = .30
    inverterNominal = inverter.Paco
    psize = inverter.array.panel.Pmax
    solutions = []

    Imax = max(inverter.idcmax,inverter.Pdco*1.0/inverter.mppt_low)
    stringMax = int(round(Imax/inverter.array.panel.Impp))+1

    #Diophantine equation
    for s in range(smax+1):
        if (s*minV) >= inverter.mppt_low:
            for p in range(stringMax):
                pRatio = p*s*psize*1.0/inverterNominal
                if pRatio < (acDcRatio*(1+pTol)) and \
                        pRatio > (acDcRatio*(1-pTol)):
                            inverter.array.shape = [s]*p
                            t = copy.deepcopy(inverter)
                            t.minV = s*minV
                            t.maxV = s*maxV
                            solutions.append(t)
    return solutions

def knapsack(items, maxweight):
    #http://codereview.stackexchange.com/questions/20569/dynamic-programming-solution-to-knapsack-problem
    bestvalues = [[0] * (maxweight + 1)
                  for i in xrange(len(items) + 1)]

    for i, (value, weight, systemDict) in enumerate(items):
        i += 1
        for capacity in xrange(maxweight + 1):
            if weight > capacity:
                bestvalues[i][capacity] = bestvalues[i - 1][capacity]
            else:
                candidate1 = bestvalues[i - 1][capacity]
                candidate2 = bestvalues[i - 1][capacity - weight] + value
                bestvalues[i][capacity] = max(candidate1, candidate2)

    reconstruction = []
    i = len(items)
    j = maxweight
    while i > 0:
        if bestvalues[i][j] != bestvalues[i - 1][j]:
            reconstruction.append(items[i - 1])
            j -= items[i - 1][1]
        i -= 1

    reconstruction.reverse()

    return bestvalues[len(items)][maxweight], reconstruction

def design(reqsStr):
#def design(DCsize, panellist, inverterlist, details):
    """parts selection algorithm"""
    #create all valid inverter panel combinations for location
    reqs = json.loads(reqsStr)
    validC = []
    clean = []
    zc = reqs['zipcode']
    #for inverterModel,inverterCost in inverterlist:
    for inverterModel in reqs['inverter options']:
        #for panelModel,panelPrice in panellist:
        for panelModel in reqs['panel options']:
            system = inverters.inverter(inverterModel,\
                    modules.pvArray(modules.module(panelModel),[2]))
            configs = fill(system,zc)
            for config in configs:
                validC.append(config)
                print config, config.array, config.array.panel, \
                        config.array.output(1000), config.ratio()

                reqs['array'] = [config.dump()]
                plant = pv.jsonToSystem(reqs)
                output = plant.model()
                print "year 1 kwh", output.annualOutput
                config.yearOne = output.annualOutput

                #value, weight, systemDict
                option = [(int(config.yearOne), \
                        int(config.array.output(1000)), config.dump())]

                #hack to allow semetery
                scale = int(reqs['desired size'] / config.array.output(1000))
                clean += option * scale

    #knapsack problem weight is system DC size and value is annual output
    #this could be expanded with different constraints for different rankings
    systemWeight, systemSet = knapsack(clean, reqs['desired size'])

    reqs['array'] = [subA for v,w,subA in systemSet]
    return reqs

if __name__ == "__main__":
    import inverters
    import modules
    import expedite

    #sketchup may be a good way to input this data
    testreqs = """{"system_name":"HAPPY CUSTOMER",
        "address":"15013 Denver W Pkwy, Golden, CO",
        "zipcode":"80401",
        "phase":1,
        "voltage":240,
        "service":200,
        "tilt":25,
        "azimuth":180,
        "inverter options":["SMA America: SB4000TL-US-22 (240V) 240V", 
            "SMA America: SB5000TL-US-22 (240V) 240V", 
            "SMA America: SB6000US-11 240V"],
        "panel options":["Axitec : AC-250P-156-60S *"],
        "homerun":150,
        "space":[[10,5]],
        "desired size":130000}"""
    shade = """{
        "shade":{"0": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "1": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 1.0, 0.2, 0.0, 0.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "2": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 1.0, 1.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "3": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "4": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "5": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "6": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "7": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "8": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8, 1.0, 1.0, 0.1, 0.0, 0.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "9": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.9, 1.0, 0.1, 0.0, 0.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "10": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 1.0, 1.0, 1.0, 1.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "11": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 1.0, 1.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}
            }"""

    proposed = design(testreqs)
    proposedPlant = pv.jsonToSystem(proposed)
    print json.dumps(proposedPlant.dump(), sort_keys=True, indent=4, \
            separators=(',', ': '))
    expedite.string_notes(proposedPlant)
