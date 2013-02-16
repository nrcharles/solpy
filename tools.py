def fill(inverter, zipcode, acDcRatio = 1.2, stationClass = 1, Vmax = 600, bipolar= True):
    """maximize array"""
    import geo
    import epw
    name, usaf = geo.closestUSAF( geo.zipToCoordinates(zipcode), stationClass)
    maxV = inverter.array.panel.Vmax(epw.minimum(usaf))
    derate20 = .9
    minV = inverter.array.panel.Vmin(epw.twopercent(usaf)) * derate20
    #print "MinV", minV
    smax = int(inverter.vdcmax/maxV)
    #range to search
    pTol = .30
    inverterNominal = inverter.Paco
    print inverter.make, inverter.model
    print "Nominal AC Power:", inverterNominal
    psize = inverter.array.panel.Pmax
    print "Nominal Panel Power:", round(psize,1)
    solutions = []
    print "I DC Max:%s" % inverter.idcmax
    #Diophantine equation
    for s in range(smax+1):
        if (s*minV) >= inverter.mppt_low:
            for p in range(12):
                pRatio = p*s*psize*1.0/inverterNominal
                if pRatio < (acDcRatio*(1+pTol)) and \
                        pRatio > (acDcRatio*(1-pTol)):
                            sol ="%sW - %sS x %sP - ratio %s" % (round(s*p*psize,1),s,p, round(pRatio,2))
                            solutions.append(sol)
                            inverter.array.series = s
                            inverter.array.parallel = p
    if len(solutions) ==0:
        solutions.append("Error: Solution not found")
    return solutions


if __name__ == "__main__":
    import inverters
    import modules
    zc='44701'
    zc='27713'
    #zc='44050'
    #zc='23173'
    #m = "Suntech Power : STP245-20-Wd"
    #m = "Mage Solar : Powertec Plus 245-6 PL *"
    m = "Mage Solar : Powertec Plus 250-6 MNCS"
    ms = modules.moduleJ(m)
    #ms = modules.mage285()
    #ms = modules.mage250ml()
    system = inverters.inverter("Refusol: 20 kW 480V",modules.pvArray(ms,11,6))
    #print fill(system,zc)
    system = inverters.inverter("Refusol: 24 kW 480V",modules.pvArray(ms,11,6))
    #print fill(system,zc)
    system = inverters.inverter("SMA America: SB7000US-11 277V",modules.pvArray(ms,14,2))
    print fill(system,zc)
    system = inverters.inverter("SMA America: SB8000US-11 277V",modules.pvArray(ms,14,2))
    print fill(system,zc)
    system = inverters.inverter("SMA America: SB6000US-11 277V",modules.pvArray(ms,14,2))
    print fill(system,zc)
    #iname = "Shanghai Chint Power Systems: CPS SCE7KTL-O US (240V) 240V"
    iname = "Refusol: 24 kW 480V"
    print m
    #system = inverters.inverter(iname,modules.pvArray(m,1,1))
    #system = inverters.inverter(iname,modules.pvArray(modules.moduleJ(m),1,1))
    #fill(system,zc,1000)

