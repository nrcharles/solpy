# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

import json
import re
STC = 25
import os
from collections import Counter
SPATH = os.path.dirname(os.path.abspath(__file__))

class module(object):
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
    #v_mp_ref ;  Vmp 
    #alpha_sc ; Isc temperature cofficient %/C
    #beta_oc ; Voc temperature cofficient V/C
    #a_ref ; ideality factor V
    #i_l_ref ; light current
    #i_o_ref ; diode reverse saturation current
    #r_s ; series resistance
    #r_sh_ref ;  shunt resistance
    #adjust =   
    #gamma_r = 
    #gamma_r appears to be Pmp Temperature Coefficent and is emperically 
    #found in %/C. SAM differs from datasheet
    #source=Mono-c-Si
    def __init__(self,model):
        self.properties = None
        panels = json.loads(open(SPATH + '/sp.json').read())
        for i in panels:
            if i['panel']==model:
                self.properties = i
                break
        if self.properties == None:
            raise Exception("Panel not found")
        self.make = model.split(':')[0].rstrip()
        self.model = model.split(':')[1].strip()
        self.Vmpp = self.properties['v_mp_ref']
        self.Impp = self.properties['i_mp_ref']
        self.Pmax = self.Vmpp*self.Impp
        self.Isc =  self.properties['i_sc_ref']
        self.Voc = self.properties['v_oc_ref']
        #Voc V/C
        self.TkVoc = self.properties['beta_oc']
        #gamma_r is emperically found in %/C SAM differs from datasheet
        #Pmp W/C
        self.TkPmp = self.properties['gamma_r']*self.Pmax/100
        self.gamma = self.properties['gamma_r']
        #todo: beta or gamma? go more conservative for now
        self.TkVmp = self.properties['gamma_r']*self.Vmpp/100
        #self.TkVmp = self.properties['beta_oc']
        self.TkIsc = self.properties['alpha_sc']*self.Isc/100
        self.A = self.properties['a_c']
        self.Eff = self.Pmax/self.A/1000
        self.nameplate = 1.0

    def output(self,Insolation, tCell = 25):
        return (Insolation/1000.0) * self.Impp * self.Vdc(tCell)
        #return Insolation * self.A * self.Eff * self.nameplate

    def Vmax(self,ashraeMin):
        return self.Voc + (ashraeMin-STC) * self.TkVoc

    def Vdc(self,t=25):
        #t adjusted for temp
        #todo fix
        return self.Vmpp - self.TkVmp * (25-t)
        #return self.Vmpp

    def Idc(self,t=25):
        return self.Impp - self.Impp * (25-t)

    def Vmin(self,ashrae2p,Tadd = 30):
        #Tadd
        #Roof mount =30
        #Ground mount = 25
        #Pole mount = 20
        return self.Vmpp + (Tadd+ashrae2p-STC) * self.TkVmp
    def __str__(self):
        return "%s : %s" % (self.make, self.model)


#todo: this needs rewritten
class pvArray(object):
    """structure to aggregate panels into an array)"""
    def __init__(self,pname, shape):
        self.shape = []
        for string in shape:
            if "parallel" in string:
                self.shape +=[string["series"]]*string["parallel"]
            else:
                self.shape.append(string["series"])
        self.panel = pname
        self.Pmax = pname.Pmax*sum(self.shape)

    def Vdc(self, t = 25):
        return self.panel.Vdc(t) * max(self.shape)
    def Vmax(self,ashraeMin):
        return self.panel.Vmax(ashraeMin) * max(self.shape)
    def Vmin(self,ashrae2p, Tadd = 30):
        return  self.panel.Vmin(ashrae2p, Tadd)* min(self.shape)
    def output(self, Insolation, tAmb=25):
        return self.panel.output(Insolation,tAmb)*sum(self.shape)
    def dump(self):
        a = Counter(self.shape)
        d = [{"series":i, "parallel": a[i]} for i in a.iterkeys()]
        return {'shape':d,'panel':str(self.panel)}

    def __str__(self):
        a = Counter(self.shape)
        s = ', '.join(['%sS x %sP' % (i,a[i]) for i in a.iterkeys()])
        return "%s" % (s)

class mppt(object):
    """structure to aggregate panels into an array)"""
    def __init__(self,moduleO, series, parallel = 1):#series, parallel = 1):
        self.module = moduleO
        self.series = series
        self.parallel = parallel
        self.minlength = 1
        self.maxlength = 14
        self.Pmax = self.output(1000)

    def Vdc(self, t = 25):
        return self.module.Vdc(t) * self.series

    def Vmax(self,ashraeMin):
        return self.module.Vmax(ashraeMin) * self.series
    def Vmin(self,ashrae2p, Tadd = 30):
        return  self.module.Vmin(ashrae2p, Tadd)* self.series

    def output(self, Insolation, tAmb=25):
        return self.module.output(Insolation,tAmb) * self.series * self.parallel

    def inc(self):
        if (self.series+1) <= self.maxlength:
            self.series += 1
        else:
            self.parallel +=1
            self.series = self.minlength

    def dec(self):
        if (self.series - 1) < self.minlength:
            self.series -=1
        elif self.parallel > 1:
            self.parallel +=1
            self.series = self.maxlength
        else:
            print 'Warning: minimum size reached'

    def dump(self):
        d = {"series":self.series, "parallel": self.parallel}
        return d
    def __repr__(self):
        return '%sS x %sP' % (self.series, self.parallel)

class array(object):
    """rewrite of pvArray"""
    def __init__(self,moduleO, shape):#series, parallel = 1):
        self.channels = []
        for c in shape:
            if 'parallel' in c:
                parallel = c['parallel']
            else:
                parallel = 1
            self.channels.append(mppt(moduleO,c['series'],parallel))
        self.Pmax = self.output(1000)

    def output(self, Insolation, tAmb=25):
        return sum([i.output(Insolation, tAmb) for i in self.channels])

    def Vmax(self,ashraeMin):
        return max([i.Vmax(ashraeMin) for i in self.channels])
    def Vmin(self,ashrae2p, Tadd = 30):
        return min([i.Vmin(ashrae2p, Tadd) for i in self.channels])

    def maxlength(self, maxl):
        for i in self.channels:
            i.maxlength = maxl

    def minlength(self, minl):
        for i in self.channels:
            i.minlength = minl

    def inc(self):
        #find channel with least panels
        minP = self.channels[0].output(1000)
        minC = self.channels[0]
        for j,i in enumerate(self.channels):
            if i.output(1000) < minP:
                minP = i.output(1000)
                minC = i
        #incriment that channel
        minC.inc()
        self.Pmax = self.output(1000)

    def dec(self):
        #find channel with most panels
        maxP = self.channels[0].Pmax
        maxC = self.channels[0]
        for i in self.channels:
            if i.Pmax > maxP:
                maxP = i.Pmax
                maxC = i
        #dccriment that channel
        maxC.dec()
        self.Pmax = self.output(1000)

    def dump(self):
        return {'shape':[i.dump() for i in self.channels],
                'panel':str(self.channels[0].module)}

    def __repr__(self):
        return '\n'.join(['channel %s: %s' % (i,c) for i,c in \
                enumerate(self.channels)])


def manufacturers():
    a =  [i['panel'].split(":")[0] for i in json.loads(open(SPATH + '/sp.json').read()) ]
    a.sort()
    b = [i for i in set(a)]
    b.sort()
    return b

def models(manufacturer = None):
    """returns list of available panel models"""
    #return json.loads(open('si.json').read())
    if manufacturer ==None:
        return [i['panel'] for i in json.loads(open(SPATH + '/sp.json').read()) ]
    else:
        a = []
        for i in json.loads(open(SPATH + '/sp.json').read()):
            if i['panel'].find(manufacturer) != -1:
                a.append(i['panel'])
        return a

def model_search(parms):
    res = []
    for i in models():
        if all(re.search(sub,i) for sub in parms):
            res.append(i)
    return res

if __name__=="__main__":
    series = 14
    p = module('Mage Solar : USA Powertec Plus 245-6 MNBS')
    print ":%s:" %p.make
    print ":%s:" %p.model
    print p.Eff
    print p

    print "Vmax:", p.Vmax(-13)*series
    print "Vmin:",p.Vmin(31,25) * series
    print "Vmin 10%:",p.Vmin(31,25) * series*.90
    a = pvArray(p,[{'series':11}])
    print a.dump()
    a = pvArray(p,[{'series':11,'parallel':2}])
    print a.dump()
    a = pvArray(p,[{'series':11},{'series':10}])
    print a.dump()
    a = array(p,[{'series':11},{'series':10}])
    print a.dump()
    print a
