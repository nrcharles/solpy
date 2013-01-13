solpy
-------
Solpy is a python library to model solar system power performance similar to PVWatts or NREL's System Advisor Model(SAM).  I initially started writing this while working in Bangladesh as fairly crude calculator to go from a fisheye panorama to a csv of vectors for shading calculations, however there were several pieces that were added to make it a bit more useful.  Daniel Thomas did work adding the Tang evacuated glass tube model.  I cherry picked some pieces of Brandon Stafford's pysolar for solar positioning although made some changes for my purposes.  There is also a simple module for reading TMY3 data. This tool is very rudimentary, but functional. 

This is primarily a research and analysis tool and there is no guarantee on the calculations.

Features
--------
-Liu & Jordan diffuse irradiance model  
-Perez et al. diffuse irradiance model  
-Sandia Inverter model  
-Sandia Module model  
-NEC voltage drop caculations  

Files
-----
-expedite.py - calculate information needed for the expedited permit process  
-epw.py - EPW weather data  
-fisheye.py - fisheye image to shading vectors  
-tmy3.py - read tmy3 data  
-pv.py - system performance prediction  
-vd.py - voltage drop  

Usage
-----
PV systems are descibed with json.

`{"system_name":"System Name",  
        "zipcode":"17601",  
        "tilt":34,  
        "azimuth":180,  
        "phase":1,  
        "voltage":240,  
        "array":[  
            {"inverter":"SMA America: SB6000US 240V",  
            "panel":"Mage Solar : Powertec Plus 250-6 MNCS",  
            "series":14,  
            "parallel":2  
            }  
            ]}`

If that json was was in a file called template.json, the command to model it would be;

pvcli -f template.json

Ipython
-------
This is the sort of project that lends itself nicely to ipython.  Since discovering that project I've tried to make things flow naturally in that enviroment. I really like the inline graphics of the qtconsole.

$ipython qtconsole --colors=Linux --pylab=inline

![example](http://char1es.net/ipython_pv_example.png)
