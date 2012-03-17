#!/usr/bin/python

#    Copyright 2008-2010 Brandon Stafford
#
#    This file is part of Pysolar.
#
#    Pysolar is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    Pysolar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with Pysolar. If not, see <http://www.gnu.org/licenses/>.

"""Calculate different kinds of radiation components via default values

"""
from math import radians
from numpy import sin, cos, tan, arcsin, arccos, arctan, pi
import solar_fun

def adjust(latitude, longitude, d, radiation, tilt = 0, plane_azimuth = pi):
    #Gth = Btd + Dth + Rth
    print latitude, longitude, d
    ghi, dni, dhi = radiation

    Bh = dni #hourly direct solar radiation
    Dh = dhi
    Gh = ghi

    #day of year
    n = d.timetuple().tm_yday #good

    #delta = declination of the sun
    delta = radians(-23.44) * cos((2*pi/365)*(n+10)) # good

    # phi = latitude
    phi = radians(latitude)

    #omega = hour angle
    offset = 0
    omega   = (d.hour+offset)*15*(pi/180)               # Hour angle (15' per hour, a.m. -ve)

    #thetaZ = solar zenith
    thetaZ = arccos(sin(phi)*sin(delta)+cos(phi)*cos(delta)*cos(omega)) #probably good

    #Z = solar zenith angle
    Z = thetaZ
    
    #solar azimuth
    solar_azimuth = solar_fun.solar_azimuth(phi,delta,omega)

    S = radians(tilt) #

    #theta = incident angle
    theta = arccos(sin(S)*sin(Z)*cos(solar_azimuth-plane_azimuth) + \
            cos(S)*cos(Z))

    # p = ground reflectivity
    p = 0.2

    #Badescu 2002
    #rd1 = 3+cos(2*S)/4
    #Tian et al. 2001
    rd = 1 -S/(2 *pi)

    #NREL Manual
    Bth = Bh * cos(theta)

    #sky-diffuse
    Dth = rd*Dh # ?

    #ground diffuse
    Rth = Gh*p*(1-cos(S))/2 #?

    #print Bh, Bth, Z,theta

    Gth = Bth + Dth +Rth
    return Gth
