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
from solpy import nec

MATERIAL_MAP = {'AL': 'XHHW',
                'CU': 'THWN'}

SERVICE_TYPE = {"120": (120, 2, 1),
                "120/208": (208, 3, 2),
                "120/240": (240, 2, 2),
                "240/3": (240, 3, 1),
                "277/480": (480, 3, 2),
                "480/3": (480, 3, 1),
                "400": (400, 2, 1),
                "700": (700, 2, 1)}

CONDUIT_MAP = {"STEEL": "EMT", "PVC": "PVC40"}


def find_conduit(harness, conduit='EMT', fill=.40):
    """find size of conduit for conductor bundle

    >>> bund = [Conductor("400", "AL"), Conductor("400", "AL"), \
                Conductor("6", "CU"), Conductor("6", "CU")]
    >>> find_conduit(bund)
    '2'

    """
    total_area = 0
    for cond in harness:
        total_area += cond.area()
    total_area = sum([cond.area() for cond in harness])
    for i in getattr(nec, '%s_TRADE_SIZES' % conduit):
        if getattr(nec, conduit)[i]*fill > total_area:
            return i


def fill_percent(harness, conduit):
    """Calculate fill percent.

    >>> bund = [Conductor("400", "AL"), Conductor("400", "AL"), \
                Conductor("6", "CU"), Conductor("6", "CU")]
    >>> PVC_2 = Conduit('2', 'PVC40')
    >>> fill_percent(bund,PVC_2)
    0.4376148931587117

    """
    total_area = sum([cond.area() for cond in harness])
    return total_area/conduit.internal_area()


def ocp_size(current):
    """Find standard size of Overcurrent protection.

    >>> ocp_size(10.1)
    15

    """
    for i in nec.OCP_STANDARD_SIZES:
        if i > current:
            return i
    raise Exception("CurrentTooGreat")


class Transformer(object):
    """Transformer class.

    >>> T1 = Transformer(1000000, 8404, 2143)

    >>> T1.output(0)
    -2143.0

    >>> T1.output(500000)
    495756.0

    """
    def __init__(self, rating, loss, noload):
        self.rating = rating
        self.loss = loss  # load losses
        self.noload = noload  # noload loss

    def output(self, pin):
        """power after loss"""
        percent_load = pin*1.0/self.rating
        total_loss = self.loss*percent_load**2+self.noload
        return pin - total_loss


class Conductor(object):
    """conductor and methods"""
    def __init__(self, size, material, insulation=None):
        self.material = material
        self.size = size
        self.last_vd = 0
        if insulation:
            self.insulation = insulation
        else:
            self.insulation = MATERIAL_MAP[self.material]

    def r(self, conduit=""):
        """resistance"""
        # print "%s_%s" % (conduit, self.material)
        return getattr(nec, "%s_%s" % (conduit, self.material))[self.size]

    def x(self, conduit):
        """reactanace"""
        # lt = "%s_%s" % (conduit,"X")
        # return globals()[lt][self.size]
        return getattr(nec, "%s_%s" % (conduit, "X"))[self.size]

    def temperature(self, i_new, ta_new=30, tc_old=75, ta_old=30):
        """conductor temperature"""
        i_old = self.ampacity()
        return ta_new + (i_new*1.0/i_old)**2*(tc_old-ta_old)

    def a(self):
        """coefficeint for material"""
        a = {"CU": 0.00323, "AL": 0.00330}
        return a[self.material]

    def ampacity(self, ta_new=30, tc_old=75, ta_old=30):
        """adjusted ampacity"""
        derate = ((tc_old - ta_new)*1.0/(tc_old - ta_old))**.5
        return getattr(nec, "%s_AMPACITY_A30_75" %
                       (self.material))[self.size]*derate

    def vd(self, a, l, v=240, pf=-1, t_amb=30, c='STEEL'):
        """voltage drop"""
        t = self.temperature(a, t_amb)
        r = resistance(self, c, pf, t)
        vdrop = 2.0 * r * a * l/1000.0
        return vdrop

    def area(self):
        """cross sectional area.

        >>> Conductor("8", "CU", "PV").area()
        0.07645379881776121

        """
        return (getattr(nec, self.insulation)[self.size]/2.0)**2*math.pi

    def __str__(self):
        return "%s %s" % (self.size, self.material)

    def __add__(self, t):
        return t + self.last_vd

    __radd__ = __add__


def resistance(conductor, conduit, pf=None, temperature=75):
    """total impedance

    >>> resistance(Conductor("400", "AL"), "STEEL", .77)
    0.07361415039626057

    >>> resistance(Conductor("400", "AL"), "STEEL", "DC")
    0.0529

    """

    if pf:
        if pf == -1:
            # worst case
            r = conductor.r(conduit) * (1 + conductor.a() * (temperature - 75))
            x = conductor.x(conduit)
            return math.sqrt(r*r+x*x)
        elif pf == "DC":
            return conductor.r() * (1 + conductor.a() * (temperature - 75))
        else:
            theta = math.acos(pf)
            # theta = math.acos(0.7)
            r = conductor.r(conduit) * (1 + conductor.a() * (temperature - 75))
            x = conductor.x(conduit)
            z = r * math.cos(theta) + x * math.sin(theta)
            return z
    else:
        r = conductor.r() * (1 + conductor.a() * (temperature - 75))
        return r


def voltagedrop(*args, **kwargs):
    """voltage drop"""
    a = 0
    vdrop = 0
    for i in reversed(args):
        if hasattr(i, 'a'):
            a += i.a()
        if hasattr(i, 'd'):
            t = 2 * a * i.r() * i.d / 1000.0
            vdrop += t
        if hasattr(i, 'vd'):
            vdrop += i.vd()
    return vdrop


class Source(object):
    """Source"""
    def __init__(self, c=.9):
        self.c = c
        self.v = 240
        self.phase = 1

    def a(self):
        return self.c

    def vd(self):
        return 0


class Conduit(object):
    """Conduit"""
    def __init__(self, tradesize, material):
        self.tradesize = tradesize
        self.material = material
        self.bundle = []

    def internal_area(self):
        return getattr(nec, self.material)[self.tradesize]


def find_conductor(r, material="CU", conduit="PVC", pf=-1, t_cond=75):
    """find conductor.

    >>> print find_conductor(1.2)
    8 CU

    """
    for size in nec.CONDUCTOR_STANDARD_SIZES:
        tr = resistance(Conductor(size, material), conduit, pf, t_cond)
        if tr < r:
            return Conductor(size, material)


def min_egc(ocp, material="CU"):
    """find egc for conductor todo: deprecate"""
    inc = [_temp for _temp in iter(nec.EGC_CU)]
    inc.sort()
    for size in inc:
        if size >= ocp:
            if material == "CU":
                return Conductor(nec.EGC_CU[size], material)
            else:
                return Conductor(nec.EGC_AL[size], material)


def find_egc(cond, ocp, material="CU"):
    """find egc for conductor when increased in size

    >>> print find_egc(Conductor("1", 'AL'), 100)
    8 CU

    """
    min_conductor = conductor_ampacity(ocp, cond.material)
    egc_c = min_egc(ocp, material)
    ratio = nec.CMIL[cond.size]*1.0 / nec.CMIL[min_conductor.size]
    if ratio > 1.0:
        increased = nec.CMIL[egc_c.size]*ratio
        for c in nec.CONDUCTOR_STANDARD_SIZES:
            if nec.CMIL[c] >= increased:
                if nec.CMIL[c] > nec.CMIL[cond.size]:
                    return cond
                else:
                    return Conductor(c, material)
    else:
        return egc_c


def egc(ocp, conductor=None, material='CU'):
    """find egc for conductor.

    >>> print egc(100, Conductor("400", 'AL'), 'AL')
    2/0 AL

    """
    if conductor:
        min_conductor = conductor_ampacity(ocp, conductor.material)
        egc_c = min_egc(ocp, material)
        ratio = nec.CMIL[conductor.size]*1.0 / nec.CMIL[min_conductor.size]
        if ratio > 1.0:
            increased = nec.CMIL[egc_c.size]*ratio
            for c in nec.CONDUCTOR_STANDARD_SIZES:
                if nec.CMIL[c] >= increased:
                    if nec.CMIL[c] > nec.CMIL[conductor.size]:
                        return conductor
                    else:
                        return Conductor(c, material)
        else:
            return egc_c
    else:
        inc = [i for i in iter(nec.EGC_CU)]
        inc.sort()
        for size in inc:
            if size >= ocp:
                if material == "CU":
                    return Conductor(nec.EGC_CU[size], material)
                else:
                    return Conductor(nec.EGC_AL[size], material)


def conductor_ampacity(current, material):
    """find conductor ampacity. todo:deprecate"""
    for size in nec.CONDUCTOR_STANDARD_SIZES:
        if getattr(nec, "%s_AMPACITY_A30_75" % (material))[size] >= current:
            return Conductor(size, material)


def check_ampacity(c, oca, ambient=30):
    """check ampacity

    >>> print check_ampacity(Conductor("12", 'CU'), 20)
    12 CU

    """
    ampacity = c.ampacity(ambient)
    if oca > ampacity:
        # print "Warning: conductor ampacity %s is exceeded by OCP rating: %s"\
        # % (round(ampacity),oca)
        for s in nec.CONDUCTOR_STANDARD_SIZES:
            # conductor_oc = globals()["%s_AMPACITY_A30_75" % (c.material)][s]
            conductor_oc = Conductor(s, c.material).ampacity(ambient)
            if conductor_oc >= oca:
                # print "Minimum size is %s %s" % (s, c.material)
                return Conductor(s, c.material)
    else:
        return c


def assemble(conductor, current, service="120/240", conduit='PVC'):
    """assemble bundle of conductor in conduit.

    >>> assemble(Conductor("2", "CU", "PV"), 40)
    2 CU : EGC 4 CU : 1 1/4" PVC40

    """
    v, conductor_n, egc_n = SERVICE_TYPE[service]
    ocp = ocp_size(current*1.25)
    egc_c = find_egc(conductor, ocp, material='CU')
    if nec.CMIL[egc_c.size] > nec.CMIL['4']:
        egc_c = find_egc(conductor, ocp, material='AL')
    conduitSize = find_conduit([conductor] * conductor_n + [egc_c] * egc_n,
                               CONDUIT_MAP[conduit])
    print conductor, ': EGC', egc_c, ": %s\"" % \
        conduitSize, CONDUIT_MAP[conduit]

if __name__ == "__main__":
    import doctest
    doctest.testmod()
