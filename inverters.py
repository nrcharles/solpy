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
    NMPT = .97
    Tfactor = .98

    def __init__(self, array):
        self.array = array
    def Pac(self, Insolation):
        m = self.__class__
        Pdc = self.array.output(Insolation)
        Vdc = self.array.Vdc()
        A = m.Pdco * (1 + m.C1 * (Vdc - m.Vdco))
        B = m.Pso * (1 + m.C2 * (Vdc - m.Vdco))
        C = m.C0 * (1 + m.C3 * (Vdc - m.Vdco))
        Pac = ((m.Paco / (A - B)) - C*(A - B))*(Pdc- B) + C *(Pdc - B)**2
        derated = Pac * m.mismatch * m.NMPT * m.soiling * m.Tfactor * \
                m.dc_wiring * m.connections * m.availability
        return derated
    def I(self,Insolation,Vac):
        return self.Pac(Insolation)/Vac

class m215(inverter):
    #Pdc = PV array max power?
    #Vdc = Vmpp?
    C0 = -0.000068474
    C1 = -0.000796158
    C2 = -0.0268797
    C3 = -0.09924
    Pdco = 224.7
    Paco = 215
    Pso = 0.749507
    Vdco = 28.8966
    Mismatch = 1.0

class sunny6000us(inverter):
    C0 = -0.00000585799
    C1 = 0.0000473779
    C2 = 0.00302826
    C3 = 0.000333289
    Pdco = 6392.01
    Paco = 6000
    Pso = 34.0589
    Vdco = 311.5
    MPPT_low = 260
    MPPT_high = 480


if __name__=="__main__":
    from modules import mage250,pvArray

    p = mage250()
    e = m215(p)
    s = pvArray(p,14,2)
    si = sunny6000us(s)
    print e.Pac(950)
    print e.I(960,240)
    print si.Pac(800)

