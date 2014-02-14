import modules
import unittest
import json

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
        import pv
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


if __name__ == '__main__':
    unittest.main()
