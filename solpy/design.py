"""
Parametric Design tools
"""
# This program is free software. See terms in LICENSE file.
import logging
logger = logging.getLogger(__name__)

import copy
import json

from caelum import eere
from solpy import pv
from solpy import geo
from solpy import inverters
from solpy import modules

def tools_fill(inverter, zipcode, ac_dc_ratio=1.2, mount="Roof", \
        station_class=1, v_max=600, bipolar=True):
    """deprecated legacy function"""

    tmp = inverter.dump()
    inverter_name = tmp['inverter']
    module_name = tmp['panel']
    return [str_format(i) for i in generate_options(inverter_name, \
            module_name, zipcode, ac_dc_ratio, \
            mount, station_class, v_max, bipolar)]
    #return [str_format(i) for i in fill(inverter, zipcode, ac_dc_ratio, \
    #        mount, station_class, v_max, bipolar)]

def str_format(inverter):
    """format as str: '9769.5W : 13S x 3P : ratio 1.22 : 314.0 - 552.0 V'"""
    dc_nom = inverter.array.output(1000)
    ratio = dc_nom/inverter.p_aco
    return '%sW : %s : ratio %s : %s - %s V' % (dc_nom, inverter.array, \
            round(ratio, 2), round(inverter.min_v), round(inverter.max_v))

def fill(inverter, zipcode, ac_dc_ratio=1.2, mount="Roof", station_class=1, \
        v_max=600, bipolar=True):
    """deprecated use generate_options"""
    t_derate = {"Roof":30, \
            "Ground":25, \
            "Pole":20}

    #csv is performance hit
    dummy, usaf = geo.closest_usaf(geo.zip_coordinates(zipcode), station_class)
    max_v = inverter.array.panel.v_max(eere.minimum(usaf))
    #NREL suggests that long term degradation is primarily current not voltage
    derate20 = .97
    min_v = inverter.array.panel.v_min(eere.twopercent(usaf), \
            t_derate[mount]) * derate20

    if inverter.vdcmax != 0:
        v_max = inverter.vdcmax
    smax = int(v_max/max_v)
    #range to search
    lower_tol = .30
    upper_tol = .30
    p_nom_lower = ac_dc_ratio*(1+lower_tol)
    p_nom_upper = ac_dc_ratio*(1-upper_tol)

    inverter_nominal = inverter.p_aco
    psize = inverter.array.panel.p_max
    solutions = []

    i_max = max(inverter.idcmax, inverter.p_dco*1.0/inverter.mppt_low)
    max_parallel = int(round(i_max/inverter.array.panel.i_mpp))+1

    #Diophantine equation
    for string_len in range(smax+1):
        if (string_len*min_v) >= inverter.mppt_low:
            for p_count in range(max_parallel):
                p_nom = p_count*string_len*psize*1.0/inverter_nominal
                if p_nom < p_nom_upper and p_nom > lower_tol:
                    inverter.array.shape = [string_len]*p_count
                    _tmp = copy.deepcopy(inverter)
                    _tmp.min_v = string_len*min_v
                    _tmp.max_v = string_len*max_v
                    solutions.append(_tmp)
    return solutions

def generate_options(inverter_name, module_name, zipcode, ac_dc_ratio=1.2, \
        mount="Roof", station_class=1, v_max=600, bipolar=True):
    """String sizing: find all valid configurations for a location"""
    module = modules.Module(module_name)
    inverter = inverters.Inverter(inverter_name)
    temp_adder = {"Roof":30,\
            "Ground":25,\
            "Pole":20}
    #NREL suggests that long term degradation is primarily current not voltage
    derate20 = .97

    #csv is performance hit
    dummy, usaf = geo.closest_usaf(geo.zip_coordinates(zipcode), station_class)
    eere_min = eere.minimum(usaf)
    module_max_voltage = module.v_max(eere_min)
    eere2 = eere.twopercent(usaf)
    module_min_voltage = module.v_min(eere2, temp_adder[mount]) * derate20

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
    lower_tol = .25
    upper_tol = .30
    p_nom_lower = ac_dc_ratio*(1+lower_tol)
    p_nom_upper = ac_dc_ratio*(1-upper_tol)
    #inverter_nominal = inverter.p_aco
    solutions = []
    while inverter.ratio() < p_nom_lower:
        _tmp = copy.deepcopy(inverter)
        _tmp.max_v = _tmp.array.v_max(eere_min)
        _tmp.min_v = _tmp.array.v_min(eere2, temp_adder[mount])
        if inverter.ratio() >= p_nom_upper:
            solutions.append(_tmp)
        inverter.array.inc()

    #i_max = max(inverter.idcmax,inverter.p_dco*1.0/inverter.mppt_low)
    #max_parallel = int(round(i_max/inverter.array.panel.i_mpp))+1

    #Diophantine equation
    return solutions

def knapsack(item_set, maxweight):
    """knapsack problem weight is system DC size and value is annual output
    this could be expanded with different constraints for different rankings"""
    #http://codereview.stackexchange.com/questions/20569/
    #dynamic-programming-solution-to-knapsack-problem
    items = []
    for option in item_set:
        #hack to expand for semetery
        scale = maxweight // option['DCnominal']
        items += [(option['yearone'], option['DCnominal'], \
                option['array'][0])] * scale

    bestvalues = [[0] * (maxweight + 1) \
                for i in xrange(len(items) + 1)]
    for i, (value, weight, dummy) in enumerate(items):
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
    system_set = [subA for dummy, dummy, subA in reconstruction]

    results = {'address':item_set[0]['address'], \
            'voltage':item_set[0]['voltage'], \
            'phase':item_set[0]['phase'], \
            'azimuth':item_set[0]['azimuth'], \
            'tilt':item_set[0]['tilt'], \
            'zipcode':item_set[0]['zipcode'], \
            'system_name':item_set[0]['system_name'], \
            'algorithm':'knapsack', \
            'notes':'most annual generation', \
            'yearone':bestvalues[len(items)][maxweight], \
            'DCnominal':sum([dc_nom \
            for dummy, dc_nom, dummy in reconstruction]), \
            'array': system_set}

    return results

def efficient(items, maxweight):
    """symetric design of the most efficeint inverter panel combo"""
    most_eff = {'eff':0}
    for option in items:
        value = option['yearone']
        weight = option['DCnominal']
        eff = value/float(weight)
        if eff > most_eff['eff']:
            most_eff = {'eff':eff, \
                    'weight': weight, \
                    'value': value, \
                    'sub_array':option['array'][0]}
    scale = maxweight/most_eff['weight']
    system_result = [most_eff['sub_array']]*scale
    results = {'address':items[0]['address'], \
            'voltage':items[0]['voltage'], \
            'yearone':most_eff['value']*scale, \
            'phase':items[0]['phase'], \
            'azimuth':items[0]['azimuth'], \
            'tilt':items[0]['tilt'], \
            'zipcode':items[0]['zipcode'], \
            'system_name':items[0]['system_name'], \
            'algorithm':'efficient', \
            'notes':'symetric design of most efficient combination', \
            'DCnominal':most_eff['weight']*scale, \
            'array': system_result}
    return results

def combinations(_a, _b):
    """generate combinations"""
    _s = []
    for i in _a:
        for j in _b:
            _s.append((i, j))
    return _s

def performance_model_plant(json_def):
    """model performance of a system"""
    plant = pv.json_system(json_def)
    yearone = plant.model()
    p_dc = sum([i.array.output(1000) for i in plant.shape])
    plant_dict = plant.dump()
    plant_dict['yearone'] = yearone.annual_output
    plant_dict['DCnominal'] = int(p_dc)
    return plant_dict

def performance_model_set(clist):
    """wrapper for distributed performance modelling"""
    cstat = celery_worker_status()
    if not 'ERROR' in cstat:
        from celery import group
        import solpy.pmodel
        logger.debug(cstat)
        return group(solpy.pmodel.model_plant.s(i) for i in clist)().get()
    else:
        return [performance_model_plant(pJSON) for pJSON in clist]

def design(reqs, ranking=None):
    """Design a PV system based upon various ranking algorithms.

    Args:
        reqs (dict): JSON object of design constriants. Shading is an optional
        constraint.

        ranking (list): algorithms that define valuation of parts.
        The default rankings are knapsack and efficient.

    Returns:
        list of systems

    For example:

    >>> reqs = {"system_name":"HAPPY CUSTOMER",
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
        "space":[[10,5]],
        "desired size":25000}
    >>> design(reqs, ranking=[efficient])
    [{'DCnominal': 23100,
    'address': '15013 Denver W Pkwy, Golden, CO',
    'algorithm': 'efficient',
    'array': [{'inverter': u'SMA America: SB5000TL-US-22 (240V) 240V',
        'panel': 'Axitec : AC-250P-156-60S *',
        'quantity': 1,
        'shape': [{'parallel': 1, 'series': 12},
            {'parallel': 1, 'series': 11}]},
    {'inverter': u'SMA America: SB5000TL-US-22 (240V) 240V',
        'panel': 'Axitec : AC-250P-156-60S *',
        'quantity': 1,
        'shape': [{'parallel': 1, 'series': 12},
            {'parallel': 1, 'series': 11}]},
    {'inverter': u'SMA America: SB5000TL-US-22 (240V) 240V',
        'panel': 'Axitec : AC-250P-156-60S *',
        'quantity': 1,
        'shape': [{'parallel': 1, 'series': 12},
            {'parallel': 1, 'series': 11}]},
    {'inverter': u'SMA America: SB5000TL-US-22 (240V) 240V',
        'panel': 'Axitec : AC-250P-156-60S *',
        'quantity': 1,
        'shape': [{'parallel': 1, 'series': 12},
            {'parallel': 1, 'series': 11}]}],
    'azimuth': 180,
    'notes': 'symetric design of most efficient combination',
    'phase': 1,
    'system_name': 'HAPPY CUSTOMER',
    'tilt': 25,
    'voltage': 240,
    'yearone': 35746.2,
    'zipcode': '80401'}]


    """
    if not ranking:
        ranking = [efficient, knapsack]
    valid_combo = []
    option_set = []
    zipcode = reqs['zipcode']

    for inverter_model, panel_model in combinations(reqs['inverter options'],\
            reqs['panel options']):
        configs = generate_options(inverter_model, panel_model, zipcode)
        for config in configs:
            valid_combo.append(config)
            logger.info('%s %s %s', config, \
                    round(config.array.output(1000), 1), \
                    round(config.ratio(), 2))
            reqs['array'] = [config.dump()]
            option_set.append(copy.deepcopy(reqs))
    performance_results = performance_model_set(option_set)
    suggested = []
    for algo in ranking:
        proposed = algo(performance_results, reqs['desired size'])
        suggested.append(proposed)
    return suggested

def celery_worker_status():
    """get celery worker status"""
    error_key = "ERROR"
    try:
        from celery.task.control import inspect
        insp = inspect()
        stats = insp.stats()
        if not stats:
            stats = {error_key: 'No running Celery workers were found.'}
    except IOError as err:
        from errno import errorcode
        msg = "Error connecting to the backend: " + str(err)
        if len(err.args) > 0 and errorcode.get(err.args[0]) == 'ECONNREFUSED':
            msg += ' Check that the RabbitMQ server is running.'
        stats = {error_key: msg}
    except ImportError as err:
        stats = {error_key: str(err)}
    return stats

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from solpy import expedite
    import argparse
    import sys

    #sketchup may be a good way to input this data
    REQS = """{"system_name":"HAPPY CUSTOMER",
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
        "desired size":25000,
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

    PARSER = argparse.ArgumentParser(description='Design a PV system')
    PARSER.add_argument('-f', '--file')
    ARGS = vars(PARSER.parse_args())
    try:
        #start program
        if ARGS['file']:
            REQS = open(ARGS['file']).read()

        for proposed_d in design(json.loads(REQS)):
            proposed_plant = pv.json_system(proposed_d)
            logger.info(json.dumps(proposed_plant.dump(), sort_keys=True, \
                    indent=4, separators=(',', ': ')))
            logger.info(proposed_d['algorithm'])
            if proposed_d['array']:
                expedite.string_notes(proposed_plant, 1)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
