#!/usr/bin/python
# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

"""Calculate different kinds of radiation components via default values

"""
from math import radians
from math import degrees
from math import fabs
from math import pi
from math import exp
from numpy import sin, cos, arccos
import datetime
import ephem
global tilt
global azimuth
global place
global horizon

def airmass(zenith):
    """returns airmass for zenith in radians"""
    #Pickering 2002 footnote 39
    #h = apparant altitude
    h =  fabs(90 - degrees(zenith))
    m = 0
    #print degrees(zenith)
    #if dni > 10:
    m = 1/(sin(radians(h+244/(165+47*h**1.1))))
    #Young
    #m1 = 0
    #if degrees(zenith) < 96:
    #    m1 = 1/(cos(zenith) + 0.50572*(6.07995+90-degrees(zenith))**-1.6364)
    #print m,m1
    return m

def eBin(clearness):
    #Perez et al. 1990 Table 1
    if clearness > 6.2:
        return 7
    if clearness > 4.5:
        return 6
    if clearness > 2.8:
        return 5
    if clearness > 1.95:
        return 4
    if clearness > 1.5:
        return 3
    if clearness > 1.23:
        return 2
    if clearness > 1.065:
        return 1
    return 0

def perez(dni,hdi,etr,S,theta,zenith):
    """Perez ee al. 1990
    Diffuse irradiance and illuminance on tilted surfaces
    """
    #theta is the incidence angle of the sun
    #Xh = horizontal diffuse
    Z = zenith
    Dh = hdi
    #Xh can be Illumanince if desired
    Xh = Dh

    m = airmass(zenith)

    I = etr
    k = 1.041  #for Z in radians

    #(1)
    e = 0
    if Dh > 0:
        clearness = ((Dh+dni)/Dh+k*Z**3)/(1.0+k*Z**3)
        e = eBin(clearness)
    #print "hdi",hdi,"clearness",e
    #(2)
    delta = 0
    if I is not 0:
        delta = Dh*m/I

    #Table 6
    #Irradiance model
    IRR = [[-0.008, 0.588,-0.062,-0.060, 0.072,-0.022],
            [0.130, 0.683,-0.151,-0.019, 0.066,-0.029],
            [0.330, 0.487,-0.221, 0.055,-0.064,-0.026],
            [0.568, 0.187,-0.295, 0.109,-0.152,-0.014],
            [0.873,-0.392,-0.362, 0.226,-0.462, 0.001],
            [1.132,-1.237,-0.412, 0.288,-0.823, 0.056],
            [1.060,-1.600,-0.359, 0.264,-1.127, 0.131],
            [0.678,-0.327,-0.250, 0.156,-1.377, 0.251]]
    #Illumanince
    ILL = [ [0.011, 0.570,-0.081,-0.095, 0.158,-0.018],
            [0.429, 0.363,-0.307, 0.050, 0.008,-0.065],
            [0.809,-0.054,-0.442, 0.181,-0.169,-0.092],
            [1.014,-0.252,-0.531, 0.275,-0.350,-0.096],
            [1.282,-0.420,-0.689, 0.380,-0.559,-0.114],
            [1.426,-0.653,-0.779, 0.425,-0.785,-0.097],
            [1.485,-1.214,-0.784, 0.411,-0.629,-0.082],
            [1.170,-0.300,-0.615, 0.518,-1.892,-0.055]]

    #3.2
    a = max(0,cos(theta))
    b = max(0.087,cos(Z))

    F1= IRR[e][0] + IRR[e][1]*delta + IRR[e][2]*Z
    F2= IRR[e][3] + IRR[e][4]*delta + IRR[e][5]*Z
    #print F1,F2

    #3.2.2 Illumanince Model
    #(9)
    Xc = Xh*((1-F1)*(1+cos(S))/2 + F1*a/b+F2*sin(S))
    #print Xc
    #Xc = max(0,Xc)
    #Xc = Xh*(.5*(1-F1)*(1+cos(beta)) + F1*a/b+F2*sin(beta))

    #possible bug?  not sure why the negative insolation sometimes
    return max(Xc,0.0)

def ephemSun(place,utc_datetime):
    latitude, longitude = place
    o = ephem.Observer()
    o.date =  utc_datetime
    o.lat = radians(latitude)
    o.lon = radians(longitude)
    az = ephem.Sun(o).az
    alt = ephem.Sun(o).alt
    return az, alt

def irradiation(record, place, horizon = None, t = 0.0, array_azimuth = 180.0, model = 'lj'):
    Gh = int(record['GHI (W/m^2)'])
    Dh = int(record['DHI (W/m^2)'])
    Bh = int(record['DNI (W/m^2)'])
    etr = int(record['ETR (W/m^2)'])

    #theta = incidence angle of the sun
    #todo: SUNY uses average for time period. This is really and integration
    #function and some error maybe introduced as is. This should be evaluated.
    az,alt = ephemSun(place,record['utc_datetime'])

    slope = radians(t)
    aaz = radians(array_azimuth+180)
    Z = pi/2-alt
    theta = arccos(cos(Z)*cos(slope) + sin(slope)*sin(Z)*cos(az - pi - aaz))
    S = radians(t) #
    return totalIRR(Gh,Dh,Bh,etr,az,alt,S,theta,horizon,model)

def totalIRR(Gh,Dh,Bh,etr,az,alt,S,theta,horizon=None, model = 'lj'):
    Z = pi/2-alt
    nA = degrees(az) % 360-180
    if horizon:
        if horizon(nA) > degrees(theta):
            Bh = 0
            print "shaded", nA,degrees(theta),horizon(nA)
    #Z = solar Zenith angle

    #NREL Manual
    Bth = max(0,Bh * cos(theta))

    #sky-diffuse
    Dth = 0
    if model == "badescu":
        #Badescu 2002 (badescu)
         rd = 3+cos(2*S)/4
         Dth = rd*Dh
    if model == "tian":
         #Tian et al. 2001 (tian)
         rd = 1 -S/(2 *pi)
         Dth = rd*Dh
    if model == "lj":
         #Liu and Jordan (lj)
         rd = (1+cos(S))/2
         Dth = rd*Dh
    if model == "p9":
         Dth = perez(Bh, Dh, etr, S, theta, Z)

    #ground diffuse p = ground reflectivity
    p = 0.2
    Rth = Gh*p*(1-cos(S))/2 #?

    if S > 0:
        return Bth + Dth +Rth
    else:
        return Gh

def airMassRatio(altitude):
    #Masters, p. 412
    return (1/sin(altitude))

def apparentExtraterrestrialFlux(day):
    #Masters, p. 412
    return 1160 + (75 * sin(((2*pi)/365) * (day - 275)))

def dayOfYear(utc_datetime):
    start = datetime.datetime(utc_datetime.year, 1, 1, tzinfo=utc_datetime.tzinfo)
    delta = (utc_datetime - start)
    return delta.days

def opticalDepth(day):
    #Masters, p. 412
    return 0.174 + (0.035 * sin((2*pi/365) * (day - 100)))

def directNormal(utc_datetime, altitude):
    #Masters, p. 413
    if(altitude > 0):
        day = dayOfYear(utc_datetime)
        flux = apparentExtraterrestrialFlux(day)
        optical_depth = opticalDepth(day)
        air_mass_ratio = airMassRatio(altitude)
        return flux * exp(-1 * optical_depth * air_mass_ratio)
    else:
        return 0.0

def globalHorizontal(Ib,theta,n):
    C = 0.095 + 0.04 * sin((2*pi/365*(n-100)))
    #print "theta",theta
    hDirect = Ib*cos(theta)
    return C* Ib + hDirect

def diffuseHorizontal(altitude,Ib,n):
    #Masters p. 416
    C = 0.095 + 0.04 * sin((2.*pi/365*(n-100)))
    return Ib *C

def blave(timestamp, place, tilt = 0, azimuth = 180, cloudCover = 0.0):
    #synthetic irradiance
    az,alt = ephemSun(place,timestamp)

    Z = pi/2-alt
    aaz = radians(azimuth+180)
    slope = radians(tilt)
    #incidence angle
    theta = arccos(cos(Z)*cos(slope) + \
            sin(slope)*sin(Z)*cos(az - pi - aaz))

    Bh,Gh,Dh,ETR =  synthetic(timestamp, alt,az,theta, cloudCover)

    record = {}
    record['utc_datetime'] = timestamp
    record['DNI (W/m^2)'] = Bh #8 Direct normal irradiance
    record['GHI (W/m^2)'] = Gh #5 Global horizontal irradiance
    record['DHI (W/m^2)'] = Dh #11 Diffuse horizontal irradiance
    record['ETR (W/m^2)'] = ETR

    return record

def synthetic(timestamp,alt, az, theta, cloudCover):
    #Palescu 2013 (3.16)
    a=.25
    b= .5
    cs = 1 - (a*cloudCover + b*cloudCover**2)

    #Irradiance
    Bh = directNormal(timestamp,alt) * cs
    day = dayOfYear(timestamp)
    Dh = diffuseHorizontal(alt,Bh,day)

    #todo: should this theta include tilt of collector?
    Gh = globalHorizontal(Bh,theta,day)
    ETR = apparentExtraterrestrialFlux(day)
    #print Gh, Bh, Dh #, ETR
    return Bh,Gh,Dh, ETR

def irrGuess(timestamp, irradiance, solarAlt, solarAz, surfaceTilt, surfaceAz):
    "angles in radians"
    Z = pi/2-solarAlt
    theta = arccos(cos(Z)*cos(surfaceTilt) + \
            sin(surfaceTilt)*sin(Z)*cos(solarAz- pi - surfaceAz))
    girr = 0
    cloudCover = 1.
    iteration = 2
    Bh,Gh,Dh,etr = synthetic(timestamp, solarAlt,solarAz,theta,0.)
    #totalIRR(Gh,Dh,Bh,etr,az,alt,S,theta,horizon=None, model = 'lj'):
    maxirr = totalIRR(Gh,Dh,Bh,etr,solarAz,solarAlt,surfaceTilt,theta, model = 'perez')
    if irradiance > maxirr:
        raise Exception('irradiance exceeds clear sky max')
    while round(irradiance,0) != round(girr,0):
        #todo: improve non linear search routine
        Bh,Gh,Dh,etr = synthetic(timestamp, solarAlt,solarAz,theta,cloudCover)
        girr = totalIRR(Gh,Dh,Bh,etr,solarAz,solarAlt,surfaceTilt,theta, model = 'lj')
        if girr <= irradiance:
            cloudCover = cloudCover - 1./(iteration**2)
        else:
            cloudCover = cloudCover + 1./(iteration**2)
        iteration += 1
        if iteration > 35:
            raise Exception('too many iterations')
    record = {}
    record['DNI (W/m^2)'] = Bh #8 Direct normal irradiance
    record['GHI (W/m^2)'] = Gh #5 Global horizontal irradiance
    record['DHI (W/m^2)'] = Dh #11 Diffuse horizontal irradiance
    record['ETR (W/m^2)'] = etr
    record['cloudCover'] = cloudCover
    return record

def moduleTemp(irradiance,weatherData):
    #todo: Maybe Sandia Module Temperature instead?
    #TamizhMani 2003
    tAmb = (weatherData['temperature'] - 32) * 5/9
    windSpd = weatherData['windSpeed']
    tModule = .945*tAmb +.028*irradiance - 1.528*windSpd + 4.3
    return tModule

#what are good default values?
def bird(Z, P, tau38=0.05, tau5=0.05, rg=.2, Uw=0.0, Uo=0.32, Ba=0.84, K1 = 0.385):
    """Bird clear sky model 1981
    Solar Constant
    Z = Zenith angle (radians, Bird uses degrees but I converted formulas) 
    P = Surface Pressure(millibars)
    rg = ground albedo
    Uw = precipitable water vapor (cm)
    Uo = total ozone (cm)
    tau5,tau38 = trubidity at 0.5 and/or 0.38um
    Ba = aerosol forward scattering ratio (0.84) recommended
    """
    #Extraterrestiral solar irradiance
    Io = 1353.0
    M = (cos(Z)+0.15*(93.885-degrees(Z))**-1.25)**-1
    tau_A = 0.275*tau38*tau5
    TA = exp(-tau_A**0.873*(1+tau_A-tau_A**0.7088)*M**0.9108)
    TAA = 1-K1*(1-M+M**1.06)*(1-TA)
    TAS = TA/TAA
    Tas = TAS #???!!! Tas seems to be Watt Model but it's refed by Bird
    rs = 0.0685+(1-Ba)*(1.0-Tas)
    Mp = M*P/1013
    Tr = exp(-0.0903*Mp**0.84*(1+Mp-Mp**1.01))
    #print "Tr",Tr

    Xo = Uo*M

    To = 1-0.1611*Xo*(1+139.48*Xo)**-0.3035 \
            -0.002715*Xo*(1+0.044*Xo+0.0003*Xo**2)**-1
    #print "To",To
    Tum = exp(-0.0127*Mp**0.26)
    #print "Tum",Tum

    Xw = Uw*M
    Tw = 1-2.4959*Xw*((1+79.034*Xw)**0.6828+6.384*Xw)**-1
    #print "Tw",Tw
    Ta = exp(-tau_A**0.873*(1+tau_A - tau_A**0.7088)*M**0.9108)
    #print "Ta",Ta
    Taa = 1-K1*(1-M+M**1.06)*(1-tau_A)

    #Direct Solar irradiance on horizontal surface
    Id = Io * cos(Z)*0.9662*Tr*To*Tum*Tw*Ta
    #Solar irradiance on horizontal surface from atomspheric scattering
    Ias = Io* cos(Z)*0.79*To*Tw*Tum*Taa
    #Total (global) solar irradiance on a horizonal surface
    It = (Id+Ias)/(1-rg*rs)
    return It, Id, Ias

def bblave(timestamp, place, tilt = 0, azimuth = 180, cloudCover = 0.0):
    #SUN Position
    o = ephem.Observer()
    o.date = timestamp #'2000/12/21 %s:00:00' % (hour - self.tz)
    latitude, longitude = place
    o.lat = radians(latitude)
    o.lon = radians(longitude)
    az = ephem.Sun(o).az
    alt = ephem.Sun(o).alt

    #Irradiance
    day = dayOfYear(timestamp)
    record = {}
    record['utc_datetime'] = timestamp
    Z = pi/2-alt
    aaz = radians(azimuth+180)
    slope = radians(tilt)

    #incidence angle
    theta = arccos(cos(Z)*cos(slope) + \
            sin(slope)*sin(Z)*cos(az - pi - aaz))
    ETR = apparentExtraterrestrialFlux(day)
    #pressure?
    t,Bh,Gh =  bird(theta,1010.0)
    Dh = diffuseHorizontal(alt,Bh,day)

    record['DNI (W/m^2)'] = Bh #8 Direct normal irradiance
    record['GHI (W/m^2)'] = Gh #5 Global horizontal irradiance
    record['DHI (W/m^2)'] = Dh #11 Diffuse horizontal irradiance
    record['ETR (W/m^2)'] = ETR
    return record

if __name__ == "__main__":
    for i in range(-90,180):
        print i,airmass(radians(i)),airMassRatio(radians(i))

    print airMassRatio(radians(30))
    print "perez(0,0,0,0.558505360638,2.81089306448,2.79093661679)"
    print perez(0,0,0,0.558505360638,2.81089306448,2.79093661679)
    #print perez(60,786,60,540,0.558505360638,0.624040125833,1.14157618561)
    #print perez(66,782,66,618,0.558505360638,0.548264494026,1.10572704488)
    print "perez(124,672,124,630,0.558505360638,0.585437141297,1.12283464275)"
    print perez(672,124,630,0.558505360638,0.585437141297,1.12283464275)
    print perez(725,71,575,0.558505360638,0.71816314243,1.19054164885)
    print perez(458,84,457,0.558505360638,0.905073340885,1.30063355891)
    print perez(365,52,283,0.558505360638,1.11854235428,1.44247248195)
    print perez(83,22,75,0.558505360638,1.33812695863,1.59866999006)
    print perez(0,0,0,0.558505360638,1.58526434614,1.7938116797)
    print perez(0,0,0,0.558505360638,1.82430194526,1.98580885248)
    print perez(0,0,0,0.558505360638,2.0648085416,2.18380405772)
    print perez(0,0,0,0.558505360638,2.30391057936,2.38276512577)
    print perez(0,0,0,0.558505360638,2.5366580297,2.57519603892)
    print perez(0,0,0,0.558505360638,2.74856500007,2.7436087649)
    print perez(0,0,0,0.558505360638,2.87979696349,2.83820540821)
    #from scipy.interpolate import interp1d
    #import numpy as np
    import geo
    #thorizon = interp1d(np.array([-180.0,180.0]),np.array([0.0,0.0]))
    timestamp = datetime.datetime.now()
    place = geo.zip_coordinates('17603')
    tilt = 1
    azimuth = 180
    print blave(timestamp,place,tilt,azimuth)
    print bblave(timestamp,place,tilt,azimuth)
    print "Bird",bird(0.478253620172,1000.0)
    azimuth = 90
    print blave(timestamp,place,tilt,azimuth)
    azimuth = 270
    print blave(timestamp,place,tilt,azimuth)
    irradiance = 300.
    utc_datetime = datetime.datetime.utcnow()
    print utc_datetime
    solarAz, solarAlt = ephemSun(place,utc_datetime)
    surfaceTilt = radians(15)
    surfaceAz = radians(180)
    print 'cc', irrGuess(utc_datetime, irradiance, solarAlt, solarAz, surfaceTilt, surfaceAz)
