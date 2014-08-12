# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.
"""PV array classes"""

import json
import re
STC = 25
import os
from collections import Counter
SPATH = os.path.dirname(os.path.abspath(__file__))

class Module(object):
    """generic module class uses JSON defintion"""
    #PV module nameplate DC rating     0.80 - 1.05
    #SAM = 1
    #PVWatts = .95
    nameplate = .95
    Vrated = 600
    #nameplate = 1
    #t_noct  ; NOCT
    #a_c ; Module Area
    #n_s  ; Number of Cells
    #i_sc_ref  ; I Short Circuit
    #v_oc_ref ;  VOC
    #i_mp_ref ;  Imp
    #v_mp_ref ;  v_mp
    #alpha_sc ; i_sc temperature cofficient %/C
    #beta_oc ; v_oc temperature cofficient V/C
    #a_ref ; ideality factor V
    #i_l_ref ; light current
    #i_o_ref ; diode reverse saturation current
    #r_s ; series resistance
    #r_sh_ref ;  shunt resistance
    #adjust =
    #gamma_r =
    #gamma_r appears to be p_mp Temperature Coefficent and is emperically
    #found in %/C. SAM differs from datasheet
    #source=Mono-c-Si
    def __init__(self, model):
        self.properties = None
        panels = json.loads(open(SPATH + '/sp.json').read())
        for i in panels:
            if i['panel'] == model:
                self.properties = i
                break
        if self.properties == None:
            raise Exception("Module not found")
        self.make = model.split(':')[0].rstrip()
        self.model = model.split(':')[1].strip()
        self.v_mpp = self.properties['v_mp_ref']
        self.i_mpp = self.properties['i_mp_ref']
        self.p_max = self.v_mpp*self.i_mpp
        self.i_sc = self.properties['i_sc_ref']
        self.v_oc = self.properties['v_oc_ref']
        #v_oc V/C
        self.tk_v_oc = self.properties['beta_oc']
        #gamma_r is emperically found in %/C SAM differs from datasheet
        #p_mp W/C
        self.tk_p_mp = self.properties['gamma_r']*self.p_max/100
        self.gamma = self.properties['gamma_r']
        #todo: beta or gamma? go more conservative for now
        self.tk_v_mp = self.properties['gamma_r']*self.v_mpp/100
        #self.tk_v_mp = self.properties['beta_oc']
        self.tk_i_sc = self.properties['alpha_sc']*self.i_sc/100
        self.a_c = self.properties['a_c']
        self.eff = self.p_max/self.a_c/1000
        self.nameplate = 1.0

    def output(self, insolation, t_cell=25):
        """Watts DC output"""
        return (insolation/1000.0) * self.i_mpp * self.v_dc(t_cell)

    def v_max(self, ashrae_min):
        """Max Voltage at minimum temperature"""
        return self.v_oc + (ashrae_min-STC) * self.tk_v_oc

    def v_dc(self, t_cell=25):
        """Voltage of module at cell tempture"""
        #t adjusted for temp
        #todo fix
        return self.v_mpp - self.tk_v_mp * (25-t_cell)
        #return self.v_mpp

    def i_dc(self, t_cell=25):
        """Current adjusted for temperature"""
        return self.i_mpp - self.i_mpp * (25-t_cell)

    def v_min(self, ashrae2p, t_adder=30):
        """Minimum voltage of module under load"""
        #t_adder
        #Roof mount =30
        #Ground mount = 25
        #Pole mount = 20
        return self.v_mpp + (t_adder+ashrae2p-STC) * self.tk_v_mp

    def __repr__(self):
        return "%s : %s" % (self.make, self.model)


class PvArray(object):
    """DEPRECATED structure to aggregate panels into an array"""
    def __init__(self, pname, shape):
        self.shape = []
        for string in shape:
            if "parallel" in string:
                self.shape += [string["series"]]*string["parallel"]
            else:
                self.shape.append(string["series"])
        self.panel = pname
        self.p_max = pname.p_max*sum(self.shape)

    def v_dc(self, t_cell=25):
        """Array Voltage at tempature"""
        return self.panel.v_dc(t_cell) * max(self.shape)
    def v_max(self, ashrae_min):
        """Maximum Array Voltage"""
        return self.panel.v_max(ashrae_min) * max(self.shape)
    def v_min(self, ashrae2p, t_adder=30):
        """Minimum Array voltage under load"""
        return  self.panel.v_min(ashrae2p, t_adder)* min(self.shape)
    def output(self, insolation, t_ambient=25):
        """Array output for insolation"""
        return self.panel.output(insolation, t_ambient)*sum(self.shape)
    def dump(self):
        """dump array to dict"""
        count = Counter(self.shape)
        temp = [{"series":i, "parallel": count[i]} for i in count.iterkeys()]
        return {'shape':temp, 'panel':str(self.panel)}

    def __str__(self):
        count = Counter(self.shape)
        temp = ', '.join(['%sS x %sP' % (i, count[i]) \
                for i in count.iterkeys()])
        return "%s" % (temp)

class Mppt(object):
    """structure to aggregate panels into an array)"""
    def __init__(self, module, series, parallel=1):
        self.module = module
        self.series = series
        self.parallel = parallel
        self.minlength = 1
        self.maxlength = 14
        self.p_max = self.output(1000)

    def v_dc(self, t_cell=25):
        """channel voltage at temperature"""
        return self.module.v_dc(t_cell) * self.series

    def v_max(self, ashrae_min):
        """max channel voltage at temperature"""
        return self.module.v_max(ashrae_min) * self.series
    def v_min(self, ashrae2p, t_adder=30):
        """min channel voltage under load"""
        return  self.module.v_min(ashrae2p, t_adder)* self.series

    def i_sc(self):
        """short circuit current"""
        return self.module.i_sc*self.parallel

    def i_mpp(self):
        """mppt current"""
        return self.module.i_mpp*self.parallel

    def output(self, insolation, t_ambient=25):
        """watts output of channel"""
        return self.module.output(insolation, t_ambient) * self.series * \
                self.parallel

    def inc(self):
        """increase number of panels in channel"""
        if self.minlength > self.maxlength:
            raise Exception('Min length exceeds Max length')
        if (self.series+1) <= self.maxlength:
            self.series += 1
        else:
            self.parallel += 1
            self.series = self.minlength

    def dec(self):
        """decrease number of panels in channel"""
        if (self.series - 1) < self.minlength:
            self.series -= 1
        elif self.parallel > 1:
            self.parallel += 1
            self.series = self.maxlength
        else:
            print 'Warning: minimum size reached'

    def dump(self):
        """dump to dict"""
        return {"series":self.series, "parallel": self.parallel}

    def __repr__(self):
        return '%sS x %sP %s' % (self.series, self.parallel, self.module)

class Array(object):
    """rewrite of pvArray"""
    def __init__(self, module, shape):#series, parallel = 1):
        self.channels = []
        for i in shape:
            if 'parallel' in i:
                parallel = i['parallel']
            else:
                parallel = 1
            self.channels.append(Mppt(module, i['series'], parallel))
        self.p_max = self.output(1000)

    def mcount(self):
        """module count"""
        return sum([i.series*i.parallel for i in self.channels])

    def output(self, insolation, t_ambient=25):
        """total dc power output"""
        return sum([i.output(insolation, t_ambient) for i in self.channels])

    def v_max(self, ashrae_min):
        """max voltage"""
        return max([i.v_max(ashrae_min) for i in self.channels])
    def v_min(self, ashrae2p, t_adder=30):
        """min voltage under load"""
        return min([i.v_min(ashrae2p, t_adder) for i in self.channels])

    def v_dc(self, t_cell=25):
        """todo:not sure what this should return"""
        return max([i.v_dc(t_cell) for i in self.channels])

    def i_sc(self):
        """total short circuit current"""
        return sum([i.i_sc() for i in self.channels])

    def i_mpp(self):
        """total mppt circuit current"""
        return sum([i.i_mpp() for i in self.channels])

    def maxlength(self, maxl):
        """max length of string. needs to be set before running"""
        for i in self.channels:
            i.maxlength = maxl

    def minlength(self, minl):
        """min length of string. needs to be set before running"""
        for i in self.channels:
            i.minlength = minl

    def inc(self):
        """increase channel with least panels"""
        #find channel with least panels
        min_p = self.channels[0].output(1000)
        min_c = self.channels[0]
        for i in self.channels:
            if i.output(1000) < min_p:
                min_p = i.output(1000)
                min_c = i
        #incriment that channel
        min_c.inc()
        self.p_max = self.output(1000)

    def dec(self):
        """decrease channel with most panels"""
        #find channel with most panels
        max_p = self.channels[0].p_max
        max_c = self.channels[0]
        for i in self.channels:
            if i.p_max > max_p:
                max_p = i.p_max
                max_c = i
        #dccriment that channel
        max_c.dec()
        self.p_max = self.output(1000)

    def dump(self):
        """dump to dict"""
        return {'shape':[i.dump() for i in self.channels],
                'panel':str(self.channels[0].module)}

    def __repr__(self):
        return ', '.join(['channel %s: %s' % (i, c) for i, c in \
                enumerate(self.channels)])


def manufacturers():
    """return list of panel manufacturers"""
    man_list = [i['panel'].split(":")[0] for i in \
            json.loads(open(SPATH + '/sp.json').read())]
    man_list.sort()
    uniq_list = [i for i in set(man_list)]
    uniq_list.sort()
    return uniq_list

def models(manufacturer=None):
    """returns list of available panel models"""
    #return json.loads(open('si.json').read())
    if manufacturer == None:
        return [i['panel'] for i in \
                json.loads(open(SPATH + '/sp.json').read())]
    else:
        panel_list = []
        for i in json.loads(open(SPATH + '/sp.json').read()):
            if i['panel'].find(manufacturer) != -1:
                panel_list.append(i['panel'])
        return panel_list

def model_search(parms):
    """search for a module model"""
    res = []
    for i in models():
        if all(re.search(sub, i) for sub in parms):
            res.append(i)
    return res

if __name__ == "__main__":
    SERIES = 14
    PANEL = Module('Mage Solar : USA Powertec Plus 245-6 MNBS')
    print ":%s:" % PANEL.make
    print ":%s:" % PANEL.model

    print "v_max:", PANEL.v_max(-13)*SERIES
    print "v_min:", PANEL.v_min(31, 25) * SERIES
    print "v_min 10%:", PANEL.v_min(31, 25) * SERIES*.90
    TEMP = Array(PANEL, [{'series':11}])
    print TEMP.dump()
    TEMP = Array(PANEL, [{'series':11, 'parallel':2}])
    TEMP = Array(PANEL, [{'series':11, 'parallel':1},{'series':11, 'parallel':1}])
    print TEMP.dump()
    print TEMP
