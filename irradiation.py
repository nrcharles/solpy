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
#    with Pysolar. If not, see <http://www.gnu.org/licenses/>.

"""Calculate different kinds of radiation components via default values

"""
from math import radians,degrees
from numpy import sin, cos, tan, arcsin, arccos, arctan, pi, arctan2
import solar_fun
import ephem
import datetime

def tilt(latitude, longitude, d, radiation, tilt = 0, plane_azimuth = pi):
    sun = ephem.Sun()
    observer = ephem.Observer()
    observer.lat,observer.lon = latitude,longitude
    observer.date = d #+ datetime.timedelta(hours=5)

    sun.compute(observer)

    #Gth = Btd + Dth + Rth
    ghi, dni, dhi = radiation

    Bh = dni #hourly direct solar radiation
    Dh = dhi
    Gh = ghi

    #day of year
    n = d.timetuple().tm_yday
    S = radians(tilt) #

    #delta = declination of the sun
    delta = radians(-23.44) * cos((2*pi/365)*(n+10)) 

    # phi = latitude
    phi = radians(latitude)

    #omega = hour angle
    #crude hack
    offset = 12
    omega   = (d.hour+offset)*15*(pi/180) 

    #thetaZ = solar zenith
    thetaZ = arccos(sin(phi)*sin(delta)+cos(phi)*cos(delta)*cos(omega)) 
    Z = thetaZ

    solar_azimuth = solar_fun.solar_azimuth(phi,delta,omega)

    #theta = incident angle
    theta = arccos(sin(S)*sin(Z)*cos(solar_azimuth-plane_azimuth) + \
            cos(S)*cos(Z))

    #begin testing theta
    #ha1 = sun.az - pi
    ha = observer.sidereal_time() - sun.ra
    #print d, ha
    delta = sun.dec
    #topocentric astronmers azimuth angle
    azi = arctan2(sin(ha),cos(ha)*sin(phi)-tan(delta)*cos(phi))

    #topocentric zenith
    L = arccos(sin(phi)*sin(delta)+cos(phi)*cos(delta)*cos(ha))

    #incidence angle
    I = arccos(cos(L)*cos(S)+sin(S)*sin(L)*cos(azi))

    # p = ground reflectivity
    p = 0.2

    #Badescu 2002
    #rd1 = 3+cos(2*S)/4
    #Tian et al. 2001
    #rd = 1 -S/(2 *pi)
    #Liu and Jordan
    rd = (1+cos(S))/2

    #NREL Manual
    Bth = Bh * cos(theta)
    #Bth = (Bh * cos(I))

    #sky-diffuse
    Dth = rd*Dh # ?

    #ground diffuse
    Rth = Gh*p*(1-cos(S))/2 #?

    Gth = Bth + Dth +Rth
    return Gth


def perez(diffuse,beta,zenith):
    a = max(0,cos(beta))
    b = max(0.087,cos(zenith))

    F1= 0
    F2= 0

    return diffuse*(.5*(1-F1)*(1+cos(beta)) + F1*a/b+F2*sin(beta))
