import unittest

class module(object):
    STC = 25
    #PV module nameplate DC rating     0.80 - 1.05
    nameplate = .95
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
        return m.Vmpp + (Tadd+ashrae2p-m.STC)*m.TkVmp

class pvArray(module):
    def __init__(self,pname, series, parallel = 1):
        self.panel = pname
        self.series = series
        self.parallel = parallel
    def Vdc(self):
        return self.panel.Vdc() * self.series
    def Vmax(self,ashraeMin):
        return self.panel.Vmax(ashraeMin) * self.series
    def Vmin(self,ashrae2p, Tadd = 30):
        return  self.panel.Vmin(ashrae2p, Tadd)* self.series
    def output(self, Insolation):
        return self.panel.output(Insolation)*self.series*self.parallel

class mage250(module):
    Pmax = 250
    Vmpp = 30.00
    Impp = 8.35
    Isc = 8.85
    Voc = 37.50
    #Uoc %/K
    beta = -0.32
    #Pmax %/K
    gamma = -0.43
    TkVoc = beta * Voc /100
    TkVmp = gamma * Vmpp/100
    A = 1.630 * .982
    Eff = .1562
    nameplate = 1

class mage240(module):
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

class motech245(module):
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

class generic170(module):
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

class testModules(unittest.TestCase):
    def setUp(self):
        self.mage250o = mage250().output(950)

    def testMageOutput(self):
        self.assertAlmostEqual(237.522, self.mage250o,3)

if __name__=="__main__":
    #p = generic180()
    series = 1
    #p = sinodeu120()
    #p = motech245()
    p = mage250()
    print p.Eff

    print p.Vmax(-13) * series
    print p.Vmin(33) * series
    print p.output(950)
    a = pvArray(motech245(), 14,2)
    print a.Vmax(-13)
    print a.Vmin(33)
    print a.output(950)
    suite = unittest.TestLoader().loadTestsFromTestCase(testModules)
    unittest.TextTestRunner(verbosity=2).run(suite)
