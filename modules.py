import unittest
import json
STC = 25
import os
SPATH = os.path.dirname(os.path.abspath(__file__))

class module(object):
    """base module class which specific modules inherit"""
    STC = 25
    #PV module nameplate DC rating     0.80 - 1.05
    #SAM = 1
    #PVWatts = .95
    nameplate = .95
    Vrated = 600
    #nameplate = 1
    #beta Voc %/Tempunit
    #gamma Pmax %/Tempunit
    def __init__(self):
        pass
    def output(self,Insolation):
        m = self.__class__
        return Insolation*m.A*m.Eff*m.nameplate
    def Vmax(self,ashraeMin):
        m = self.__class__
        return m.Voc + (ashraeMin-m.STC)*m.TkVoc
    def Vdc(self):
        m = self.__class__
        return m.Vmpp

    def Vmin(self,ashrae2p,Tadd = 30):
        #Tadd
        #Roof mount =30
        #Ground mount = 25
        #Pole mount = 20
        m = self.__class__
        return m.Vmpp + (Tadd+ashrae2p-m.STC)*m.TkVoc
        #tkVmp or tkVoc?
        #return m.Vmpp + (Tadd+ashrae2p-m.STC)*m.TkVmp

class moduleJ(object):
    """base module class which specific modules inherit"""
    #PV module nameplate DC rating     0.80 - 1.05
    #SAM = 1
    #PVWatts = .95
    nameplate = .95
    Vrated = 600
    #nameplate = 1
    #beta Voc %/Tempunit
    #gamma Pmax %/Tempunit
    def __init__(self,model):
        self.properties = None
	print SPATH
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
        #self.beta = self.properties['beta_oc']
        #self.gamma = self.properties['gamma_r']
        #Voc V/C
        self.TkVoc = self.properties['beta_oc']
        #Pmp W/C
        self.TkPmp = self.properties['gamma_r']*self.Pmax/100
        self.gamma = self.properties['gamma_r']
        self.TkVmp = self.properties['gamma_r']*self.Vmpp/100
        self.A = self.properties['a_c']
        self.Eff = self.Pmax/self.A/1000
        self.nameplate = 1.0

    def output(self,Insolation):
        return Insolation * self.A * self.Eff * self.nameplate
    def Vmax(self,ashraeMin):
        return self.Voc + (ashraeMin-STC) * self.TkVoc
    def Vdc(self):
        return self.Vmpp

    def Vmin(self,ashrae2p,Tadd = 30):
        #Tadd
        #Roof mount =30
        #Ground mount = 25
        #Pole mount = 20
        return self.Vmpp + (Tadd+ashrae2p-STC) * self.TkVmp

#this needs rewritten
class pvArray(module):
    """structure to aggregate panels into an array)"""
    def __init__(self,pname, series, parallel = 1):
        self.panel = pname
        self.series = series
        self.parallel = parallel
        self.Pmax = pname.Pmax*series*parallel
        
    def Vdc(self):
        return self.panel.Vdc() * self.series
    def Vmax(self,ashraeMin):
        return self.panel.Vmax(ashraeMin) * self.series
    def Vmin(self,ashrae2p, Tadd = 30):
        return  self.panel.Vmin(ashrae2p, Tadd)* self.series
    def output(self, Insolation):
        return self.panel.output(Insolation)*self.series*self.parallel

class mage285(module):
    make = "Mage"
    model = ""
    Pmax = 285
    Vmpp = 35.59
    Impp = 8.01
    Isc = 8.45
    Voc = 44.76
    #Uoc %/K
    beta = -0.32
    #Pmax %/K
    gamma = -0.43
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.973 * .989
    Eff = .146
    nameplate = 1.0

class mage250(module):
    make = "Mage"
    model = "250/6 MNS"
    Pmax = 250
    Vrated = 600
    Vmpp = 30.55
    Impp = 8.21
    Isc = 8.70
    Voc = 37.70
    #Uoc %/K
    beta = -0.32
    #Pmax %/K
    gamma = -0.43
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.644 * .992
    Eff = .1533
    nameplate = 1.0

class mage250ml(module):
    make = "Mage"
    model = "250/6 ML"
    Pmax = 250
    Vrated = 600
    Vmpp = 30.90
    Impp = 8.09
    Isc = 8.79
    Voc = 37.57
    #Uoc %/K
    beta = -0.33
    #Pmax %/K
    gamma = -0.43
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.655 * .989
    Eff = .154
    nameplate = 1.0

class mage240(module):
    make = "Mage"
    Pmax = 240
    Vmpp = 29.48
    Impp = 8.14
    Isc = 8.51
    Voc = 37.48
    #Uoc %/K
    beta = -0.297
    #Pmax %/K
    gamma = -0.438
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.650 * .991
    Eff = .146

class mage235(module):
    make = "Mage"
    model = ""
    Pmax = 235
    Vmpp = 29.69
    Impp = 7.92
    Isc = 8.55
    Voc = 37.03
    #Uoc %/K
    beta = -0.32
    #Pmax %/K
    gamma = -0.43
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.655 * .989
    Eff = .144

class motech245(module):
    make = "Motech"
    model = "245"
    Pmax = 245
    Vmpp = 29.9
    Impp = 8.2
    Isc = 8.7
    Voc = 37.4
    #Voc %/C
    beta = -0.34
    #Pmax %/C
    gamma = -0.46
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.650 * .992
    Eff = Pmax/A/1000

class sinodeu120(module):
    Pmax = 120
    Vmpp = 17
    Impp = 7.06
    Isc = 7.76
    Voc = 21.2
    beta = -0.37 #%/K
    gamma = -0.52 #%/K
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.480*670
    Eff = Pmax/A/1000

class suntech285(module):
    make = "SUNTECH"
    model = "STP285-VRM-1.5"
    Pmax = 285
    Vrated = 1000
    Vmpp = 35.4
    Impp = 8.06
    Isc = 8.37
    Voc = 44.9
    #Uoc %/K
    beta = -0.33
    #Pmax %/K
    gamma = -0.44
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.956* 1.066
    Eff = .147
    nameplate = 1.0



class rec300(module):
    make = "REC"
    model = "REC300PE72"
    Pmax = 300
    Vrated = 1000
    Vmpp = 36.1
    Impp = 8.33
    Isc = 8.86
    Voc = 44.9
    #Uoc %/K
    beta = -0.28
    #Pmax %/K
    gamma = -0.41
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.9812 * .9906
    Eff = .153
    nameplate = 1.0


class generic170(module):
    make = ""
    model = ""
    Pmax = 170
    Vmpp = 34.8
    Impp =4.9
    Isc = 5.7
    Voc = 43.2
    TkVoc = -0.1728
    TkVmp = -0.1796
    Eff = .15
    A = Pmax/Eff/1000

class generic180(module):
    make = ""
    model = ""
    Pmax = 180
    Vmpp = 25.9
    Impp = 6.95
    Isc = 7.78
    Voc = 32.6
    beta = -0.34 #%/K
    gamma = -0.47 #%/K
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    TkPmp = -0.49 * Vmpp/100
    Eff = .15
    A = Pmax/Eff/1000

class astroenergy290(module):
    make = ""
    model = ""
    Pmax = 290
    Vmpp = 35.68
    Impp = 8.15
    Isc =  8.94
    Voc = 44.90
    beta = -0.332 #%/K
    gamma = -0.445 #%/K
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    TkPmp = -0.451 * Vmpp/100
    Eff = .149
    A = Pmax/Eff/1000

class asp240(module):
    Pmax = 240
    Vmpp = 30.54
    Impp = 7.87
    Isc = 8.48
    Voc = 37.26
    beta = -0.335 #%/C
    gamma = -0.40 #%/C
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    TkPmp = -0.40 * Vmpp/100
    Eff = .1482
    A = Pmax/Eff/1000

class asp390(module):
    make = ""
    model = ""
    Pmax = 390
    Vmpp = 49.38
    Impp = 7.92
    Isc = 8.42
    Voc = 59.62
    beta = -0.40 #%/C
    gamma = -0.49 #%/C
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    TkPmp = -0.49 * Vmpp/100
    Eff = .152
    A = Pmax/Eff/1000

class asw270p(module):
    make = ""
    model = ""
    Pmax = 270
    Vmpp = 35.2
    Impp = 7.670
    Isc = 8.44
    Voc = 44.4
    #Voc %/C
    beta = -0.33 #%/K
    #Pmax %/K
    gamma = -0.46 #%/K
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    TkPmp = gamma * Vmpp/100
    A = 1.954*.990
    Eff = Pmax/A/1000

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


class testModules(unittest.TestCase):
    """Unit Tests"""
    def setUp(self):
        self.mage250o = mage250().output(950)

    def testMageOutput(self):
        self.assertAlmostEqual(237.509, self.mage250o,3)

if __name__=="__main__":
    #p = generic180()
    series = 14
    #p = sinodeu120()
    #p = motech245()
    #p = astroenergy290()
    #p = asp390()
    p = moduleJ('Mage Solar : Powertec Plus 245-6 MNBS')
    print ":%s:" %p.make
    print ":%s:" %p.model
    p = mage250()
    print p.Eff
    print p 

    print "Vmax:", p.Vmax(-13)*series
    print "Vmin:",p.Vmin(31,25) * series
    print "Vmin 10%:",p.Vmin(31,25) * series*.90

    #print p.output(950)
    #a = pvArray(motech245(), 14,2)
    #a = pvArray(motech245(), 14,2)
    #print a.Vmax(-20)
    #print a.Vmin(33)
    #print a.output(950)
    suite = unittest.TestLoader().loadTestsFromTestCase(testModules)
    unittest.TextTestRunner(verbosity=2).run(suite)
