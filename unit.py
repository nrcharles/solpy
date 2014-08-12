import modules
import unittest
import json
import pv
import tools
import design
import inverters


#modules.py
class TestModules(unittest.TestCase):
    def test_module(self):
        model = modules.model_search('Powertec 250 PL')[0]
        p = modules.Module(model)
        self.assertAlmostEquals(p.v_max(-10),42.3129)
        self.assertAlmostEquals(p.v_dc(),31.28)
        self.assertAlmostEquals(p.i_dc(),8.01)
        self.assertAlmostEquals(p.v_min(40),24.931724)
        self.assertAlmostEquals(p.output(900),225.49752)

#inverters.py
class TestInverters(unittest.TestCase):
    def test_inverter(self):
        pass
#pv.py
#irradiation.py
class TestModeling(unittest.TestCase):
    def test_annual_output1(self):
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
        plant = pv.json_system(json.loads(p1))
        rs = plant.model()
        self.assertAlmostEquals(rs.annual_output,7697.53)

    def test_annual_output2(self):
        p1 = """{"system_name":"HAPPY CUSTOMER",
        "address":"15013 Denver W Pkwy, Golden, CO",
        "zipcode":"80401",
        "tilt":23,
        "azimuth":180,
        "phase":1,
        "voltage":240,
        "array":[
            {"inverter":"SMA America: SB11000TL-US-12 (240V) 240V",
            "panel":"Axitec : AC-250P-156-60S *",
            "series":14,
            "parallel":4,
            "quantity":7
            },
            {"inverter":"SMA America: SB8000TL-US-12 (240V) 240V",
            "panel":"Axitec : AC-250P-156-60S *",
            "series":14,
            "parallel":3,
            "quantity":1
            }
            ]}
            """
        js1 = json.loads(p1)
        plant1 = pv.json_system(js1)
        rs1 = plant1.model()
        js2 = json.loads(json.dumps(plant1.dump()))
        plant2 = pv.json_system(js2)
        js3 = json.loads(json.dumps(plant2.dump()))
        rs2 = plant2.model()
        self.assertDictEqual(js2,js3)
        self.assertAlmostEquals(rs1.annual_output,rs2.annual_output)

    def test_hourlyShading(self):
        p1 = """{"system_name":"Another Happy Customer",
        "zipcode":"44654",
        "tilt":25,
        "azimuth":180,
        "phase":1,
        "voltage":240,
        "shade":{"0": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "1": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 1.0, 0.2, 0.0, 0.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "2": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 1.0, 1.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "3": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "4": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "5": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "6": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "7": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "8": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8, 1.0, 1.0, 0.1, 0.0, 0.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "9": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.9, 1.0, 0.1, 0.0, 0.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "10": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 1.0, 1.0, 1.0, 1.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "11": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 1.0, 1.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
        "array":[
            {"inverter":"Enphase Energy: M215-60-2LL-S2x-IG-NA (240 V) 240V",
            "derate":0.98,
            "panel":"Mage Solar : Powertec Plus 250-6 PL",
            "series":1,
            "parallel":1,
            "scale":36
            }
            ]}"""
        js1 = json.loads(p1)
        plant1 = pv.json_system(js1)
        rs1 = plant1.model()
        self.assertAlmostEquals(rs1.annual_output,8600.66)

#design.py
#tools.py
class TestDesign(unittest.TestCase):
    def test_tools_fill(self):
        m = "Mage Solar : USA Powertec Plus 250-6 MNCS"
        ms = modules.Module(m)
        zc = '27713'
        system = inverters.Inverter("SMA America: SB7000US-11 277V",modules.PvArray(ms,[{'series':14}]))
        sols = design.tools_fill(system,zc,mount="Roof")
        ans = ['8266.5W : 11S x 3P : ratio 1.18 : 265.0 - 467.0 V',
                '6012.0W : 12S x 2P : ratio 0.86 : 290.0 - 510.0 V',
                '9018.0W : 12S x 3P : ratio 1.29 : 290.0 - 510.0 V',
                '6513.0W : 13S x 2P : ratio 0.93 : 314.0 - 552.0 V',
                '9769.5W : 13S x 3P : ratio 1.4 : 314.0 - 552.0 V',
                '7014.0W : 14S x 2P : ratio 1.0 : 338.0 - 595.0 V',
                '10521.0W : 14S x 3P : ratio 1.5 : 338.0 - 595.0 V']
        self.assertListEqual(ans,sols)

class TestDesign1(unittest.TestCase):
    def test_generate(self):
        m = "Mage Solar : USA Powertec Plus 250-6 MNCS"
        zc = '27713'
        i_name = "SMA America: SB7000US-11 277V"
        sols = design.generate_options(i_name,m,zc,mount="Roof")
        str_sols = [design.str_format(i) for i in sols]
        ans_1 = ['6513.0W : channel 0: 13S x 2P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 0.93 : 323.0 - 552.0 V',
                '7014.0W : channel 0: 14S x 2P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.0 : 348.0 - 595.0 V',
                '8266.5W : channel 0: 11S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.18 : 274.0 - 467.0 V',
                '9018.0W : channel 0: 12S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.29 : 298.0 - 510.0 V',
                '9769.5W : channel 0: 13S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.4 : 323.0 - 552.0 V']
        self.assertListEqual(ans_1,str_sols)

class TestVirr(unittest.TestCase):
    def test_virr1(self):
        import datetime
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
        plant = pv.json_system(json.loads(p1))
        ts =datetime.datetime(2000,9,22,19)
        weatherData = {}
        weatherData['temperature'] = 25
        weatherData['windSpeed'] = 0
        virrRec = plant.virr(2000,ts, weatherData)
        self.assertAlmostEquals(virrRec['girr'],437.0)

#todo: modules that still need unit tests
#ee.py
#vd.py
#geo.py
#expedite.py
#forecast.py
#enphase.py
#noaa.py
#setup.py
#thermal.py
#collectors.py
#pathfinder.py
#tmy3.py
#epw.py
#epw_thermal.py
#fisheye.py
#nec.py
#site_analysis.py
#solar_fun.py

if __name__ == '__main__':
    unittest.main()
