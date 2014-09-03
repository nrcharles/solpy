#! /usr/bin/env python
# Copyright (C) 2013 Daniel Thomas
#
# This program is free software. See terms in LICENSE file.
#
# This is to be replaced by thermal.py and associated files.
#
# solar_fun - Functions for solar geometry and weather data access
# To do:
#  - integrate weather data code in tmy3
#  - move collector and location data out to separate files
#  - check solar position algorithm against alternatives

import numpy as np
import re
from   numpy import sin, cos, tan, arcsin, arccos, arctan, pi
from   datetime import *
import scipy.interpolate
import solar

class weather_data():
    def __init__(self, placename):
        self.name   = placename
        self.fname  = '/Users/daniel/work/solar/weather_data/EPW_data/BGD_%s/BGD_%s.epw' % \
                      (self.name,self.name)
        self.d      = np.genfromtxt(self.fname,dtype=None,delimiter=',',skiprows=8, 
                      usecols=(1,2,3,4,6,7,8,9,10,11,12,13,14,15,20,21))
        self.d.dtype.names = ('month','day','hour','minute','t_amb','t_dp','rh_amb','press',
            'g_o','g_on','ir_sky','g','g_n','g_d','winddir','windspeed')
        self.units  = ('-','-','-','-','C','C','%','Pa','Wh/m2','Wh/m2','Wh/m2','Wh/m2',
            'Wh/m2','Wh/m2','deg','m/s')
        self.time   = datetime(2010,1,1,1)
        self.step   = timedelta(hours=1)
        self.curr   = 0
    def __getitem__(self,var):
        if isinstance(var,tuple):
            if var[1] == 'next': self.next()
            else:                self.set_time(var[1])
            return self.d[var[0]][self.curr]
        if isinstance(var,str):
            return self.d[var][self.curr]
    def next(self):
        self.curr += 1
        self.time += self.step #= self.time.replace(hour=self.time.hour+1)
    def set_time(self, t):
        self.time = t
        for i in range(len(self.d)):
            if self.d['month'][i]==t.month and self.d['day'][i]==t.day and self.d['hour'][i]==t.hour:
                self.curr = i
    def day_total(self,var):
        #print "self.curr =",self.curr
        if self.time.hour != 1: print 'WARNING: sum not starting from beginning of day.'
        return sum(self.d[var][i] for i in range(self.curr,self.curr+23))
    def day_data(self,n):
        day = np.copy(self.d[0:1440])
#        day.dtype = [('i','int'),('time','float'),('hour','int'),('minute','int'),('t_amb','float'),
#            ('t_dp','float'),('rh_amb','float'),('press','float'),('g_o','float'),('g_on','float'),('ir_sky','float'),
#            ('g','float'),('g_n','float'),('g_d','float'),('winddir','float'),('windspeed','float')]
#            [('i',int),('time',float),('hour',int),('minute',int),('t_amb',float),
#            ('t_dp',float),('rh_amb',float),('press',float),('g_o',float),('g_on',float),('ir_sky',float),
#            ('g',float),('g_n',float),('g_d',float),('winddir',float),('windspeed',float)]
        day.dtype.names = ('i','time','hour','minute','t_amb','t_dp','rh_amb','press',
            'g_o','g_on','ir_sky','g','g_n','g_d','winddir','windspeed')
        #day.dtype = 'int,int,int,int,float,float,float,float,float,float,float,float,float,float,float,float'
        x = 30 + np.array(range(24))*60
        x[0] = 0
        x[-1] = 1439
        x_new = range(24*60)
        i_min,i_max = (n-1)*24, n*24
        for var in self.d.dtype.names:  #range(len(self.d.dtype))
            if   var=='i':      day[var]= [ m + 1    for m in x_new]
            elif var=='minute': day[var]= [ m - (m/60)*60 + 1    for m in x_new]
            elif var=='hour':   day[var]= [ m/60 + 1 for m in x_new]
            else:
                y = self.d[var][i_min:i_max]
                f = scipy.interpolate.interp1d(x,y,kind='linear',bounds_error=False,fill_value=0)
                day[var] = f(x_new)
        day['time'] = (day['hour']-1)*100 + (100/60.0)*day['minute']
        #day['minute']= [ m + 1    for m in x_new]
        #day['hour']  = [ m/60 + 1 for m in x_new]
        return day
        #else: print 'ERROR: day_data() doesn\'t support',n,dt
    def __del__(self):
        pass

class location():
    def __init__(self, name='default',lat=0,lon=0,alt=0):
        self.name  = name
        getattr(self,name)()
        if lat !=0:  self.lat   = lat
        if alt !=0:  self.alt   = alt
        if lon !=0:  
            self.lon   = lon
            self.lon_s = round(lon/15)*15
        self.phi   = self.lat*pi/180.0            # Latitude, in radians
    def default(self):                            # Default values currently for Bonoful
        self.lat   = 24.718931                    # Latitude
        self.lon   = -90.17393                    # Longitude
        self.lon_s = -90.0                        # Standard meridian
        self.alt   = 20.0                         # Altitude
    def akb(self):
        self.lat   = 24.0+(49.0/60)+(10.0/3600)   # Latitude  - Bogra LPK 24.8194
        self.lon   = -(89.0+(20.0/60)+(7.5/3600)) # Longitude - Bogra LPK 89.3354
        self.lon_s = -90.0                        # Standard meridian
        self.alt   = 20.0                         # Altitude  - Bogra LPK [m]
    def bonoful(self):
        self.lat   = 24.718931                    # Latitude  - Bonoful 24.718931
        self.lon   = -90.17393                    # Longitude - Bonoful 90.17393
        self.lon_s = -90.0                        # Standard meridian
        self.alt   = 20.0                         # Altitude  - Bonoful [m]
    def setlon(self, a):
        self.lon = a
    def load(self, filename):
        pass

class collector():
    def __init__(self, name='default'):
        self.name  = name
        getattr(self,name)()
    def default(self):
        self.beta  = 0.0                          # Collector slope
        self.gamma = 0.0                          # Collector azimuth angle (0 = due South)
        self.A_gr  = 0.0                          # Collector gross tube area          (m2)
        self.V     = 0.0                          # Collector volume                   (m3)
        self.B     = 0.0                          # Tube spacing (center to center)    (m)
        self.D1    = 0.0                          # Collector inner tube OD            (m)
        self.D2    = 0.0                          # Collector outer tube OD            (m)
        self.L_ab  = 0.0                          # Length of exposed absorber section (m)
        self.N_tubes = 0
        self.a1,a2,a3= 0.0,0.0,0.0
        self.b1,b2,b3= 0.0,0.0,0.0
    def akb1(self):
        self.beta  = arctan(121.0/152.0)          # Collector slope (38.5 deg.)
        self.gamma = 0.0                          # Collector azimuth angle (0 = due South)
        self.A_gr  = 2*1.87*1.70                  # Collector gross tube area (6.358 m2, frame = 2*1.93*1.885)
        self.V     = 0.145                        # Collector volume (m3)
        self.B     = 0.075                        # Tube spacing (center to center) (mm)
        self.D1    = 0.047                        # Collector inner tube OD (mm)
        self.D2    = 0.058                        # Collector outer tube OD (mm)
        self.L_ab  = 1.685                        # Length of exposed absorber section
        self.N_tubes = 50                         # Number of tubes
        self.a1 = 2.54448 # 2.727782              # Collector equation coefficients
        self.a2 = 1.46415 # 1.264477
        self.a3 = 7.97159 # 7.416783
        self.b1 = 0.92059 # 0.899795              # For eqn. with Tang intercepted solar
        self.b2 =-0.66595 #-0.556184
        self.b3 =-5.30400 #-4.747576

    def Q_out(self,H,dT):
        '''Daily total collector heat output from ISO 9459-2 collector equation: 
             Q_u = a1*H + a2*(T_i-T_amb) + a3
           Current fit: June 8, 2011 - R^2 = 0.851'''
        return (self.N_tubes/50.0)*(self.a1*H + self.a2*dT + self.a3)
    def Q_tang(self,Qt,dT): # R2 = 0.951
        return (self.N_tubes/50.0)*(self.b1*Qt+ self.b2*dT + self.b3)

    def load(self, filename):
        pass

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
#            hr           = (time/100)*100
#            mn           = time - (time/100)*100
#            self.time_s  = (hr + (100/60.0)*(mn+(4*(self.L.lon_s-self.L.lon)+solar_time(self.n))))/2400.0 
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
        #t = self.stime(time)
        #print t
        return np.searchsorted(self.time_s,self.stime(time))
        

def solar_time(n):
    '''solar_time: returns E, for solar/local time offset.'''
    B = ((n-1) * (360.0/365))*(pi/180.0) # See D&B p.11
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
    '''intercepted: Calculations for radiation intercepted by collector, based on Tang, 2009'''
    # NB: Deviations from Tang's notation: lamba > phi; phi > gamma

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

def flowperiod(data,flow_min):
    '''flowperiod: returns the index to the time when the pump started and stopped running'''
    rows = len(data['flow'])
    pump = [0,rows-1]
    for i in range(rows/2,1,-1):  #    print 'data[flow][',i,'] = ',data['flow'][i]
        if (data['flow'][i] < flow_min): 
            pump[0] = i+5
            break
    for i in range(rows/2,rows):
        if (data['flow'][i] < flow_min): 
            pump[1] = i-5
            break
    return pump

def sunrise(data):
    '''sunrise: returns the data row number when pyranometer measures > 1 W/m2 radiation'''
    for i in range(0,len(data['pyr_t'])/2):
        if (data['pyr_t'][i] > 1.0): break
    return i

def ftime(t):
    '''ftime - formats a time int (iii) to 24-hr clock format (ii:ii)'''
    time = "%02i:%02i" % (t/100,t%100)
    return time

def get_errors(filename):
    '''get_errors: reads the errors from the comment line of a .csv data file'''
    fin  = open(filename,'r')
    fin.readline()
    errors = fin.readline() # Errors are listed in second line
    errors = re.sub('# ERRORS:,? ?','',errors)
    errors = re.sub('\n','',errors)
    fin.close()
    return errors

