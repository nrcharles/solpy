#!/usr/bin/env python
# Copyright (C) 2012 Daniel Thomas
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
from   numpy import sin, cos, tan, arcsin, arccos, arctan, pi
import solar
from   collectors import *


class location():
    ''' This should be merged with the pv location class...'''
    def __init__(self, name='default',lat=0,lon=0,alt=0):
        self.name  = name
        self.lat   = lat
        self.alt   = alt
        self.lon   = lon
        self.lon_s = round(lon/15)*15
        self.phi   = self.lat*pi/180.0            # Latitude, in radians

class solar_day():
    '''solar_day uses Duffie & Beckman solar position algorithm for 1 day's solar angles.
       Day constants are floats, variables are numpy arrays.'''
    def __init__(self, n, L, C, time=[]):
        # Constants:
        self.n     = n        # Day of year
        self.L     = L        # Location object
        self.C     = C        # Collector object
        self.delta = (23.45*pi/180) * sin(2*pi*(284+self.n)/365) # Declination (1.6.1)
        # Variables: all numpy arrays of length 24*60 = 1440 
        if len(time) > 1:     # Set up the time array: time_s is normalized (0 - 1)
            self.time_s = self.stime(time)
        else:
            self.time_s  = (np.arange(1440)+4*(self.L.lon_s-self.L.lon)+solar_time(self.n))/1440.0 
        self.omega   = (self.time_s-0.5)*24*15*(pi/180)               # Hour angle (15' per hour, a.m. -ve)
        self.gamma_s = np.array([solar.azimuth(self.L.phi,self.delta,m) for m in self.omega]) # Solar azimuth
        self.theta_z = arccos( cos(self.L.phi)*cos(self.delta)*cos(self.omega) +
                       sin(self.L.phi)*sin(self.delta) )              # Zenith angle (1.6.5)
        self.theta   = arccos( cos(self.theta_z)*cos(self.C.beta) +   # Angle of incidence on collector (1.6.3)
                       sin(self.theta_z)*sin(self.C.beta)*cos(self.gamma_s-self.C.gamma) ) 
    def stime(self,time):
        '''Converts Campbell Sci 0-2400 time format to a 0-1 normalized array'''
        hr  = (time/100)*100
        mn  = time - (time/100)*100
        return (hr + (100/60.0)*(mn+(4*(self.L.lon_s-self.L.lon)+solar_time(self.n))))/2400.0 
    def i(self, time):
        '''indirect time reference: returns array location for given solar time.'''
        return np.searchsorted(self.time_s,self.stime(time))
        
def solar_time(n):
    '''solar_time: returns E, for solar/local time offset.'''
    B = ((n-1) * (360.0/365))*(pi/180.0)    # See D&B p.11
    E = 229.2 * (0.000075 + 0.001868*cos(B) - 0.032077*sin(B) - 0.014615*cos(2*B) - 0.04089*sin(2*B))
    return E    

def clear_sky(n, theta_z, alt):
    '''clear_sky: returns an estimate of the clear sky radiation for a given day, time.
    output: G_c = [G_ct, G_cb, G_cd] '''
    A   = alt/1000.0                           # Altitude in km
    r_0 = 0.95                                 # r_0 - r_k are correction factors from Table 2.8.1 (p.73)
    r_1 = 0.98                                 # (for tropical climate; 
    r_k = 1.02 
    a_0 = r_0 * (0.4237 - 0.00821*((6.0-A)**2))
    a_1 = r_1 * (0.5055 + 0.00595*((6.5-A)**2))
    k   = r_k * (0.2711 + 0.01858*((2.5-A)**2))
    tau_b = a_0 + a_1*np.exp(-k/cos(theta_z))  # Transmission coeff. for beam (2.8.1), from Hottel
    tau_d = 0.271 - 0.294*tau_b                # Transmission coeff. for diffuse (2.8.5), Liu & Jordan
    G_sc  = 1367.0                             # Solar constant [W/m2] (p.6)
    G_on  = G_sc * (1+0.033*cos(2.0*pi*n/365)) # Extraterrestial radiation, normal plane [W/m2] (1.4.1)
    G_o   = G_on * cos(theta_z)                # Extraterrestial radiation, horizontal [W/m2] (1.10.1)
    G_c    = [0.0, 0.0, 0.0]
    if (G_o > 0.0): G_c = [(tau_b+tau_d)*G_o, tau_b*G_o, tau_d*G_o]
    return G_c

def intercepted(S):
    ''' intercepted: Calculations for radiation intercepted by glass tube collector, 
        based on Tang, 2009
        NB: Deviations from Tang's notation: lamba > phi; phi > gamma'''

    # Solar position vectors
    n_x  =  cos(S.delta)*cos(S.L.phi)*cos(S.omega) + sin(S.delta)*sin(S.L.phi)
    n_y  = -cos(S.delta)*sin(S.omega)
    n_z  = -cos(S.delta)*sin(S.L.phi)*cos(S.omega) + sin(S.delta)*cos(S.L.phi)
    np_x = n_x*cos(S.C.beta) - (n_y*sin(S.C.gamma)+n_z*cos(S.C.gamma))*sin(S.C.beta)
    np_y = n_y*cos(S.C.gamma) - n_z*sin(S.C.gamma)
    np_z = n_x*sin(S.C.beta) + (n_y*sin(S.C.gamma)+n_z*cos(S.C.gamma))*cos(S.C.beta)
    io   = np.zeros_like(np_x)
    for i in range(0,len(np_x)-1):
       if np_x[i] > 0: io[i] = 1.0

    # Beam radiation, directly intercepted
    Omega   = arctan(abs(np_z/np_x))
    Omega_0 = arccos((S.C.D1+S.C.D2)/(2*S.C.B))
    Omega_1 = arccos((S.C.D1-S.C.D2)/(2*S.C.B))
    fOmega = []
    #if   Omega <= Omega_0: fOmega = 1.0
    #elif Omega >= Omega_1: fOmega = 0.0
    #else: fOmega = (S.C.B/S.C.D1)*cos(Omega) + 0.5*(1-(S.C.D2/S.C.D1))
    for Om in Omega:
        if   Om <= Omega_0: fOmega.append(1.0)
        elif Om >= Omega_1: fOmega.append(0.0)
        else: fOmega.append((S.C.B/S.C.D1)*cos(Om) + 0.5*(1-(S.C.D2/S.C.D1)))
    #I_bt = S.C.D1 * I_b * np.sqrt(np_x*np_x + np_z*np_z) * fOmega
    fOmega *= io
    F_bt = np.sqrt(np_x*np_x + np_z*np_z) * fOmega

    # Diffuse radiation, directly intercepted
    if ((pi/2)-S.C.beta) >= Omega_0:
        piF = Omega_0 + (1-(S.C.D2/S.C.D1))*((pi/2) - S.C.beta + Omega_1 - 2*Omega_0)/4 + \
              (S.C.B/(2*S.C.D1))*(sin(Omega_1)+cos(S.C.beta)-2*sin(Omega_0))
    else:
        piF = 0.5*(Omega_0+(pi/2)-S.C.beta) + (1-(S.C.D2/S.C.D1))*(Omega_1 - Omega_0)/4 + \
              (S.C.B/(2*S.C.D1))*(sin(Omega_1) - sin(Omega_0))
    #I_dt = S.C.D1 * I_d * piF   # NB: for H-type, where I_d,S.C.beta = I_d
    F_dt = piF
    return F_bt, F_dt, Omega, fOmega
