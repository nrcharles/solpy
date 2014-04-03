solpy
-------
Solpy is a python library to model solar system power performance similar to PVWatts or NREL's System Advisor Model(SAM).  I initially started writing this while working in Bangladesh as fairly crude calculator to go from a fisheye panorama to a csv of vectors for shading calculations, however there were several pieces that were added to make it a bit more useful for both analyis and design.  
Daniel Thomas did work adding the Tang evacuated glass tube model. Pyephem was added for solar positioning.  There is also a simple module for reading TMY3 data. This tool is rudimentary, but functional.  

This is primarily a research and analysis tool and there is no guarantee on the calculations.

Features
--------
-Liu & Jordan diffuse irradiance model  
-Perez et al. diffuse irradiance model  
-Sandia Inverter model  
-NEC voltage drop caculations  
-Basic System Validation  
-Basic string sizing library  
-Simple Parametric System Design tools  
-realtime system performance forecasting using weather data  

Files
-----
-design.py - parametric design library
-enphase.py - Enphase API wrapper  
-epw.py - EPW weather data functions
-expedite.py - calculate information needed for the expedited permit process  
-fisheye.py - fisheye image to shading vectors  
-forecast.py - forecast.io API wrapper  
-noaa.py - NOAA weather data API wrapper  
-pv.py - system performance prediction  
-pvcli - cli for pv modeling using historic weather data--
-tmy3.py - read tmy3 data  
-vd.py - voltage drop  

Usage
-----
PV systems are descibed with json. For example:

    {"system_name":"System Name",
        "zipcode":"17601",
        "tilt":34,
        "azimuth":180,
        "phase":1,
        "voltage":240,
        "array":[
            {"inverter":"SMA America: SB6000US 240V",
            "panel":"Mage Solar : USA Powertec Plus 250-6 MNCS",
            "series":14,
            "parallel":2}
            ]
        }

If json in a file called i.e. template.json, can be modeled from cli.

    pvcli -f template.json

Ipython
-------
This is the sort of project that lends itself nicely to ipython.  Since discovering that project I've tried to make things flow naturally in that enviroment. I really like the inline graphics of the qtconsole.

$ipython qtconsole --colors=Linux --pylab=inline

![example](http://char1es.net/ipython_pv_example.png)

Basic System Validation
-----------------------
There is support for simple design validation from the command line warning for overvoltage or excessive ratios.

    ncharles@vm0 $ cat unit.json 
    {"system_name":"HAPPY CUSTOMER",
            "address":"15013 Denver W Pkwy, Golden, CO",
            "zipcode":"80401",
            "phase":1,
            "voltage":240,
            "array":[
                {"inverter":"SMA America: SB3000TL-US 240V *",
                "tilt":25,
                "azimuth":180,
                "panel":"Mage Solar : Powertec Plus 300-6 PL *",
                "shape":[{"series":6,
                "parallel":1},
                {"series":6,
                "parallel":1}],
                "scale":1
                },
                {"inverter":"Enphase Energy: M215-60-2LL-S2x-IG-NA (240 V) 240V",
                "panel":"Mage Solar : Powertec Plus 250-6 PL",
                "quantity":20,
                "azimuth":180,
                "tilt":25
                }
                ]}

    ncharles@vm0 $ expedite.py -f unit.json 
    HAPPY CUSTOMER - 15013 Denver W Pkwy, Golden, CO 80401
    7.3 KW AC RATED
    8.62 KW DC RATED
    System AC Output Current: 30.4 A
    Nominal AC Voltage: 240 V

    Minimum Temperature: -22.9 C
    2 Percent Max Temperature: 30.2 C
    Weather Source: DENVER/CENTENNIAL [GOLDEN - NREL] 724666

    PV Module Ratings @ STC
    Module Make: Mage Solar
    Module Model: Powertec Plus 300-6 PL *
    Quantity: 12
    Max Power-Point Current (Imp): 8.01 A
    Max Power-Point Voltage (Vmp): 37.51 V
    Open-Circuit Voltage (Voc): 45.19 V
    Short-Circuit Current (Isc): 8.66 A
    Maximum Power (Pmax): 300.5 W

    Inverter Make: SMA America
    Inverter Model:  SB3000TL-US 240V *
    Quantity: 1
    Max Power: 3.0 KW
    Max AC Current: 12.5 A
    DC Operating Current: 16.0 A
    DC Short Circuit Current: 17.3 A
    DC Operating Voltage: 225.1 V
    System Max DC Voltage: 311.4 V
    Pnom Ratio: 1.2

    PV Module Ratings @ STC
    Module Make: Mage Solar
    Module Model: Powertec Plus 250-6 PL
    Quantity: 20
    Max Power-Point Current (Imp): 8.01 A
    Max Power-Point Voltage (Vmp): 31.28 V
    Open-Circuit Voltage (Voc): 37.66 V
    Short-Circuit Current (Isc): 8.66 A
    Maximum Power (Pmax): 250.6 W

    Inverter Make: Enphase Energy
    Inverter Model:  M215-60-2LL-S2x-IG-NA (240 V) 240V
    Quantity: 20
    Max Power: 0.2 KW
    Max AC Current: 0.9 A

    Array Azimuth: 180 Degrees
    Array Tilt: 25 Degrees
    December 21 9:00 AM Sun Azimuth: 138.2 Degrees
    December 21 9:00 AM Sun Altitude: 14.3 Degrees
    December 21 3:00 PM Sun Azimuth: 222.2 Degrees
    December 21 3:00 PM Sun Altitude: 14.3 Degrees
    Magnetic declination: 9.0 Degrees
    Minimum Row space ratio: 2.95

    Minimum Bundle
    8 CU : EGC 10 CU : 1/2" EMT
