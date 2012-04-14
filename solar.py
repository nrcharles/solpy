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
from numpy import sin, cos, tan, arccos, pi, arctan2
import solar_fun
import ephem

def position(latitude, longitude, d, S, plane_azimuth):
    sun = ephem.Sun()
    observer = ephem.Observer()
    observer.lat,observer.lon = latitude,longitude
    observer.date = d #+ datetime.timedelta(hours=5)

    sun.compute(observer)

    #day of year
    n = d.timetuple().tm_yday

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
    #theta = I

    zenith = pi/2 - observer.lon + sun.dec
    #print theta, I

    return theta, Z, zenith

