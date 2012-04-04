class inverter(object):
    """Sandia Model"""
    def __init__(self, array):
        self.array = array
    def Pac(self, Insolation):
        m = self.__class__
        Pdc = self.array.output(Insolation)
        Vdc = self.array.Vmpp
        A = m.Pdco * (1 + m.C1 * (Vdc - m.Vdco))
        B = m.Pso * (1 + m.C2 * (Vdc - m.Vdco))
        C = m.C0 * (1 + m.C3 * (Vdc - m.Vdco))
        Pac = ((m.Paco / (A - B)) - C*(A - B))*(Pdc- B) + C *(Pdc - B)**2
        return Pac
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

if __name__=="__main__":
    from modules import mage250
    p = mage250()
    e = m215(p)
    print e.Pac(950)
    print e.I(960,240)

