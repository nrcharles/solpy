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
from math import radians #,degrees
from numpy import sin, cos, tan, arccos, arcsin, pi #, arctan2

def azimuth(phi,delta,omega):
    '''solar_azimuth: Solar azimuth angle (from D&B eq. 1.6.6)
       (Angle from South of the projection of beam radiation on the horizontal plane, W = +ve)
    Arguments: 
    omega - Hour angle (radians)
    phi   - Latitude (radians)
    '''
    omega_ew = arccos(tan(delta)/tan(phi))  # E-W hour angle (1.6.6g)
    if (abs(omega) < omega_ew): C_1 =  1
    else:                       C_1 = -1
    if (phi*(phi-delta) >= 0):  C_2 =  1
    else:                       C_2 = -1
    if (omega >= 0):            C_3 =  1
    else:                       C_3 = -1
    #gamma_sp = arctan( sin(omega) / (sin(phi)*cos(omega)-cos(phi)*tan(delta)) ) # Gives error!
    theta_z  = arccos( cos(phi)*cos(delta)*cos(omega) + sin(phi)*sin(delta) )
    gamma_sp = arcsin( sin(omega)*cos(delta)/sin(theta_z) )
    gamma_s  = C_1*C_2*gamma_sp + C_3*((1.0-C_1*C_2)/2.0)*pi
    return gamma_s

def position(latitude, longitude, d, S, plane_azimuth):
    S = radians(S)
    plane_azimuth=radians(plane_azimuth)

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

    solar_azimuth = azimuth(phi,delta,omega)

    #theta = incident angle
    theta = arccos(sin(S)*sin(Z)*cos(solar_azimuth-plane_azimuth) + \
            cos(S)*cos(Z))

    return theta, Z #, zenith
