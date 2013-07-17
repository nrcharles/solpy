#!/usr/bin/python

#    Copyright 2012 Nathan Charles
#
#
#    This is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This software is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <http://www.gnu.org/licenses/>.

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
    """Perez et al. 1990
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


def irradiation(record, place, horizon, t = 0.0, array_azimuth = 180.0, model = 'lj'):
    latitude, longitude = place

    Gh = int(record['GHI (W/m^2)'])
    Dh = int(record['DHI (W/m^2)'])
    Bh = int(record['DNI (W/m^2)'])

    #theta = incidence angle of the sun
    o = ephem.Observer()
    o.date =  record['utc_datetime']
    o.lat = radians(latitude)
    o.lon = radians(longitude)
    az = ephem.Sun(o).az
    alt = ephem.Sun(o).alt
    slope = radians(t)
    Z = pi/2-alt
    aaz = radians(array_azimuth+180)
    theta = arccos(cos(Z)*cos(slope) + sin(slope)*sin(Z)*cos(az - pi - aaz))

    nA = degrees(az) % 360-180
    if horizon(nA) > degrees(theta):
        Bh = 0
        print "shaded", nA,degrees(theta),horizon(nA)
    #Z = solar Zenith angle
    S = radians(t) #

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
         etr = int(record['ETR (W/m^2)'])
         Dth = perez(Bh, Dh, etr, S, theta, Z)

    #ground diffuse p = ground reflectivity
    p = 0.2
    Rth = Gh*p*(1-cos(S))/2 #?

    if t > 0:
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
    #SUN Position
    o = ephem.Observer()
    o.date = timestamp #'2000/12/21 %s:00:00' % (hour - self.tz)
    latitude, longitude = place
    o.lat = radians(latitude)
    o.lon = radians(longitude)
    az = ephem.Sun(o).az
    alt = ephem.Sun(o).alt

    #Palescu 2013 (3.16)
    a=.25
    b= .5
    cs = 1 - (a*cloudCover + b*cloudCover**2)

    #Irradiance
    Bh = directNormal(timestamp,alt) * cs
    day = dayOfYear(timestamp)
    Dh = diffuseHorizontal(alt,Bh,day)
    record = {}
    record['utc_datetime'] = timestamp
    Z = pi/2-alt
    aaz = radians(azimuth+180)
    slope = radians(tilt)

    #incidence angle
    theta = arccos(cos(Z)*cos(slope) + \
            sin(slope)*sin(Z)*cos(az - pi - aaz))
    #todo: should this theta include tilt of collector?
    Gh = globalHorizontal(Bh,theta,day)
    ETR = apparentExtraterrestrialFlux(day)
    #print Gh, Bh, Dh #, ETR

    record['DNI (W/m^2)'] = Bh #8 Direct normal irradiance
    record['GHI (W/m^2)'] = Gh #5 Global horizontal irradiance
    record['DHI (W/m^2)'] = Dh #11 Diffuse horizontal irradiance
    record['ETR (W/m^2)'] = ETR
    return record

def moduleTemp(irradiance,weatherData):
    #todo: Maybe Sandia Module Temperature instead?
    #TamizhMani 2003
    tAmb = (weatherData['temperature'] - 32) * 5/9
    windSpd = weatherData['windSpeed']
    tModule = .945*tAmb +.028*irradiance - 1.528*windSpd + 4.3
    return tModule

if __name__ == "__main__":
    for i in range(-90,180):
        print i,airmass(radians(i)),airMassRatio(radians(i))

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
    from scipy.interpolate import interp1d
    import numpy as np
    import geo
    thorizon = interp1d(np.array([-180.0,180.0]),np.array([0.0,0.0]))
    timestamp = datetime.datetime.now()
    place = geo.zipToCoordinates('17603')
    tilt = 1
    azimuth = 180
    print blave(timestamp,place,tilt,azimuth)
    azimuth = 90
    print blave(timestamp,place,tilt,azimuth)
    azimuth = 270
    print blave(timestamp,place,tilt,azimuth)
