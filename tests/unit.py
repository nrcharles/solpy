"""solpy unit tests."""
import unittest
import doctest
import json
import logging
from solpy import pv
from solpy import modules
from solpy import design
from solpy import inverters
from solpy import enphase
logging.basicConfig(level=logging.ERROR)
from solpy import ee


# modules.py
class TestModules(unittest.TestCase):
    def test_module(self):
        model = modules.model_search('Powertec 250 PL')[0]
        p = modules.Module(model)
        self.assertAlmostEquals(p.v_max(-10), 42.3129)
        self.assertAlmostEquals(p.v_dc(), 31.28)
        self.assertAlmostEquals(p.i_dc(), 8.01)
        self.assertAlmostEquals(p.v_min(40), 24.931724)
        self.assertAlmostEquals(p.output(900), 225.49752)

# inverters.py
class TestInverters(unittest.TestCase):
    def test_inverter(self):
        pass

class TestEE(unittest.TestCase):
    def test_inverter(self):
        doctest.DocTestSuite(ee)


# pv.py
# irradiation.py
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
        self.assertAlmostEquals(rs.annual_output, 7689.05)

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
        self.assertEqual(js2, js3)
        self.assertAlmostEquals(rs1.annual_output, rs2.annual_output)

    def test_hourlyNoShading(self):
        p1 = """{"system_name":"Another Happy Customer",
        "zipcode":"44654",
        "tilt":25,
        "azimuth":180,
        "phase":1,
        "voltage":240,
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
        self.assertAlmostEquals(rs1.annual_output, 12939.9)

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
        self.assertAlmostEquals(rs1.annual_output, 9098.56)

#design.py
#tools.py
class TestDesign(unittest.TestCase):
    def test_tools_fill(self):
        m = "Mage Solar : USA Powertec Plus 250-6 MNCS"
        ms = modules.Module(m)
        zc = '27713'
        system = inverters.Inverter("SMA America: SB7000US-11 277V", \
                modules.Array(ms, [{'series':14}]))
        sols = design.tools_fill(system, zc, mount="Roof")
        ans = ['8266.5W : 11S x 3P : ratio 1.18 : 265.0 - 467.0 V', \
                '6012.0W : 12S x 2P : ratio 0.86 : 290.0 - 510.0 V', \
                '9018.0W : 12S x 3P : ratio 1.29 : 290.0 - 510.0 V', \
                '6513.0W : 13S x 2P : ratio 0.93 : 314.0 - 552.0 V', \
                '9769.5W : 13S x 3P : ratio 1.4 : 314.0 - 552.0 V', \
                '7014.0W : 14S x 2P : ratio 1.0 : 338.0 - 595.0 V', \
                '10521.0W : 14S x 3P : ratio 1.5 : 338.0 - 595.0 V']
        ans1 = ['6513.0W : channel 0: 13S x 2P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 0.93 : 323.0 - 552.0 V',
        '7014.0W : channel 0: 14S x 2P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.0 : 348.0 - 595.0 V',
        '8266.5W : channel 0: 11S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.18 : 274.0 - 467.0 V',
        '9018.0W : channel 0: 12S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.29 : 298.0 - 510.0 V',
        '9769.5W : channel 0: 13S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.4 : 323.0 - 552.0 V',
        '10521.0W : channel 0: 14S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.5 : 348.0 - 595.0 V']
        #print 'ans', '\n'.join(ans)
        #print 'sols', '\n'.join(sols)
        self.assertListEqual(ans1, sols)

class TestDesign1(unittest.TestCase):
    def test_generate(self):
        m = "Mage Solar : USA Powertec Plus 250-6 MNCS"
        zc = '27713'
        i_name = "SMA America: SB7000US-11 277V"
        sols = design.generate_options(i_name, m, zc, mount="Roof")
        str_sols = [design.str_format(i) for i in sols]
        ans_1 = ['6513.0W : channel 0: 13S x 2P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 0.93 : 323.0 - 552.0 V',
                '7014.0W : channel 0: 14S x 2P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.0 : 348.0 - 595.0 V',
                '8266.5W : channel 0: 11S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.18 : 274.0 - 467.0 V',
                '9018.0W : channel 0: 12S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.29 : 298.0 - 510.0 V',
                '9769.5W : channel 0: 13S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.4 : 323.0 - 552.0 V',
                '10521.0W : channel 0: 14S x 3P Mage Solar : USA Powertec Plus 250-6 MNCS : ratio 1.5 : 348.0 - 595.0 V']
        self.assertListEqual(ans_1, str_sols)

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
        ts = datetime.datetime(2000, 9, 22, 19)
        weatherData = {}
        weatherData['temperature'] = 25
        weatherData['windSpeed'] = 0
        virrRec = plant.virr(2000, ts, weatherData)
        self.assertAlmostEquals(virrRec['girr'], 437.0)

@unittest.skipIf(not enphase.APIKEY, 'Enphase APIKEY not set')

class TestEnphase(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        """The key should be changed for an application that is testing"""
        self.user_id = '4d7a45774e6a41320a'
        self.systems = enphase.index(self.user_id)

    def test_index(self):
        e1 = """{"systems":
                    [{"system_id":67,
                        "system_name":"Eich Residence",
                        "system_public_name":"Eich Residence",
                        "status":"normal",
                        "timezone":"America/Los_Angeles",
                        "country":"US",
                        "state":"CA",
                        "city":"Sebastopol",
                        "postal_code":"95472",
                        "other_references":["Solarfox"],
                        "connection_type":"ethernet"},
                    {"system_id":239922,
                        "system_name":"Fornage D st",
                        "system_public_name":
                        "Residential System",
                        "status":"normal",
                        "timezone":"America/Los_Angeles",
                        "country":"US",
                        "state":"CA",
                        "city":"Petaluma",
                        "postal_code":"94952",
                        "connection_type":"ethernet"},
                    {"system_id":286840,
                        "system_name":"Rogers, Jim",
                        "system_public_name":"Residential System",
                        "status":"normal",
                        "timezone":"America/Los_Angeles",
                        "country":"US",
                        "state":"CA",
                        "city":"Petaluma",
                        "postal_code":"94952",
                        "connection_type":"ethernet"},
                    {"system_id":339784,
                        "system_name":"Weed Patch Solar",
                        "system_public_name":"Residential System",
                        "status":"normal",
                        "timezone":"America/Denver",
                        "country":"US",
                        "state":"ID",
                        "city":"Mountain Home",
                        "postal_code":"83647",
                        "connection_type":"wifi"},
                    {"system_id":490782,
                        "system_name":"Derek's House - 5 Regalia",
                        "system_public_name":"Derek's House - 5 Regalia",
                        "status":"comm",
                        "timezone":"America/Los_Angeles",
                        "country":"US",
                        "state":"CA",
                        "city":"Novato",
                        "postal_code":"94947-2125",
                        "connection_type":"ethernet"},
                    {"system_id":537438,
                        "system_name":"Wagoner",
                        "system_public_name":"Residential System",
                        "status":"normal",
                        "timezone":"America/Los_Angeles",
                        "country":"US",
                        "state":"CA",
                        "city":"Windsor",
                        "postal_code":"95492",
                        "connection_type":"ethernet"}]}"""
        indexes = [enphase.System(user_id=self.user_id,**i) for i in json.loads(e1)["systems"]]

        self.assertEqual(indexes, self.systems)

    def test_stats(self):
        system67 = [system for system in self.systems if int(system.system_id) == 67][0]
        stats = system67.stats(1430742599, 1430742901)
        e1 = """{"intervals":
                    [{  "powr": 15,
                        "enwh": 1,
                        "devices_reporting": 2,
                        "end_at": 1430742600},
                     {  "powr": 15,
                        "enwh": 1,
                        "devices_reporting": 2,
                        "end_at": 1430742900
                    }],
                 "total_devices": 35,
                 "system_id": 67}"""

        self.assertEqual(stats, json.loads(e1))

    def test_rgm_stats(self):
        pass

    def test_monthly_production(self):
        system67 = [system for system in self.systems if int(system.system_id) == 67][0]

    def test_energy_lifetime(self):
        system67 = [system for system in self.systems if int(system.system_id) == 67][0]
        el = system67.energy_lifetime('2008-01-28', '2008-02-02' )
        e1 = """{   "production":
                        [8388, 7537, 8843, 2039, 8235, 0],
                    "system_id": 67,
                    "start_date": "2008-01-28"}"""
        self.assertEqual(el,json.loads(e1))

    def test_envoys(self):
        system67 = [system for system in self.systems if int(system.system_id) == 67][0]
        envoy = system67.envoys()
        for e in envoy['envoys']:
            e.pop('last_report_at')#last_report_at is always changing don't test that field

        e1 = """{   "system_id": 67,
                    "envoys":
                        [{  "status": "normal",
                            "envoy_id": 434803,
                            "name": "Envoy 121112607295",
                            "part_number": "800-00069-r02",
                            "serial_number": "121112607295"}]}"""

        self.assertEqual(envoy, json.loads(e1))

    def test_summary(self):
        system67 = [system for system in self.systems if int(system.system_id) == 67][0]
        summary  = system67.summary('2008-01-28')
        summary.pop('last_report_at')

        e1 = """{   "status": "normal",
                    "energy_lifetime": 14040,
                    "current_power": 0,
                    "modules": 0,
                    "operational_at": 1201362300,
                    "summary_date": "2008-01-28",
                    "source": "microinverters",
                    "energy_today": 8388,
                    "system_id": 67,
                    "size_w": 0}"""

        self.assertEqual(summary, json.loads(e1))

    def test_inventory(self):
        system67 = [system for system in self.systems if int(system.system_id) == 67][0]
        inventory = system67.inventory()

        e1 = """{   "inverters":
                        [   {"model": "M190", "sn": "030909022461"},
                            {"model": "M190", "sn": "030910024009"},
                            {"model": "M190", "sn": "030909022244"},
                            {"model": "M190", "sn": "030909022445"},
                            {"model": "M190", "sn": "030909022442"},
                            {"model": "M190", "sn": "030910023946"},
                            {"model": "M190", "sn": "030909022271"},
                            {"model": "M190", "sn": "030910023959"},
                            {"model": "M190", "sn": "030909022183"},
                            {"model": "M190", "sn": "030909022272"},
                            {"model": "M190", "sn": "030910024007"},
                            {"model": "M190", "sn": "030910024016"},
                            {"model": "M190", "sn": "030910023983"},
                            {"model": "M190", "sn": "030910023982"},
                            {"model": "M190", "sn": "030909022453"},
                            {"model": "M190", "sn": "030910023947"},
                            {"model": "M190", "sn": "030910024001"},
                            {"model": "M190", "sn": "030909022443"},
                            {"model": "M190", "sn": "030910024029"},
                            {"model": "M190", "sn": "030909022283"},
                            {"model": "M190", "sn": "110923032336"},
                            {"model": "M190", "sn": "110923032378"},
                            {"model": "M190", "sn": "110923032337"},
                            {"model": "M190", "sn": "110923032365"},
                            {"model": "M190", "sn": "110923032368"},
                            {"model": "M190", "sn": "110923032334"},
                            {"model": "M190", "sn": "110923032346"},
                            {"model": "M190", "sn": "110918030057"},
                            {"model": "M190", "sn": "110918030192"},
                            {"model": "M190", "sn": "110918030079"},
                            {"model": "M190", "sn": "110918030185"},
                            {"model": "D380", "sn": "110924032940-A"},
                            {"model": "D380", "sn": "110924032940-B"},
                            {"model": "D380", "sn": "110924032942-A"},
                            {"model": "D380", "sn": "110924032942-B"}],
                    "system_id": 67,
                    "envoys": [{"sn": "121112607295"}]}"""
        self.assertEqual(inventory, json.loads(e1))

# todo: modules that still need unit tests
# ee.py
# vd.py
# geo.py
# expedite.py
# forecast.py
# noaa.py
# setup.py
# thermal.py
# collectors.py
# pathfinder.py
# tmy3.py
# epw.py
# epw_thermal.py
# fisheye.py
# nec.py
# site_analysis.py
# solar_fun.py

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(ee))
    tests.addTests(doctest.DocTestSuite(design))
    return tests

if __name__ == '__main__':
    unittest.main()
