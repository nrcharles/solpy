Theory and model interaction
============================

Modeling the solar contribution on a structure requires a strong an understanding the solar resource. This is a synthesis of many components starting with external flux (ETR), ephemeris of the sun, atmospheric conditions and obstructions and albedo.

.. graphviz:: solpy.gv

This graph shows the interaction of models. Models can be connected to interact in different ways. For example shading obstructions can be applied after irradiance has been calculated.  This is the method some tools in the solar industry such as the Solar Pathfinder use to simplify the process. However it can be applied earlier to better estimate diffuse and reflected components.

---------
Ephemeris
---------

The ephemeris, or position of the sun, can be calculated at a time using algorithms such as the Sun Position Algorithim (SPA), solpy uses the pyephem package currently.

----------------
Clear Sky Models
----------------

Irradiance calculations generally involves some level of modeling since historic weather data is generally not available at the correct orientation for the site. A synthesis of irradiance starts starts with clear sky models. A value for external flux (ETR) is calculated and adjusted for atmospheric conditions such as airmass. The most common clear sky models are from Liu and Jordan, and Bird. These models calculate the parameters of Direct Normal Irradiance (DNI), Global Horizontal Irradiance (GHI) and Diffuse Horizontal Irradiance (DHI).


-------------
Cloud Shading
-------------
Having estimated the clear sky component, clouds must be accounted for. There has been empirical correlation between and cloud cloud cover C and bright sunshine :math:`\sigma`.

.. math::
    \kappa = aC+bC^2

    \sigma = 1 - \kappa

The coefficients a and b are determined using least squares regression fit for the observed values of cloud shade. The complement of :math:`\sigma` is often called cloud shade and can be used to adjust the clear sky components.

---------------------------------
Typical Meteorological Year (TMY)
---------------------------------

The alternative to synthetic irradiance is using Typical Meteorological Year (TMY) data sets. These data sets are chosen based on historical weather data measured at various Airport weather stations. Monthly data is cherry picked to create annual datasets representational of typical weather for a location. TMY3 is the current version and gives measured GHI, DNI, DHI, ETR, cloud index as well as various other ambient conditions.

----
Beam
----

These general irradiance components need to be adapted to the local site and orientation. The beam component of radiation is based on DNI and is adjusted for the angle of incidence. Angle of incidence is calculated where Σ is tilt of collector and :math:`\phi_{c}` is azimuth of collector.

.. math::

    \cos \theta_{I} = \cos \alpha \cos (\phi_{s} - \phi_{c}) \sin \Sigma + \sin \alpha \cos \Sigma

The beam component is then calculated.

.. math::
    I_{beam} = I_{DNI} \cos \theta_{I}


----------------
Ground Reflected
----------------


The ground reflected component of irradiance is largely a function of albedo (:math:`\rho`) and incident angle. It is well characterized by the function:

.. math::
    I_{reflected} = \rho (I_{beam} + I_{diffuse})(\frac{1-\cos \Sigma}{2})

------------------
Diffuse Sky models
------------------

Calculating the diffuse sky irradiation component is the area with the least consensus. Noorian, et al. compare 12 different models and that is not an exhaustive list. In general they fall into two categories: Isotropic and non-isotropic. Isotropic models assume that the diffuse radiation is uniform across the sky. Liu \& Jordan developed a commonly used isotropic diffuse model:

.. math::
    I_{diffuse} = DHI\cdot\frac{1 + \cos \theta_{c}}{2}

Anisotropic models are much more complicated. The Perez 90 model is often used but is much more complicated and was developed around computer simulation. The basic form is seen in the following equation where the coefficients are developed from empirical data.

.. math::
    0.5[1-F'_{1}](1+\cos \theta_{c})+F'_{1}\frac{a}{b} + F'_{2}\sin \theta_{c}

-------------------------------------
Total Irradiance on an inclined plane
-------------------------------------

.. math::
    I_{total} = I_{beam} + I_{diffuse} + I_{reflected}

---------------------
PV Module Temperature
---------------------

NREL proposes a 3 parameter model for PV module temperature.

.. math::
    T_{module}(^{\circ}C ) = 0.943\cdot T_{ambient} + 0.028\cdot I_{total} - 1.528 \cdot WindSpeed + 4.3

-------------------
CEC PV module model
-------------------

The single diode model is the most common module model.

http://pvpmc.org/modeling-steps/module-iv-curve/diode-equivalent-circuit-models/
http://pvpmc.org/pv-lib/functions-by-catagory/pvl_calcparams_desoto/

Solpy currently doesn't use this by default because of performance issues, rather it uses a simpler formuation.

.. math::
    Power = \frac{I_{total}}{1000} \cdot I_{mpp} \cdot ( V_{mpp} - tk_{Vmp} \cdot (25-T_{module}))

---------------------
Sandia Inverter Model
---------------------

Inverter power is calculated using the Sandia Inverter model described in King, David L, Sigifredo Gonzalez, Gary M Galbraith, and William E Boyson. 2007. “Performance Model for Grid-Connected Photovoltaic Inverters.”

.. math::

    P_{ac} = {(P_{aco}/(A-B)) - C\cdot(A-B)}\cdot(P_{dc}-B)+C\cdot(P_{dc}-B)^2

where:

.. math::

    A = P_{dco}\cdot(1+C_{1}(V_{dc}-V_{dco}))

    B = P_{so}\cdot(1+C_{2}(V_{dc}-V_{dco}))

    C = C_{o}\cdot(1+C_{3}(V_{dc}-V_{dco}))
