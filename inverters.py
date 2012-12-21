import json
class inverter(object):
    """Sandia Model"""
    #Inverter Output = Array STC power * Irradiance * Negative Module Power Tolerance * Soiling * Temperature factor * Wiring efficiency * Inverter efficiency
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

    def __init__(self, model, array):
        self.array = array
        self.properties = None
        inverters = json.loads(open('si.json').read())
        for i in inverters:
            if i['inverter']==model:
                self.properties = i
                break
        if self.properties == None:
            raise Exception("Inverter not found")
        self.ac_voltage = self.properties['ac_voltage']
        self.inverter = self.properties['inverter']
        self.vdcmax = self.properties['vdcmax']
        self.Pdco = self.properties['pdco']
        self.Paco = self.properties['paco']
        self.pnt = self.properties['pnt']
        self.Pso = self.properties['pso']
        self.Vdco = self.properties['vdco']
        self.C0 = self.properties['c0']
        self.C1 = self.properties['c1']
        self.C2 = self.properties['c2']
        self.C3 = self.properties['c3']
        self.idcmax = self.properties['idcmax']
        self.mppt_hi = self.properties['mppt_hi']
        self.mppt_low = self.properties['mppt_low']
        self.make,self.model = self.inverter.split(":",2)

    def Pac(self, Insolation):
        Pdc = self.array.output(Insolation)
        Vdc = self.array.Vdc()
        A = self.Pdco * (1 + self.C1 * (Vdc - self.Vdco))
        B = self.Pso * (1 + self.C2 * (Vdc - self.Vdco))
        C = self.C0 * (1 + self.C3 * (Vdc - self.Vdco))
        Pac = ((self.Paco / (A - B)) - C*(A - B))*(Pdc- B) + C *(Pdc - B)**2
        derate = self.mismatch * self.soiling * self.dc_wiring * self.connections \
                * self.availability# * m.Tfactor #* m.NMPT
        return Pac * derate
    def I(self,Insolation,Vac):
        return self.Pac(Insolation)/Vac

def models():
    """returns list of available inverter models"""
    #return json.loads(open('si.json').read())
    return [i['inverter'] for i in json.loads(open('si.json').read()) ]

def insolationToA(ins, peakA):
    """scale current in response to insolation"""
    pass

if __name__=="__main__":
    from modules import mage250,pvArray

    p = mage250()
    #e = m215(p)
    e = inverter("Enphase Energy: M215-60-SIE-S2x 240V",p)
    s = pvArray(p,14,2)
    s = pvArray(p,14,20*8)
    #si = sb6000us(s)

    print e.Pac(950)
    print e.I(960,240)

