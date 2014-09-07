.. solpy documentation master file, created by
   sphinx-quickstart on Tue Sep  2 20:44:36 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to solpy
================

Solpy is a python library to model solar system power performance similar to PVWatts or NREL's System Advisor Model(SAM).  This is primarily a research and analysis tool and there is no guarantee on the calculations.

Quick Start
===========

This is an example of modeling systems annual performance with no shade.

.. highlight:: python
.. code-block:: python

    from solpy import pv
    import json

    jsonstring = """
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
        }"""

    plant = pv.json_system(json.loads(jsonstring))
    print plant.model()
    #Year 1 Annual _output: 8395.12 kWh

Contents:

.. toctree::
   models
   modules
   inverters
   pv
   design
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

