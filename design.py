import copy
import geo
import epw

def fill(inverter, zipcode, acDcRatio = 1.2, mount="Roof", stationClass = 1, Vmax = 600, bipolar= True):
    """maximize array"""
    tDerate = {"Roof":30,
            "Ground":25,
            "Pole":20}
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(zipcode), stationClass)
    maxV = inverter.array.panel.Vmax(epw.minimum(usaf))
    #NREL suggests that long term degradation is primarily current not voltage
    derate20 = .97
    minV = inverter.array.panel.Vmin(epw.twopercent(usaf),tDerate[mount]) * derate20
    #print "MinV", minV
    if inverter.vdcmax != 0:
         Vmax = inverter.vdcmax
    smax = int(Vmax/maxV)
    #range to search
    pTol = .30
    inverterNominal = inverter.Paco
    psize = inverter.array.panel.Pmax
    solutions = []

    Imax = max(inverter.idcmax,inverter.Pdco*1.0/inverter.mppt_low)
    stringMax = int(round(Imax/inverter.array.panel.Impp))+1

    #Diophantine equation
    for s in range(smax+1):
        if (s*minV) >= inverter.mppt_low:
            for p in range(stringMax):
                pRatio = p*s*psize*1.0/inverterNominal
                if pRatio < (acDcRatio*(1+pTol)) and \
                        pRatio > (acDcRatio*(1-pTol)):
                            inverter.array.shape = [s]*p
                            t = copy.deepcopy(inverter)
                            t.minV = s*minV
                            t.maxV = s*maxV
                            solutions.append(t)
    return solutions

def design(DCsize, panels, inverters):
    designs = []
    for i in inverters:
        for i in panels:
            #expedite.
            pass

if __name__ == "__main__":
    import inverters
    import modules
    zc='27713'
    m = "Mage Solar : USA Powertec Plus 250-6 MNCS"
    ms = modules.module(m)
    system = inverters.inverter("Refusol: 20 kW 480V",modules.pvArray(ms,[11]*6))
    s = fill(system,zc)
    for i in s:
        print i, i.ratio()
