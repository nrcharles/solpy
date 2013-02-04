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

CONDUCTOR_STANDARD_SIZES = ["14","12","10","8","6","4","2","1","1/0","2/0",\
        "3/0","4/0","250","300","350","400","500","600","750"]
#NEC 240.6
OCP_STANDARD_SIZES = [15,20,25,30,35,40,45,50,50,60,70,80,90,100,110,125,150,\
        175,200,225,250,300,350,400,450,500,600,700,800,1000,1200,1600,2000,\
        2500,3000,4000,5000,6000]
OCP_STANDARD_FUSES = [1,3,6,10,15,20,25,30,35,40,45,50,50,60,70,80,90,100,\
        110,125,150,175,200,225,250,300,350,400,450,500,600,601,700,800,1000,\
        1200,1600,2000,2500,3000,4000,5000,6000]
#NEC 310.15(B)(16)
CU_AMPACITY_A30_75 = {"14":20,
        "12":25,
        "10":35,
        "8":50,
        "6":65,
        "4":85,
        "3":100,
        "2":115,
        "1":130,
        "1/0":150,
        "2/0":175,
        "3/0":200,
        "4/0":230,
        "250":255,
        "300":285,
        "350":310,
        "400":335,
        "500":380,
        "600":420,
        "700":460,
        "750":475}
AL_AMPACITY_A30_75 = {"14": None,
        "12":20,
        "10":30,
        "8":40,
        "6":50,
        "4":65,
        "3":75,
        "2":90,
        "1":100,
        "1/0":120,
        "2/0":135,
        "3/0":155,
        "4/0":180,
        "250":205,
        "300":230,
        "350":250,
        "400":270,
        "500":310,
        "600":340,
        "700":375,
        "750":385}
#Ambiant Temperature Correction Factor

PVC_X = {"14" : 0.058,
    "12" : 0.054,
    "10" : 0.050,
    "8" : 0.052,
    "6" : 0.051,
    "4" : 0.048,
    "3" : 0.047,
    "2" : 0.045,
    "1" : 0.046,
    "1/0" : 0.044,
    "2/0" : 0.043,
    "3/0" : 0.042,
    "4/0" : 0.041,
    "250" : 0.041,
    "300" : 0.041,
    "350" : 0.040,
    "400" : 0.040,
    "500" : 0.039,
    "600" : 0.039,
    "750" : 0.038}

AL_X = PVC_X

STEEL_X = {"14" : 0.073,
    "12" : 0.068,
    "10" : 0.063,
    "8" : 0.065,
    "6" : 0.064,
    "4" : 0.060,
    "3" : 0.059,
    "2" : 0.057,
    "1" : 0.057,
    "1/0" : 0.055,
    "2/0" : 0.054,
    "3/0" : 0.052,
    "4/0" : 0.051,
    "250" : 0.052,
    "300" : 0.051,
    "350" : 0.050,
    "400" : 0.049,
    "500" : 0.048,
    "600" : 0.048,
    "750" : 0.048}

PVC_CU = {"14" : 3.100,
    "12" : 2.000,
    "10" : 1.200,
    "8" : 0.780,
    "6" : 0.490,
    "4" : 0.310,
    "3" : 0.250,
    "2" : 0.190,
    "1" : 0.150,
    "1/0" : 0.120,
    "2/0" : 0.100,
    "3/0" : 0.077,
    "4/0" : 0.062,
    "250" : 0.052,
    "300" : 0.044,
    "350" : 0.038,
    "400" : 0.033,
    "500" : 0.027,
    "600" : 0.023,
    "750" : 0.019}

AL_CU = {"14" : 3.100,
    "12" : 2.000,
    "10" : 1.200,
    "8" : 0.780,
    "6" : 0.490,
    "4" : 0.310,
    "3" : 0.250,
    "2" : 0.200,
    "1" : 0.160,
    "1/0" : 0.130,
    "2/0" : 0.100,
    "3/0" : 0.082,
    "4/0" : 0.067,
    "250" : 0.057,
    "300" : 0.049,
    "350" : 0.043,
    "400" : 0.038,
    "500" : 0.032,
    "600" : 0.028,
    "750" : 0.024}

STEEL_CU = {"14" : 3.100,
    "12" : 2.000,
    "10" : 1.200,
    "8" : 0.780,
    "6" : 0.490,
    "4" : 0.310,
    "3" : 0.250,
    "2" : 0.200,
    "1" : 0.160,
    "1/0" : 0.120,
    "2/0" : 0.100,
    "3/0" : 0.079,
    "4/0" : 0.063,
    "250" : 0.054,
    "300" : 0.045,
    "350" : 0.039,
    "400" : 0.035,
    "500" : 0.029,
    "600" : 0.025,
    "750" : 0.021}

PVC_AL = {"14" : 5.100,
    "12" : 3.200,
    "10" : 2.000,
    "8" : 1.300,
    "6" : 0.810,
    "4" : 0.510,
    "3" : 0.400,
    "2" : 0.320,
    "1" : 0.250,
    "1/0" : 0.200,
    "2/0" : 0.160,
    "3/0" : 0.130,
    "4/0" : 0.100,
    "250" : 0.085,
    "300" : 0.071,
    "350" : 0.061,
    "400" : 0.054,
    "500" : 0.043,
    "600" : 0.036,
    "750" : 0.029}

AL_AL = {"14" : 5.100,
    "12" : 3.200,
    "10" : 2.000,
    "8" : 1.300,
    "6" : 0.810,
    "4" : 0.510,
    "3" : 0.410,
    "2" : 0.320,
    "1" : 0.260,
    "1/0" : 0.210,
    "2/0" : 0.160,
    "3/0" : 0.130,
    "4/0" : 0.110,
    "250" : 0.090,
    "300" : 0.076,
    "350" : 0.066,
    "400" : 0.059,
    "500" : 0.048,
    "600" : 0.041,
    "750" : 0.034}

STEEL_AL = {"14" : 5.100,
    "12" : 3.200,
    "10" : 2.000,
    "8" : 1.300,
    "6" : 0.810,
    "4" : 0.510,
    "3" : 0.400,
    "2" : 0.320,
    "1" : 0.250,
    "1/0" : 0.200,
    "2/0" : 0.160,
    "3/0" : 0.130,
    "4/0" : 0.100,
    "250" : 0.086,
    "300" : 0.072,
    "350" : 0.063,
    "400" : 0.055,
    "500" : 0.045,
    "600" : 0.038,
    "750" : 0.031}

_CU = {"14" : 3.140,
    "12" : 1.980,
    "10" : 1.240,
    "8" : 0.778,
    "6" : 0.491,
    "4" : 0.308,
    "3" : 0.245,
    "2" : 0.194,
    "1" : 0.154,
    "1/0" : 0.122,
    "2/0" : .0967,
    "3/0" : .0766,
    "4/0" : .0608,
    "250" : .0515,
    "300" : .0429,
    "350" : .0367,
    "400" : .0321,
    "500" : .0258,
    "600" : .0214,
    "750" : .0171}

_AL = {"14" : 5.170,
    "12" : 3.250,
    "10" : 2.040,
    "8" : 1.280,
    "6" : 0.808,
    "4" : 0.508,
    "3" : 0.403,
    "2" : 0.319,
    "1" : 0.253,
    "1/0" : 0.201,
    "2/0" : 0.159,
    "3/0" : 0.126,
    "4/0" : 0.100,
    "250" : .0847,
    "300" : .0707,
    "350" : .0605,
    "400" : .0529,
    "500" : .0424,
    "600" : .0353,
    "750" : .0282}


#NEC Table 250.122
EGC_CU = {15:"14",
        20:"12",
        60:"10",
        100:"8",
        200:"6",
        300:"4",
        400:"3",
        500:"2",
        600:"1",
        800:"1/0",
        1000:"2/0",
        1200:"3/0",
        1600:"4/0",
        2000:"250",
        2500:"350",
        3000:"400",
        4000:"500",
        5000:"700",
        6000:"800"}

#NEC Table 250.122
EGC_AL = {15:"12",
        20:"10",
        60:"8",
        100:"6",
        200:"4",
        300:"2",
        400:"1",
        500:"1/0",
        600:"2/0",
        800:"3/0",
        1000:"4/0",
        1200:"250",
        1600:"350",
        2000:"400",
        2500:"600",
        3000:"600",
        4000:"750",
        5000:"1200",
        6000:"1200"}

CMIL = {"18":1620,
        "16":2580,
        "14":4110,
        "12":6530,
        "10":10380,
        "8":16510,
        "6":26240,
        "4":41740,
        "3":52620,
        "2":66360,
        "1":83690,
        "1/0":105600,
        "2/0":133100,
        "3/0":167800,
        "4/0":211600,
        "250":250000,
        "300":300000,
        "350":350000,
        "400":400000,
        "500":500000,
        "600":600000,
        "700":700000,
        "750":750000,
        "800":800000,
        "900":900000,
        "1000":1000000,
        "1250":1250000,
        "1500":1500000,
        "2000":2000000}

def ocpSize(a):
    for i in OCP_STANDARD_SIZES:
        if i > a:
            return i

class transformer(object):
    def __init__(self, rating, loss, noload):
        self.rating = rating
        self.loss = loss # load losses
        self.noload = noload #noload loss
    def output(self, pin):
        percent_load=pin*1.0/self.rating
        total_loss = self.loss*percent_load**2+self.noload
        return pin - total_loss

class junction(object):
    """Takes tuples of wire and next junction"""
    def __init__(self, *args, **kwargs):
        self.children = []
        self.rating = 100
        self.phase = 1
        for arg in args:
            self.children.append(arg)
            if arg.phase is not 1:
                self.phase = 3

    def vd(self):
        return max([child.vd() for child in self.children])

    def a(self):
        t = 0
        for child in self.children:
            t += child.a()
        return t

    def i(self,Insolation):
        t = 0
        for child in self.children:
            t += child.i(Insolation)
        return t

class cb():
    def __init__(self, rating, phase =1):
        self.rating = rating
    def ampacity(self):
        return self.rating

class branch():
    def __init__(self, breaker, wire, j):
        self.child = j
        self.breaker = breaker
        self.wire = wire
        self.phase = 1

    def vd(self):
        if self.phase is 1:
            vdrop = 2 * self.child.a() * self.wire.d * self.wire.r() / 1000
            return vdrop + self.child.vd()
    def vdp(self):
        if self.phase is 1:
            return self.vd()/240.9 * 100.0

    def a(self):
        return self.child.a()

    def i(self, Insolation):
        return self.child.i(Insolation)

class m215():
    def __init__(self, number, landscape = True, phase =1):
        self.phase = phase
        self.number = number
        self.a = .896
        self.v = 240
        self.w = 215
        self.wires = 4
        if phase is not 1:
            self.a = 1.0
            self.v = 208
            self.wires = 5
    def vd(self):
        n = self.number + 1
        if self.phase is 1:
            #1 phase theoretical
            #vd = 0.00707n(n+1)al
            l = 1.0
            return n*(n+1)*.00707*self.a*l
        elif self.phase is 3:
            #3 phase emperical
            #y = 0.0036x^2 + 0.0094x + 0.0209
            return 0.0036 * n*n + 0.0094 * n + 0.0209
        else:
            print "ERROR"

class wire():
    def __init__(self, length, size, cu = True):
        self.cu = cu
        self.size = size
        self.d = length
        self.t = 75
    def r(self):
        if self.cu:
            #r2 = r1[1 + a(t2 - 75)]
            #a = 0.00323 for cu
            a = 0.00323
            r1 =  PVC_CU[self.size]
            r2 = r1* (1 + a * (self.t - 75))
            x = PVC_X[self.size]
            z = math.sqrt(r2*r2+x*x)
            return z

class circuit():
    def __init__(self):
        pass
    def r(self):
        pass

class conductor(object):
    def __init__(self, size, material,vdp=0.0):
        self.material = material
        self.size = size
        self.lastVDP = vdp

    def r(self, conduit = ""):
        #print "%s_%s" % (conduit, self.material)
        return globals()["%s_%s" % (conduit,self.material)][self.size]

    def x(self, conduit):
        #lt = "%s_%s" % (conduit,"X")
        #return globals()[lt][self.size]
        return globals()["%s_%s" % (conduit,"X")][self.size]

    def temperature(self,a):
        pass

    def a(self):
        a = {"CU":0.00323,
                "AL":0.00330}
        return a[self.material]
    def __str__(self):
        return "%s %s" % (self.size, self.material)
    def __add__(self, t):
        return t + self.lastVD

#class conduit():
#    def __init__(self,material):
#        self.material = material

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
    phase = 1
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

class engage():
    def __init__(self, inverters, phase = 1, landscape = True, endfed = False):
        self.endfed = endfed
        self.landscape = landscape
        self.phase = phase
        self.s1 = []
        self.s2 = []
        if endfed is True:
            self.s1 = [m215(i,self.landscape,self.phase) for i in range(0,inverters)]
        else:
            a = inverters/2
            self.s1 = [m215(i,self.landscape,self.phase) for i in range(0,a)]
            b = inverters - a 
            self.s2 = [m215(i,self.landscape,self.phase) for i in range(0,b)]

    def vd(self):
        if self.endfed:
            return self.s1[-1].vd()
        else:
            return max(self.s1[-1].vd(), self.s2[-1].vd())
        #if self.phase is 1:
        #    return self.a[0].a * (len(self.a) + len(self.b)) * self.distance
    def a(self):
        if self.phase is 1:
            a = (len(self.s1)+len(self.s2)) * 0.895
            return a
        else:
            return (len(self.s1)+len(self.s2)) /1.732

def findConductor(r, material = "CU",conduit = "PVC", pf = .778, temperature = 75):
    for s in CONDUCTOR_STANDARD_SIZES:
        tr = resistance(conductor(s,material),conduit,pf,temperature)
        if tr < r:
            return conductor(s,material)

def findOCP(oc, material = "CU"):
    for s in OCP_STANDARD_SIZES:
        if s > oc:
            return s
    raise "CurrentTooGreat"

def findEGC(ocp,material="CU"):
    inc = [s for s in iter(EGC_CU)]
    inc.sort()
    for s in inc:
        if s >= ocp:
            if material=="CU":
                return EGC_CU[s]
            else:
                return EGC_AL[s]

def findConductorA(current,material):
    for s in CONDUCTOR_STANDARD_SIZES:
        if globals()["%s_AMPACITY_A30_75" % (material)][s] >= current:
            return conductor(s,material)

def checkAmpacity(c, oca):
    ampacity = globals()["%s_AMPACITY_A30_75" % (c.material)][c.size] 
    print "Ampacity", ampacity
    if ampacity < oca:
        print "Warning: conductor appacity %s is exceeded by OCP rating: %s" % (ampacity,oca)
        for s in CONDUCTOR_STANDARD_SIZES:
            conductor_oc = globals()["%s_AMPACITY_A30_75" % (c.material)][s] 
            if conductor_oc > oca:
                print "Minimum size is %s %s" % (s, c.material)
                return conductor(s,c.material)
    else:
        return c

if __name__ == "__main__":
    #house = netlist()
    #house.append(meter())
    #house.append(junction())
    #a = engage(17, 1, True, True)
    print findConductor(1.2)
    b = engage(17)
    #print b.vd()
    #j1 = junction()
    #j1.append(a)
    #j1.append(b)
    b1 = branch(cb(20),wire(181,"8"),engage(12,phase = 3 ))
    b2 = branch(cb(20),wire(123,"6"),engage(24,phase = 3 ))
    b3 = branch(cb(20),wire(90,"8"),engage(24,phase = 3 ))
    b4 = branch(cb(20),wire(57,"8"),engage(24,phase = 3 ))
    b5 = branch(cb(20),wire(181,"8"),engage(12,phase = 3 ))
    j1 = junction(b1,b2)
    #print "Voltage Drop"
    #print voltagedrop(j1)
    print j1.vd()
    #print "t"

    #print a.vd()
    #print b.vd()
    #w1 = wire( 200, "2/0")
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

