"""
Parametric Design tools
"""
# This program is free software. See terms in LICENSE file.

import copy
import epw
import pv
import json

def tools_fill(inverter, zipcode, acDcRatio = 1.2, mount="Roof", stationClass = 1, Vmax = 600, bipolar= True):
    #deprecated legacy function
    return [format(i) for i in fill(**locals())]

def format(inverter):
    """'9769.5W : 13S x 3P : ratio 1.22 : 314.0 - 552.0 V'"""
    DC = inverter.array.output(1000)
    ratio = DC/inverter.Paco
    return '%sW : %s : ratio %s : %s - %s V' % (DC, inverter.array, \
            round(ratio,2), round(inverter.minV), round(inverter.maxV))

def fill(inverter, zipcode, acDcRatio = 1.2, mount="Roof", stationClass = 1, \
        Vmax = 600, bipolar= True):
    import geo
    """String sizing"""
    tDerate = {"Roof":30,
            "Ground":25,
            "Pole":20}

    #csv is performance hit
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(zipcode), stationClass)
    maxV = inverter.array.panel.Vmax(epw.minimum(usaf))
    #NREL suggests that long term degradation is primarily current not voltage
    derate20 = .97
    minV = inverter.array.panel.Vmin(epw.twopercent(usaf),tDerate[mount]) * \
            derate20

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

def generateOptions(inverterName,moduleName,zipcode, channels=1, acDcRatio = 1.2, \
        mount="Roof", stationClass = 1, Vmax = 600, bipolar= True):
    import geo
    import inverters
    import modules
    module = modules.module(moduleName)
    inverter = inverters.inverter(inverterName)
    """String sizing"""
    tempAdder = {"Roof":30,
            "Ground":25,
            "Pole":20}
    #NREL suggests that long term degradation is primarily current not voltage
    derate20 = .97

    #csv is performance hit
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(zipcode), stationClass)
    epw_min = epw.minimum(usaf)
    moduleMaxVoltage = module.Vmax(epw_min)
    epw2 = epw.twopercent(usaf)
    moduleMinVoltage = module.Vmin(epw2,tempAdder[mount]) * derate20

    if inverter.vdcmax != 0:
         Vmax = inverter.vdcmax
    maxlen = int(Vmax/moduleMaxVoltage)
    minlen = int(inverter.mppt_low/moduleMinVoltage) + 1
    inverter.array = modules.array(module,[{'series':minlen}]*inverter.mppt_channels)
    inverter.array.minlength(minlen)
    inverter.array.maxlength(maxlen)
    #range to search
    pTol = .30
    inverterNominal = inverter.Paco
    solutions = []
    while (inverter.array.output(1000) < inverterNominal * (acDcRatio + pTol)):
        inverter.array.inc()
        print inverter.array
        print inverter.array.output(1000),inverter.ratio()
        t = copy.deepcopy(inverter)
        t.maxV = t.array.Vmax(epw_min)
        t.minV = t.array.Vmin(epw2,tempAdder[mount])
        solutions.append(t)
    return solutions

    #Imax = max(inverter.idcmax,inverter.Pdco*1.0/inverter.mppt_low)
    #stringMax = int(round(Imax/inverter.array.panel.Impp))+1

    #Diophantine equation
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
    systemSet = [subA for v,w,subA in reconstruction]

    return bestvalues[len(items)][maxweight], systemSet

def efficient(items, maxweight):
    """symetric design of the most efficeint inverter panel combo"""
    mostEff = [None, None, None]
    for (value, weight, systemDict) in items:
        eff = value/float(weight)
        if eff > mostEff[0]:
            mostEff = [eff,weight,systemDict]
    scale = maxweight/mostEff[1]
    result = [mostEff[2]]*scale
    return (mostEff[1]*scale, result)

def combinations(a,b):
    s = []
    for i in a:
        for j in b:
            s.append((i,j))
    return s

def performanceModelPlant(jsonDef):
    plant = pv.jsonToSystem(jsonDef)
    yearone = plant.model()
    PDC = sum([i.array.output(1000) for i in plant.shape])
    plantDict = plant.dump()
    plantDict['yearone'] = yearone.annualOutput
    plantDict['DCnominal'] = int(PDC)
    return plantDict

def performanceModelSet(clist):
    """wrapper for distributed performance modelling"""
    CSTAT = celery_worker_status()
    if not 'ERROR' in CSTAT:
        from celery import group
        import pmodel
        #print CSTAT
        return group(pmodel.modelPlant.s(i) for i in clist)().get()
    else:
        return [performanceModelPlant(pJSON) for pJSON in clist]

def design(reqsStr):
    """parts selection algorithm. """
    reqs = json.loads(reqsStr)
    validC = []
    optionSet = []
    zc = reqs['zipcode']

    for inverterModel, panelModel in combinations(reqs['inverter options'],\
            reqs['panel options']):
        system = inverters.inverter(inverterModel,\
                modules.pvArray(modules.module(panelModel),[2]))
        configs = fill(system,zc)
        for config in configs:
            validC.append(config)
            print config, config.array, config.array.panel, \
                    config.array.output(1000), config.ratio()

            reqs['array'] = [config.dump()]
        optionSet.append(copy.deepcopy(reqs))

    performanceResults = performanceModelSet(optionSet)

    configSet= []
    for o in performanceResults:
        #hack to expand for semetery
        scale = reqs['desired size'] // o['DCnominal']
        configSet += [(o['yearone'],o['DCnominal'],o['array'][0])] * scale

    suggested = []

    #knapsack problem weight is system DC size and value is annual output
    #this could be expanded with different constraints for different rankings
    systemWeight, systemSet = knapsack(configSet, reqs['desired size'])
    reqs['array'] = systemSet 
    reqs['notes'] = 'Maximum size'
    suggested.append(copy.deepcopy(reqs))

    systemWeight, systemSet = efficient(configSet, reqs['desired size'])
    reqs['array'] = systemSet
    reqs['notes'] = 'Maximum symetric efficiency'
    suggested.append(copy.deepcopy(reqs))

    return suggested

def celery_worker_status():
    ERROR_KEY = "ERROR"
    try:
        from celery.task.control import inspect
        insp = inspect()
        d = insp.stats()
        if not d:
            d = { ERROR_KEY: 'No running Celery workers were found.' }
    except IOError as e:
        from errno import errorcode
        msg = "Error connecting to the backend: " + str(e)
        if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
            msg += ' Check that the RabbitMQ server is running.'
        d = { ERROR_KEY: msg }
    except ImportError as e:
        d = { ERROR_KEY: str(e)}
    return d

if __name__ == "__main__":
    import inverters
    import modules
    import expedite
    import argparse
    import sys

    #sketchup may be a good way to input this data
    testreqs = """{"system_name":"HAPPY CUSTOMER",
        "address":"15013 Denver W Pkwy, Golden, CO",
        "zipcode":"80401",
        "phase":1,
        "voltage":240,
        "service":200,
        "tilt":25,
        "azimuth":180,
        "notes":"reqs",
        "inverter options":["SMA America: SB5000TL-US-22 (240V) 240V", 
            "SMA America: SB7000TL-US-12 (240V) 240V",
            "SMA America: SB8000TL-US-12 (240V) 240V",
            "SMA America: SB9000TL-US-12 (240V) 240V",
            "SMA America: SB6000US-11 240V"],
        "panel options":["Axitec : AC-250P-156-60S *"],
        "homerun":150,
        "space":[[10,5]],
        "desired size":25000}"""
    shade = """{
        "shade":{
            "0": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.1, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "1": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 1.0, 0.2, 0.0, 
            0.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.4, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "2": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 1.0, 1.0, 0.0, 0.0, 
            0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "3": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 1.0, 1.0, 1.0, 1.0, 1.0, 
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "4": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "5": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.3, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "6": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "7": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 1.0, 1.0, 1.0, 1.0, 1.0, 
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "8": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8, 1.0, 1.0, 0.1, 0.0, 
            0.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.6, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "9": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.9, 1.0, 0.1, 0.0, 
            0.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "10": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.4, 1.0, 1.0, 1.0, 1.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
            "11": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.1, 1.0, 1.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}
            }"""

    parser = argparse.ArgumentParser(description='Design a PV system')
    parser.add_argument('-f', '--file')
    args = vars(parser.parse_args())
    try:
        #start program
        if args['file']:
            testreqs = open(args['file']).read()

        for proposed in design(testreqs):
            proposedPlant = pv.jsonToSystem(proposed)
            print json.dumps(proposedPlant.dump(), sort_keys=True, indent=4, \
                separators=(',', ': '))
            print proposed['notes']
            expedite.string_notes(proposedPlant)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
