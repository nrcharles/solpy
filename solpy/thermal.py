#!/usr/bin/env python
# Copyright (C) 2013 Daniel Thomas
#
# This program is free software. See terms in LICENSE file.

import numpy as np
from   numpy import sin, cos, tan, arcsin, arccos, arctan, pi
import solar
from   collectors import *
from   datetime import datetime, timedelta, date


class location():
    ''' This should be merged with the pv location class...'''
    def __init__(self, name='default',lat=0,lon=0,alt=0):
        self.name  = name
        self.lat   = lat                    # Latitude  [degrees]
        self.alt   = alt                    # Altitude  [m]
        self.lon   = lon                    # Longitude [degrees]
        self.lon_s = round(lon/15)*15       # Standard longitude [degrees]   # UNUSED??
        self.phi   = self.lat*pi/180.0      # Latitude, [radians]

class solar_day():
    '''solar_day uses Duffie & Beckman solar position algorithm for 1 day's solar angles.
       Day constants are floats, variables are numpy arrays.'''
    def __init__(self, n, L, C, time=None):
        # Constants:
        self.n     = n        # Day of year
        self.L     = L        # Location object
        self.C     = C        # Collector object
        self.delta = (23.45*pi/180) * sin(2*pi*(284+self.n)/365) # Declination (1.6.1)
        # Variables: all numpy arrays of length 24h * 60min = 1440 
        if time == None: self.time = np.array([datetime(2000,1,1)+timedelta(days=n-1,minutes=m) for m in range(1440)])
        else:            self.time = time
        self.omega   = np.array([(t.hour+(t.minute/60.0)-12)*15.0*(pi/180.0) for t in self.time])  # Hour angle (15' per hour, a.m. -ve)
        self.gamma_s = np.array([solar.azimuth(self.L.phi,self.delta,m) for m in self.omega]) # Solar azimuth
        self.theta_z = arccos( cos(self.L.phi)*cos(self.delta)*cos(self.omega) +
                       sin(self.L.phi)*sin(self.delta) )              # Zenith angle (1.6.5)
        self.theta   = arccos( cos(self.theta_z)*cos(self.C.beta) +   # Angle of incidence on collector (1.6.3)
                       sin(self.theta_z)*sin(self.C.beta)*cos(self.gamma_s-self.C.gamma) )
        self.R_b     = cos(np.clip(self.theta,0,pi/2))/cos(np.clip(self.theta_z,0,1.55)) # (1.8.1) Ratio of radiation on sloped/horizontal surface

        G_sc  = 1367.0                             # Solar constant [W/m2] (p.6)
        G_on  = G_sc * (1+0.033*cos(2.0*pi*n/365)) # Extraterrestial radiation, normal plane [W/m2] (1.4.1)
        self.G_o   = G_on * cos(self.theta_z)           # Extraterrestial radiation, horizontal [W/m2] (1.10.1)
        

    def clear_sky(self):
        return np.array([clear_sky(self.n,t,self.L.alt) for t in self.theta_z])
        
    def G_T_HDKR(self,G,G_d):
        '''Calculates total radiation on a tilted plane, using the HDKR model'''
        G_b  = np.clip(G - G_d,0,1500)
        A_i  = G_b/self.G_o                             # Anisotropy index
        np.seterr(divide='ignore',invalid='ignore')     # Avoiding errors in divide by inf. below
        f    = np.sqrt(np.nan_to_num(G_b/G))            # Horizon brightening factor
        np.seterr(divide='warn',invalid='warn')
        G_T  = ((G_b + G_d*A_i)*self.R_b + \
                G_d * (1-A_i) * ((1+cos(self.C.beta))/2) * (1 + f*sin(self.C.beta/2)**3) + \
                G*self.C.rho_g*((1-cos(self.C.beta))/2)) # Ground reflectance
        return G_T
                                       
    def R_b(self):
        pass
   
def day_of_year(dtime):
    '''returns n, the day of year, for a given python datetime object'''
    if isinstance(dtime,int):
        ndate = datetime.now().replace(month=1,day=1)+timedelta(days=dtime-1)
        return ndate.date()
    elif isinstance(dtime,datetime) or isinstance(dtime,date):
        n = (dtime - dtime.replace(month=1,day=1)).days + 1
        return n
    else: 
        print('ERROR: day_of_year takes an int (n) or datetime.datetime object')
        return ' '
     
def solar_time(n):
    '''solar_time: returns E, for solar/local time offset.'''
    B = ((n-1) * (360.0/365))*(pi/180.0)    # See D&B p.11
    E = 229.2 * (0.000075 + 0.001868*cos(B) - 0.032077*sin(B) - 0.014615*cos(2*B) - 0.04089*sin(2*B))
    return E    

def clear_sky(n, theta_z, alt):
    '''clear_sky: returns an estimate of the clear sky radiation for a given day, time.
       output: G_c = [G_ct, G_cb, G_cd] '''
    A   = alt/1000.0                           # Altitude [km]
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



def Intercepted_Tang(S,I_nb,I_nd):
    ''' intercepted: Calculations for radiation intercepted by glass tube collector, 
        based on Tang, 2009
        NB: Deviations from Tang's notation (to confirm with D&B used elsewhere): 
            lamba -> phi; phi -> gamma'''
    # Collector Constants
    D1 = S.C.c.t.D1
    D2 = S.C.c.t.D2
    B  = S.C.c.B
    s  = S.C.S

    # Solar position vectors
    n_x  =  cos(S.delta)*cos(S.L.phi)*cos(S.omega) + sin(S.delta)*sin(S.L.phi)
    n_y  = -cos(S.delta)*sin(S.omega)
    n_z  = -cos(S.delta)*sin(S.L.phi)*cos(S.omega) + sin(S.delta)*cos(S.L.phi)
    np_x = n_x*cos(S.C.beta) - (n_y*sin(S.C.gamma)+n_z*cos(S.C.gamma))*sin(S.C.beta)
    np_y = n_y*cos(S.C.gamma) - n_z*sin(S.C.gamma)
    np_z = n_x*sin(S.C.beta) + (n_y*sin(S.C.gamma)+n_z*cos(S.C.gamma))*cos(S.C.beta)

    # Beam radiation, directly intercepted
    Omega = {'T': arctan(abs(np_y/np_x)),
             'H': arctan(abs(np_z/np_x)) }[S.C.c.type]
    Omega_0 = arccos((D1+D2)/(2*B))
    Omega_1 = arccos((D1-D2)/(2*B))
    # f(Omega): added np_x condition to avoid after-sunset values, np.clip to cut -ve values
    fOmega  = np.zeros_like(np_x)
    for i in range(len(Omega)):
        if   np_x[i]  <= 0.0:      fOmega[i] = 0.0
        elif Omega[i] <= Omega_0:  fOmega[i] = 1.0
        elif Omega[i] >= Omega_1:  fOmega[i] = 0.0
        else: fOmega[i] = np.clip((B/D1)*cos(Omega[i]) + 0.5*(1-(D2/D1)),0,2)
    cosOt = { 'T': np.sqrt(np_x*np_x + np_y*np_y),
              'H': np.sqrt(np_x*np_x + np_z*np_z) }[S.C.c.type]
    I_bt = D1 * cosOt * fOmega * I_nb
    
    # Diffuse radiation, directly intercepted
    if   S.C.c.type == 'T':
        piF  = Omega_0 + 0.5*(1-(D2/D1))*(Omega_1-Omega_0) + (B/D1)*(sin(Omega_1)-sin(Omega_0))
        I_dB = 0.5 * (1+cos(S.C.beta)) * I_nd
    elif S.C.c.type == 'H':
        if ((pi/2)-S.C.beta) >= Omega_0:  piF = Omega_0 + (1-(D2/D1))*((pi/2) - S.C.beta + Omega_1 - 2*Omega_0)/4 + \
                    (B/(2*D1))*(sin(Omega_1)+cos(S.C.beta)-2*sin(Omega_0))
        else: piF = 0.5*(Omega_0+(pi/2)-S.C.beta) + (1-(D2/D1))*(Omega_1 - Omega_0)/4 + \
                    (B/(2*D1))*(sin(Omega_1) - sin(Omega_0))
        I_dB = I_nd
    I_dt = D1 * piF * I_dB

    # Beam radiation, reflected from DFR
    W = B - (D2/cos(Omega))     # Eq. 18
    C = 2*s/D2
    dx = s * tan(Omega) - D2/(2*cos(Omega))     # (Eq. 23)
    

#     # Debugging plot:
#     import matplotlib.pyplot as plt
#     import matplotlib.dates  as mdates
#     fig = plt.figure(1, figsize=(14,8))
#     ax  = fig.add_axes([0.1, 0.1, 0.8, 0.8])
#     t   = S.time[1]
#     ax.plot(S.time,I_bt,'red',   label=r'$I_{bt}$',linewidth=2)
#     ax.plot(S.time,I_dt,'orange',label=r'$I_{dt}$',linewidth=2)
#     ax.plot(S.time,np_x,'blue', label=r'$n^{\prime}_x$',linewidth=1)
#     ax.plot(S.time,fOmega,'green', label=r'$f(\Omega)$',linewidth=2)
#     ax.plot(S.time,Omega,'black', label=r'$\Omega$',linewidth=1)
#     ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M')) 
#     ax.set_xlim((t.replace(hour=6,minute=0),t.replace(hour=20,minute=0)))
#     ax.legend()
#     ax.set_ylim((-1,5))
#     plt.show()

    # Total intercepted radiation for entire collector array
    I_total = S.C.N_tubes*S.C.c.t.L_ab * (I_bt + I_dt)
    return I_total

def F(y):
    C = 2*s/D2
    dx = s * tan(Omega) - D2/(2*cos(Omega))     # (Eq. 23)
    A1 = (2*(dx - y))/D2
    A2 = (2*(B + dx - y))/D2
    theta1 = arctan((A1*C + (A1**2 * C**2 - (A1**2 - 1)*(C**2 - 1))**0.5)/(C**2 - 1))
    theta2 = arctan((-A2*C +(A2**2 * C**2 - (1 - A2**2)*(1 - C**2))**0.5)/(1 - C**2))
