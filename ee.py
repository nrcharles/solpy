"""
RULES:
Protect wires
-Wire ampacity
-Heat derating in sun

Voltage drop
-<1% per circuit
-<3% from mains to last inverter
"""
cu = {    "18":8.08,
    "16":5.08,
    "14":3.19,
    "12":2.01,
    "10":1.26,
    "8":0.786,
    "6":0.510,
    "4":0.321,
    "3":0.254,
    "2":0.201,
    "1":0.160,
    "1/0":0.127,
    "2/0":0.101,
    "3/0":0.0797,
    "4/0":0.0626,
    "250":0.0535,
    "300":0.0446,
    "350":0.0383,
    "400":0.0331,
    "500":0.0256,
    "600":0.0223,
    "700":0.0189,
    "750":0.0176,
    "800":0.0166,
    "900":0.0147,
    "1000":0.0132,
    "1250":0.0106,
    "1500":0.00883,
    "1750":0.00756,
    "2000":0.00662
    }
al = {"18":12.8,
        "16":8.05,
        "14":5.06,
        "12":3.18,
        "10":2.00,
        "8":1.26,
        "6":0.808,
        "4":0.508,
        "3":0.403,
        "2":0.319,
        "1":0.253,
        "1/0":0.201,
        "2/0":0.159,
        "3/0":0.126,
        "4/0":0.100,
        "250":0.0847,
        "300":0.0707,
        "350":0.0605,
        "400":0.0529,
        "500":0.0424,
        "600":0.0353,
        "700":0.0303,
        "750":0.0282,
        "800":0.0265,
        "900":0.0235,
        "1000":0.0212,
        "1250":0.0169,
        "1500":0.0141,
        "1750":0.0121,
        "2000":0.0106
        }

class junction():
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
            r1 =  cu[self.size]
            r2 = r1* (1 + a * (self.t - 75))
            return r2

def voltagedrop(*args, **kwargs):
    a = 0
    vdrop = 0
    phase = 1
    for i in reversed(args):
        print i
        if hasattr(i, 'a'):
            a += i.a()
        if hasattr(i, 'd'):
            t = 2*a*i.r()*i.d /1000.0
            print t
            vdrop += t 
        if hasattr(i, 'vd'):
            print i.vd()
            vdrop += i.vd()
    return vdrop

class source():
    def __init__(self):
        self.a = .9
        self.v = 240
        self.phase = 1

    def a(self):
        return self.a

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

if __name__ == "__main__":
    #house = netlist()
    #house.append(meter())
    #house.append(junction())
    #a = engage(17, 1, True, True)
    b = engage(17)
    print b.vd()
    #j1 = junction()
    #j1.append(a)
    #j1.append(b)
    b1 = branch(cb(20),wire(181,"8"),engage(12,phase = 3 ))
    b2 = branch(cb(20),wire(123,"6"),engage(24,phase = 3 ))
    b3 = branch(cb(20),wire(90,"8"),engage(24,phase = 3 ))
    b4 = branch(cb(20),wire(57,"8"),engage(24,phase = 3 ))
    b5 = branch(cb(20),wire(181,"8"),engage(12,phase = 3 ))
    j1 = junction(b1,b2)
    print "Voltage Drop"
    print voltagedrop(j1)
    print j1.vd()
    print "t"

    #print a.vd()
    print b.vd()
    w1 = wire( 200, "2/0")
    #print a.a
    print "Voltage Drop"
    print voltagedrop(w1, w1, b)
