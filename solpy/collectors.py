#!/usr/bin/env python
# Copyright (C) 2013 Daniel Thomas
#
# This program is free software. See terms in LICENSE file.
#
#   This file contains solar thermal collector classes used by thermal.py
#   Specifications for specific collectors are also here for now.

pi = 3.141

class tube(object):
    '''Double-wall vacuum glass tube collectors.  Two main sizes are defined, the
       58mm OD is most common.'''
    def __init__(self, name='v58mm'):
        self.name  = name
        getattr(self,name)()
    def v58mm(self):                    # Vacuum-insulated 58mm OD tube
        self.D1    = 0.047              # Collector inner tube OD [m]
        self.D2    = 0.058              # Collector outer tube OD [m]
        self.L_ab  = 1.685              # Length of exposed absorber section
        self.L_tot = 1.816              # Overall length [m]
    def v47mm(self):
        pass
    def exposed_area(self):             # Outer surface area, exposed to air [m2]
        return pi*self.D1*self.L_ab
    def volume(self):                   # Interior volume, capacity [m3]
        return pi*(self.D1**2)*self.L_ab

class collector(object):
    '''Currently written for vacuum tube collectors; needs to extended to flat plate collectors'''
    def __init__(self):
        pass
    def manifold_area(self):            # Surface area, excluding tube holes
        c = self.__class__
        return (2*c.w + 2*c.h)*c.L + 2*(c.w*c.h) - c.N_tubes*(pi*((c.t.D2)**2))
    def tube_area(self):                # Total outer surface area of tubes [m2]
        c = self.__class__
        return c.t.exposed_area() * c.N_tubes

class collectorArray(collector):
    def __init__(self,coll,series=1,parallel=1,slope=0,azimuth=0,DFR=False,S=0.0,rho_g=0.2):
        self.c     = coll               # Collector object
        self.N     = series*parallel    # Currently only considering total size
        self.beta  = slope*pi/180       # Collector slope [radians]
        self.gamma = azimuth*pi/180     # Collector azimuth [radians] (0 = due South)
        self.DFR   = DFR                # Diffuse Flat Reflector [T/F] behind tubes
        self.S     = S                  # Distance from DFR to center of tubes [m]
        self.rho_g = rho_g              # Ground reflectance (albedo)
        self.A_gr  = self.c.A_gr*self.N
        self.V     = self.c.V   *self.N
        self.N_tubes=self.c.N_tubes*self.N
        self.a1,a2,a3= 0.0,0.0,0.0      # Collector equation coefficients
        self.b1,b2,b3= 0.0,0.0,0.0        
    def manifold_area(self):
        return self.c.manifold_area()*self.N
    def tube_area(self):
        return self.c.tube_area()*self.N
    def Q_out(self,H,dT):
        '''Daily total collector heat output from ISO 9459-2 collector equation: 
             Q_u = a1*H + a2*(T_i-T_amb) + a3
           Current fit: June 8, 2011 - R^2 = 0.851'''
        return (self.N_tubes/50.0)*(self.a1*H + self.a2*dT + self.a3)
    def Q_tang(self,Qt,dT): # R2 = 0.951
        '''Similar correlation of heat output given solar radiation incident on 
           tubes, as calculated by the method in Tang, 2009.''' 
        return (self.N_tubes/self.c.N_tubes)*(self.b1*Qt+ self.b2*dT + self.b3)

class chuanghui_H50(collector):
    type  = 'H'
    A_gr  = 2*1.87*1.70                 # [m2] Collector gross tube area (6.358 m2, frame = 2*1.93*1.885)
    V     = 0.145                       # [m3] Collector volume
    B     = 0.075                       # [m]  Tube spacing (center to center)
    t     = tube('v58mm')
    N_tubes = 50                        # Number of tubes
    w     = 0.158                       # [m]  Manifold width
    h     = 0.148                       # [m]  Manifold height
    L     = 1.942                       # [m]  Manifold length
