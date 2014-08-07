"""
Parametric Design tools
"""
# This program is free software. See terms in LICENSE file.

import copy
import epw
import pv
import json

def tools_fill(inverter, zipcode, ac_dc_ratio=1.2, mount="Roof", \
        station_class=1, v_max=600, bipolar=True):
    """deprecated legacy function"""
    return [str_format(i) for i in fill(**locals())]

def str_format(inverter):
    """format as str: '9769.5W : 13S x 3P : ratio 1.22 : 314.0 - 552.0 V'"""
    DC = inverter.array.output(1000)
    ratio = DC/inverter.p_aco
    return '%sW : %s : ratio %s : %s - %s V' % (DC, inverter.array, \
            round(ratio, 2), round(inverter.min_v), round(inverter.max_v))

def fill(inverter, zipcode, ac_dc_ratio=1.2, mount="Roof", station_class=1, \
        v_max=600, bipolar=True):
    """String sizing"""
    import geo
    t_derate = {"Roof":30, \
            "Ground":25, \
            "Pole":20}

    #csv is performance hit
    name, usaf = geo.closest_usaf(geo.zip_coordinates(zipcode), station_class)
    max_v = inverter.array.panel.v_max(epw.minimum(usaf))
    #NREL suggests that long term degradation is primarily current not voltage
    derate20 = .97
    min_v = inverter.array.panel.v_min(epw.twopercent(usaf), t_derate[mount]) * \
            derate20

    if inverter.vdcmax != 0:
        v_max = inverter.vdcmax
    smax = int(v_max/max_v)
    #range to search
    p_tol = .30
    inverter_nominal = inverter.p_aco
    psize = inverter.array.panel.p_max
    solutions = []

    i_max = max(inverter.idcmax, inverter.p_dco*1.0/inverter.mppt_low)
    string_max = int(round(i_max/inverter.array.panel.i_mpp))+1

    #Diophantine equation
    for s in range(smax+1):
        if (s*min_v) >= inverter.mppt_low:
            for p in range(string_max):
                pRatio = p*s*psize*1.0/inverter_nominal
                if pRatio < (ac_dc_ratio*(1+p_tol)) and \
                        pRatio > (ac_dc_ratio*(1-p_tol)):
                    inverter.array.shape = [s]*p
                    t = copy.deepcopy(inverter)
                    t.min_v = s*min_v
                    t.max_v = s*max_v
                    solutions.append(t)
    return solutions

def generate_options(inverter_name, module_name, zipcode, ac_dc_ratio=1.2, \
        mount="Roof", station_class=1, v_max=600, bipolar=True):
    import geo
    import inverters
    import modules
    module = modules.Module(module_name)
    inverter = inverters.Inverter(inverter_name)
    """String sizing"""
    tempAdder = {"Roof":30,\
            "Ground":25,\
            "Pole":20}
    #NREL suggests that long term degradation is primarily current not voltage
    derate20 = .97

    #csv is performance hit
    name, usaf = geo.closest_usaf(geo.zip_coordinates(zipcode), station_class)
    epw_min = epw.minimum(usaf)
    module_max_voltage = module.v_max(epw_min)
    epw2 = epw.twopercent(usaf)
    module_min_voltage = module.v_min(epw2, tempAdder[mount]) * derate20

    if inverter.vdcmax != 0:
        v_max = inverter.vdcmax
    maxlen = int(v_max//module_max_voltage)
    minlen = int(inverter.mppt_low/module_min_voltage) + 1
    if minlen > maxlen:
        return []
    inverter.array = modules.Array(module, \
            [{'series':minlen}]*inverter.mppt_channels)
    inverter.array.minlength(minlen)
    inverter.array.maxlength(maxlen)
    #range to search
    p_tol = .30
    inverter_nominal = inverter.p_aco
    solutions = []
    while inverter.array.output(1000) < inverter_nominal * \
            (ac_dc_ratio + p_tol):
        inverter.array.inc()
        #print inverter.array
        #print inverter.array.output(1000), inverter.ratio()
        t = copy.deepcopy(inverter)
        t.max_v = t.array.v_max(epw_min)
        t.min_v = t.array.v_min(epw2, tempAdder[mount])
        #print inverter.ratio()
        if inverter.ratio() > ac_dc_ratio*(1. - p_tol):
            solutions.append(t)
    return solutions

    #i_max = max(inverter.idcmax,inverter.p_dco*1.0/inverter.mppt_low)
    #string_max = int(round(i_max/inverter.array.panel.i_mpp))+1

    #Diophantine equation
    return solutions

def knapsack(item_set, maxweight):
    """knapsack problem weight is system DC size and value is annual output
    this could be expanded with different constraints for different rankings"""
    #http://codereview.stackexchange.com/questions/20569/
    #dynamic-programming-solution-to-knapsack-problem
    items = []

    for o in item_set:
        #hack to expand for semetery
        scale = maxweight // o['DCnominal']
        items += [(o['yearone'], o['DCnominal'], o['array'][0])] * scale

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
    system_set = [subA for v, w, subA in reconstruction]

    results = {'algorithm':'knapsack', \
            'notes':'most annual generation', \
            'system_weight':bestvalues[len(items)][maxweight], \
            'system_set': system_set}
    return results

def efficient(items, maxweight):
    """symetric design of the most efficeint inverter panel combo"""
    most_eff = [None, None, None]
    for o in items:
        value = o['yearone']
        weight = o['DCnominal']
        eff = value/float(weight)
        if eff > most_eff[0]:
            most_eff = [eff, weight, o['array'][0]]
    scale = maxweight/most_eff[1]
    system_result = [most_eff[2]]*scale
    results = {'algorithm':'efficient', \
            'notes':'symetric design of most efficient combination', \
            'system_weight':most_eff[1]*scale, \
            'system_set': system_result}
    return results

def combinations(a, b):
    s = []
    for i in a:
        for j in b:
            s.append((i, j))
    return s

def performance_model_plant(jsonDef):
    plant = pv.json_system(jsonDef)
    yearone = plant.model()
    PDC = sum([i.array.output(1000) for i in plant.shape])
    plantDict = plant.dump()
    plantDict['yearone'] = yearone.annual_output
    plantDict['DCnominal'] = int(PDC)
    return plantDict

def performance_model_set(clist):
    """wrapper for distributed performance modelling"""
    CSTAT = celery_worker_status()
    if not 'ERROR' in CSTAT:
        from celery import group
        import pmodel
        #print CSTAT
        return group(pmodel.model_plant.s(i) for i in clist)().get()
    else:
        return [performance_model_plant(pJSON) for pJSON in clist]

def design(reqs_str,ranking=[efficient, knapsack]):
    """parts selection algorithm. """
    reqs = json.loads(reqs_str)
    validC = []
    optionSet = []
    zc = reqs['zipcode']

    for inverter_model, panel_model in combinations(reqs['inverter options'],\
            reqs['panel options']):
        #system = inverters.Inverter(inverter_model,\
        #        modules.PvArray(modules.Module(panel_model), [{'series':2}]))
        configs = generate_options(inverter_model, panel_model, zc)
        for config in configs:
            validC.append(config)
            print config, '\n', config.array, config.array.dump()['panel'], \
                    config.array.output(1000), config.ratio()

            reqs['array'] = [config.dump()]
        optionSet.append(copy.deepcopy(reqs))

    performance_results = performance_model_set(optionSet)
    print performance_results[0]

    suggested = []
    for algo in ranking:
        proposed = algo(performance_results, reqs['desired size'])
        reqs['array'] = proposed['system_set']
        reqs['algorithm'] = proposed['algorithm']
        suggested.append(copy.deepcopy(reqs))

    return suggested

def celery_worker_status():
    ERROR_KEY = "ERROR"
    try:
        from celery.task.control import inspect
        insp = inspect()
        d = insp.stats()
        if not d:
            d = {ERROR_KEY: 'No running Celery workers were found.'}
    except IOError as e:
        from errno import errorcode
        msg = "Error connecting to the backend: " + str(e)
        if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
            msg += ' Check that the RabbitMQ server is running.'
        d = {ERROR_KEY: msg}
    except ImportError as e:
        d = {ERROR_KEY: str(e)}
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
            print proposed
            proposedPlant = pv.json_system(proposed)
            print json.dumps(proposedPlant.dump(), sort_keys=True, indent=4, \
                separators=(',', ': '))
            print proposed['algorithm']
            expedite.string_notes(proposedPlant,1)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
