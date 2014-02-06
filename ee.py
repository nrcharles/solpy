# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

"""
RULES:
Protect wires
-Wire ampacity
-Heat derating in sun

Voltage drop
-<1% per circuit
-<3% from mains to last inverter
"""
import math
import nec

MATERIAL_MAP = {'AL':'XHHW',
                'CU':'THWN'}

SERVICE_TYPE = {"120":(120,2,1),
    "120/208":(208,3,2),
    "120/240":(240,2,2),
    "240/3":(240,3,1),
    "277/480":(480,3,2),
    "480/3":(480,3,1),
    "400":(400,2,1),
    "700":(700,2,1)
}

CONDUIT_MAP = {"STEEL":"EMT",
    "PVC":"PVC40"}

def findConduit(harness,c='EMT',fill=.40):
    area = 0
    for cond in harness:
        A = (getattr(nec,MATERIAL_MAP[cond.material])[cond.size]/2.0)**2*math.pi
        area += A
    for i in getattr(nec,'%s_TRADE_SIZES' % c):
        if getattr(nec,c)[i]*fill > area:
            return i

def fillPercent(harness, conduit):
    pass

def ocpSize(a):
    """Find standard size of Overcurrent protection"""
    for i in nec.OCP_STANDARD_SIZES:
        if i > a:
            return i
    raise "CurrentTooGreat"

class transformer(object):
    def __init__(self, rating, loss, noload):
        self.rating = rating
        self.loss = loss # load losses
        self.noload = noload #noload loss
    def output(self, pin):
        percent_load=pin*1.0/self.rating
        total_loss = self.loss*percent_load**2+self.noload
        return pin - total_loss

class conductor(object):
    def __init__(self, size, material, insulation = None):
        self.material = material
        self.size = size
        if insulation:
            self.insulation = insulation
        else:
            self.insulation = MATERIAL_MAP[self.material]

    def r(self, conduit = ""):
        #print "%s_%s" % (conduit, self.material)
        return getattr(nec,"%s_%s" % (conduit,self.material))[self.size]

    def x(self, conduit):
        #lt = "%s_%s" % (conduit,"X")
        #return globals()[lt][self.size]
        return getattr(nec,"%s_%s" % (conduit,"X"))[self.size]

    def temperature(self,Inew, Tanew = 30, Tcold = 75, Taold = 30):
        Iold = self.ampacity()
        return Tanew + (Inew*1.0/Iold)**2*(Tcold-Taold)

    def a(self):
        a = {"CU":0.00323,
                "AL":0.00330}
        return a[self.material]

    def ampacity(self, Tanew = 30, Tcold = 75, Taold = 30):
        derate = ((Tcold - Tanew)*1.0/(Tcold - Taold))**.5
        return getattr(nec,"%s_AMPACITY_A30_75" % (self.material))[self.size] * derate

    def vd(self, a, l ,v =240, pf = -1, tAmb = 30, c = 'STEEL' ):
        t = self.temperature(a,tAmb)
        r = resistance( self,c,pf, t)
        vdrop = 2.0 * r * a * l/1000.0
        return vdrop

    def area(self):
        return (getattr(nec,self.insulation)[self.size]/2.0)**2*math.pi

    def __str__(self):
        return "%s %s" % (self.size, self.material)
    def __add__(self, t):
        return t + self.lastVD
    __radd__ = __add__

def resistance(conductor, conduit, pf=None, temperature = 75):
    #Rewrite with PowerFactor
    if pf:
        if pf == -1:
            #worst case
            r = conductor.r(conduit) * (1 + conductor.a() * (temperature -75))
            x = conductor.x(conduit)
            return math.sqrt(r*r+x*x)
        elif pf == "DC":
            return  conductor.r() * (1 + conductor.a() * (temperature -75))
        else:
            theta = math.acos(pf)
            #theta = math.acos(0.7)
            r = conductor.r(conduit) * (1 + conductor.a() * (temperature -75))
            x = conductor.x(conduit)
            z = r * math.cos(theta) + x * math.sin(theta)
            return z
    else:
        r = conductor.r() * (1 + conductor.a() * ( temperature -75))
        return r

def voltagedrop(*args, **kwargs):
    a = 0
    vdrop = 0
    for i in reversed(args):
        if hasattr(i, 'a'):
            a += i.a()
        if hasattr(i, 'd'):
            t = 2*a*i.r()*i.d /1000.0
            vdrop += t 
        if hasattr(i, 'vd'):
            vdrop += i.vd()
    return vdrop

class source():
    def __init__(self,c = .9):
        self.c = c
        self.v = 240
        self.phase = 1

    def a(self):
        return self.c

    def vd(self):
        return 0

class conduit():
    def __init__(self ,tradesize,material):
        self.tradesize = 0
        self.material = ""
        self.length = 0
        self.bundle = []
    def addConductors(self,blah):
        pass


def findConductor(r, material = "CU",conduit = "PVC", pf =-1, tCond = 75):
    for s in nec.CONDUCTOR_STANDARD_SIZES:
        tr = resistance(conductor(s,material),conduit,pf,tCond)
        if tr < r:
            return conductor(s,material)

def minEGC(ocp,material="CU"):
    inc = [s for s in iter(nec.EGC_CU)]
    inc.sort()
    for s in inc:
        if s >= ocp:
            if material=="CU":
                return conductor(nec.EGC_CU[s],material)
            else:
                return conductor(nec.EGC_AL[s],material)

def findEGC(cond, ocp,material="CU"):
    minConductor = conductorAmpacity(ocp,cond.material)
    EGC = minEGC(ocp,material)
    ratio = nec.CMIL[cond.size]*1.0 / nec.CMIL[minConductor.size]
    if ratio > 1.0:
        increased = nec.CMIL[EGC.size]*ratio
        for c in nec.CONDUCTOR_STANDARD_SIZES:
            if nec.CMIL[c] >= increased:
                if nec.CMIL[c] > nec.CMIL[cond.size]:
                    return cond
                else:
                    return conductor(c,material)
    else:
        return EGC

def conductorAmpacity(current,material):
    for s in nec.CONDUCTOR_STANDARD_SIZES:
        if getattr(nec,"%s_AMPACITY_A30_75" % (material))[s] >= current:
            return conductor(s,material)

def checkAmpacity(c, oca, ambient = 30):
    ampacity = c.ampacity(ambient)
    if oca > ampacity:
        #print "Warning: conductor ampacity %s is exceeded by OCP rating: %s" % (round(ampacity),oca)
        for s in nec.CONDUCTOR_STANDARD_SIZES:
            #conductor_oc = globals()["%s_AMPACITY_A30_75" % (c.material)][s] 
            conductor_oc = conductor(s,c.material).ampacity(ambient)
            if conductor_oc >= oca:
                #print "Minimum size is %s %s" % (s, c.material)
                return conductor(s,c.material)
    else:
        return c

def assemble(conductor,current,service="120/240",conduit='PVC'):
    v, conductorN, egcN = SERVICE_TYPE[service]
    ocp = ocpSize(current*1.25)
    egc = findEGC(conductor,ocp,material='CU')
    if nec.CMIL[egc.size] > nec.CMIL['4']:
        egc = findEGC(conductor,ocp,material='AL')
    conduitSize = findConduit([conductor]*conductorN+[egc]*egcN,CONDUIT_MAP[conduit])
    print conductor,': EGC',egc,": %s\"" % conduitSize,CONDUIT_MAP[conduit]

if __name__ == "__main__":
    #house = netlist()
    #house.append(meter())
    #house.append(junction())
    #a = engage(17, 1, True, True)
    print findConductor(1.2)
    #print b.vd()
    #j1 = junction()
    #j1.append(a)
    #j1.append(b)
    #print "Voltage Drop"
    #print voltagedrop(j1)
    #print "t"

    #print a.vd()
    #print b.vd()
    #print a.a
    #print "Voltage Drop"
    #print voltagedrop(w1, w1, b)
    print "resistance"
    print resistance(conductor("400","AL"),"STEEL",.77)
    print resistance(conductor("400","AL"),"STEEL","DC")
    print "transformer"
    t1 = transformer(1000000,8404,2143)
    print t1.output(0)
    print t1.output(500000)
    bund=  [conductor("400","AL"),conductor("400","AL"),conductor("6","CU"),conductor("6","CU")]
    print conductor("8","CU","PV").area()
    print "PV Conduit", findConduit([conductor("8","CU","PV")]*12 + [conductor("6","CU")])
    print "PV Conduit", findConduit([conductor("8","CU","PV")]*4 + [conductor("6","CU")])
    print 
    print "conductor area", bund[0].area()
    print findConduit(bund)
    print "CU EGC", findEGC(conductor("400",'AL'),100)
    print "AL EGC", findEGC(conductor("400",'AL'),100,'AL')
    print "AL EGC", findEGC(conductor("1/0",'AL'),40)
    print "AL EGC", findEGC(conductor("1/0",'AL'),40,'AL')
    print "AL EGC", findEGC(conductor("1",'AL'),100)
    import vd
    cond = vd.vd(18,250,material='AL')
    print "found",cond
    print "EGC", findEGC(cond,18*1.25,'AL')
    print ocpSize(10.1)
    print ocpSize(9)
    print findConductor(.001)
    print conductorAmpacity(200,"CU")
    print checkAmpacity(cond, 20, ambient = 30)
    print assemble(conductor("2","CU","PV"),40)
