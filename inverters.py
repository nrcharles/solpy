# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.
"""Inverter class and related functions methods"""

import json
import os
SPATH = os.path.dirname(os.path.abspath(__file__))
class Inverter(object):
    """Sandia Model"""
    #Inverter Output = Array STC power * Irradiance *\
    #Negative Module Power Tolerance * Soiling * Temperature factor * \
    #Wiring efficiency * Inverter efficiency
    #PVWATTS Default
    #Mismatch      0.97 - 0.995
    mismatch = .98
    #Diodes and connections      0.99 - 0.997
    connections = .995
    #DC wiring     0.97 - 0.99
    dc_wiring = .98
    #AC wiring0.98 - 0.993
    ac_wiring = .99
    #Soiling       0.30 - 0.995
    soiling = .95
    #System availability     0.00 - 0.995
    availability = 0.98
    #not included in PVWATTS/SAM
    NMPT = .97
    Tfactor = .98

    def __init__(self, model, array=None, orientation=[(180, 0)]):
        self.array = array
        self.orientation = orientation
        self.properties = None
        inverters = json.loads(open(SPATH + '/si.json').read())
        for i in inverters:
            try:
                if i['inverter'] == model:
                    self.properties = i
                    break
            except:
                print "Error on key with data", i
                raise
        if self.properties == None:
            raise Exception("Inverter not found")
        self.ac_voltage = self.properties['ac_voltage']
        self.inverter = self.properties['inverter']
        self.vdcmax = self.properties['vdcmax']
        self.p_dco = self.properties['pdco']
        self.p_aco = self.properties['paco']
        self.pnt = self.properties['pnt']
        self.p_so = self.properties['pso']
        self.v_dco = self.properties['vdco']
        self.c0 = self.properties['c0']
        self.c1 = self.properties['c1']
        self.c2 = self.properties['c2']
        self.c3 = self.properties['c3']
        self.idcmax = self.properties['idcmax']
        self.mppt_hi = self.properties['mppt_hi']
        self.mppt_low = self.properties['mppt_low']
        self.mppt_channels = 1
        self.make, self.model = self.inverter.split(":", 2)
        self.derate = self.mismatch * self.soiling * self.dc_wiring *\
                self.connections * self.availability# * m.Tfactor #* m.NMPT
        #self.derate = self.dc_wiring

        #current corrections for TL inverters
        tl_meta = json.loads(open(SPATH + '/tl.json').read())
        for i in tl_meta:
            try:
                if i['inverter'] == model:
                    self.current = i['current']
                    self.phase = i['phase']
                    if 'mppt_channels' in i:
                        self.mppt_channels = i['mppt_channels']
                    break
            except:
                pass

    def p_ac(self, insolation, t_cell=25):
        """AC power in Watts"""
        p_dc = self.array.output(insolation, t_cell)
        v_dc = self.array.v_dc()
        A = self.p_dco * (1 + self.c1 * (v_dc - self.v_dco))
        B = self.p_so * (1 + self.c2 * (v_dc - self.v_dco))
        C = self.c0 * (1 + self.c3 * (v_dc - self.v_dco))
        p_ac = ((self.p_aco / (A - B)) - C*(A - B))*(p_dc- B) + C *(p_dc - B)**2
        #clip at p_aco
        return min(float(self.p_aco), p_ac * self.derate)

    def i_ac(self, insolation, v_ac):
        """ac current"""
        return self.p_ac(insolation)/v_ac

    def ratio(self):
        """AC/DC ratio"""
        return self.array.output(1000)/self.p_dco

    def dump(self):
        """dump to dict"""
        temp = {}
        shape = self.array.dump()
        temp['panel'] = shape['panel']
        del shape['panel']
        temp['inverter'] = "%s:%s" % (self.make, self.model)
        if len(shape) > 1:
            temp['shape'] = shape
        else:
            temp.update(shape)
        return temp

    def __repr__(self):
        return "%s:%s [%s]" % (self.make, self.model, self.array)

def manufacturers():
    """get list of manufacturers"""
    man_list = [i['inverter'].split(":")[0] for i in \
            json.loads(open(SPATH + '/si.json').read())]
    man_list.sort()
    uniq_list = [i for i in set(man_list)]
    uniq_list.sort()
    return uniq_list

def models(manufacturer=None):
    """models for a particular manufacturer or all models"""
    """returns list of available inverter models"""
    if manufacturer == None:
        return [i['inverter'] for i in \
                json.loads(open(SPATH + '/si.json').read())]
    else:
        a = []
        for i in json.loads(open(SPATH + '/si.json').read()):
            if i['inverter'].find(manufacturer) != -1:
                a.append(i['inverter'])
        return a

if __name__ == "__main__":
    from modules import Module, Array

    PANEL = Module('Mage Solar : Powertec Plus 245-6 PL *')
    INVERTER = Inverter("Enphase Energy: M215-60-SIE-S2x 240V",\
            Array(PANEL, [{'series':1}]))
    print INVERTER.array
    print ""
    print INVERTER.dump()
    #si = sb6000us(s)

    print INVERTER.p_ac(950)
    print INVERTER.i_ac(960, 240)

    INVERTER = Inverter("SMA America: SB7000US-11 277V", Array(PANEL, [{'series':11,'parallel':3}]))
    print INVERTER
    print INVERTER.array
