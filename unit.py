import modules
import unittest
import json
import pv
import tools
import inverters

class TestModules(unittest.TestCase):
    def test_module(self):
        model = modules.model_search('Powertec 250 PL')[0]
        p = modules.module(model)
        self.assertAlmostEquals(p.Vmax(-10),42.3129)
        self.assertAlmostEquals(p.Vdc(),31.28)
        self.assertAlmostEquals(p.Idc(),8.01)
        self.assertAlmostEquals(p.Vmin(40),24.931724)
        self.assertAlmostEquals(p.output(900),225.49752)

class TestInverters(unittest.TestCase):
    def test_inverter(self):
        pass

class TestModeling(unittest.TestCase):
    def test_annualOutput(self):
        p1 = """{"system_name":"HAPPY CUSTOMER",
        "address":"15013 Denver W Pkwy, Golden, CO",
        "zipcode":"80401",
        "phase":1,
        "voltage":240,
        "array":[
            {"inverter":"Enphase Energy: M215-60-2LL-S2x-IG-NA (240 V) 240V",
            "panel":"Mage Solar : Powertec Plus 250-6 PL",
            "quantity":20,
            "azimuth":180,
            "tilt":25
            }
            ]}"""
        plant = pv.jsonToSystem(json.loads(p1))
        rs = plant.model()
        self.assertAlmostEquals(rs.annualOutput,7262.12)

class TestDesign(unittest.TestCase):
    def test_tools_fill(self):
        import tools
        m = "Mage Solar : USA Powertec Plus 250-6 MNCS"
        ms = modules.module(m)
        zc = '27713'
        system = inverters.inverter("SMA America: SB7000US-11 277V",modules.pvArray(ms,[14]*2))
        sols = tools.fill(system,zc,mount="Roof")
        ans = ['8266.5W : 11S x 3P : ratio 1.18 : 265.0 - 467.0 V',
                '6012.0W : 12S x 2P : ratio 0.86 : 290.0 - 510.0 V',
                '9018.0W : 12S x 3P : ratio 1.29 : 290.0 - 510.0 V',
                '6513.0W : 13S x 2P : ratio 0.93 : 314.0 - 552.0 V',
                '9769.5W : 13S x 3P : ratio 1.4 : 314.0 - 552.0 V',
                '7014.0W : 14S x 2P : ratio 1.0 : 338.0 - 595.0 V',
                '10521.0W : 14S x 3P : ratio 1.5 : 338.0 - 595.0 V']
        self.assertAlmostEquals(ans,sols)

if __name__ == '__main__':
    unittest.main()
