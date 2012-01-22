#! /usr/bin/env python
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

from __future__ import print_function  # Temp, while using python 2.7
import matplotlib.pyplot as plt
import matplotlib.image as img
import numpy as np
import solar_fun as s
import sys, re, calendar, argparse
from numpy import pi
from datetime import date, datetime, timedelta
from scipy.interpolate import interp1d
version = 0.2
edited  = 'Jan 15, 2011'

class horizon():
    def __init__(self, gamma, alpha, L):
        self.gamma = gamma #- pi    # azimuth angle [deg], with South = 0' for calcs & plotting
        self.alpha = alpha        # altitude angle [deg]
        self.r     = 90 - np.rad2deg(self.alpha)      # r in degrees
        self.L     = L            # location object

def get_args():
    '''Sets up the command line parser to get user arguments'''
    parser = argparse.ArgumentParser(usage='%(prog)s [options] FILE',
            description='Use for analyzing potential solar sites for loss of performance due to shading',
            epilog='Created by Daniel Thomas; Version %s: %s'%(version,edited))
    parser.add_argument('-c','--csv', metavar='FILE',dest='horizon',default=False,
            help='csv input file with horizon altitude data')
    parser.add_argument('-l','--location',metavar='PLACE',dest='location',default=False,
            help='Specify location for horizon data: options: akb, bonoful')
    parser.add_argument('-w','--weather',metavar='PLACE',dest='weather',default=False,
            help='Calculate losses from TMY weather data for PLACE')
    parser.add_argument('-i','--image',metavar='IMAGE',dest='image',default=False,
            help='Plot fisheye panorama image in the background')            
    parser.add_argument('-c2','--csv2',metavar='FILE2',dest='horizon2',default=False,
            help='Compare with a second horizon .csv data set')
    return parser.parse_args()

def load_horizon(fname,loca):
    '''Open SolarShading app's csv output, and returns horizon data arrays'''
    fin   = open(fname,'r')
    h     = np.array(fin.readline().rstrip(',\n').split(','),dtype=float) # header line
    gamma = np.deg2rad(np.array(fin.readline().rstrip(',\n').split(','),dtype=float)) # azimuth angle [deg]
    alpha = np.deg2rad(np.array(fin.readline().rstrip(',\n').split(','),dtype=float)) # altitude angle [deg]
    pname = re.sub('\..+','',fname)
    if   loca:     place = s.location(loca)
    elif len(h)>3: # for android .csv files.
        place = s.location('default',h[0],-h[1],h[2])
        #gamma = gamma - pi
    else:          place = s.location('default')
    fin.close()
    return horizon(gamma,alpha,place) #place, hor

def load_horizon_array(array, loca = None):                                                                                                                     
    if   loca:     place = s.location(loca)
    else:          place = s.location('default')
    #place = s.location('akb')
    gamma = np.deg2rad(np.array([v[0] for v in array]))
    alpha = np.deg2rad(np.array([v[1] for v in array]))
    return horizon(gamma,alpha,place)

def extrap1d(interpolator):
    '''Takes an scipy.interpolate.interp1d object as input.'''
    xs = interpolator.x
    ys = interpolator.y

    def pointwise(x):
        if x < xs[0]:    return ys[0]+(x-xs[0])*(ys[1]-ys[0])/(xs[1]-xs[0])
        elif x > xs[-1]: return ys[-1]+(x-xs[-1])*(ys[-1]-ys[-2])/(xs[-1]-xs[-2])
        else:            return interpolator(x)
    def ufunclike(xs):
        return np.array(map(pointwise, np.array(xs)))
    return ufunclike

def make_invisible(ax):      # Sets axis elements to transparent
    ax.patch.set_alpha(0)
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    return ax

def plot_sunpath(ax,L,C):
    '''Plot sun path for given location, L, and collector, C'''
    ax.set_theta_zero_location('S')
    ax.set_theta_direction('counterclockwise')    # Looking up at the sky, West is right
    ax.set_thetagrids([0,45,90,135,180,225,270,315],['S','SE','E','NE','N','NW','W','SW'])

    n_sum   = date(2011,6,21).timetuple()[-2]     # n for summer solstice
    n_win   = date(2011,12,21).timetuple()[-2]     # n for winter solstice
    n_range = np.rint(np.arange(n_sum,n_win,(n_win-n_sum-0.1)/6.0))
    t_range = np.array(range(600,1801,100)) #[600,700,800,900,1200,1500,1800])
    t_gamma, t_theta = [],[] 

    for n in n_range:      # Plot lines for each month between solstices
        sday = s.solar_day(n,L,C)
        if   n == n_range[0]: summer = sday
        elif n == n_range[-1]: winter = sday
        ax.plot(sday.gamma_s,np.rad2deg(sday.theta_z), 'orange')
        t_gamma.append(sday.gamma_s[sday.i(t_range)])
        t_theta.append(sday.theta_z[sday.i(t_range)])
    f_i = interp1d(winter.gamma_s,np.rad2deg(winter.theta_z),kind='linear',bounds_error=False,fill_value=0)
    f_e = extrap1d(f_i)
    ax.fill_between(summer.gamma_s,np.rad2deg(summer.theta_z),f_e(summer.gamma_s),facecolor='yellow',alpha=0.5)

    t_gamma = np.array(t_gamma)
    t_theta = np.array(t_theta)
    for t in range(len(t_range)): # Plot lines for each hour of the day
        x = np.array([t_gamma[n,t] for n in range(len(n_range))])
        y = np.array([t_theta[n,t] for n in range(len(n_range))])
        ax.plot(x,np.rad2deg(y),'orange')
    ax.set_rmax(90)

def plot_horizon(ax,theta,r,c='k'):
    '''Plot the horizon defined by polar coordinates (theta [rad], r [deg])'''
    r_f   = [100 for i in theta]
    ax.plot(theta,r,c)
    #ax.set_theta_zero_location('S')
    #ax.set_theta_direction('counterclockwise')    # Looking up at the sky, West is right
    #ax.set_thetagrids([0,45,90,135,180,225,270,315],['S','SE','E','NE','N','NW','W','SW'])
    ax.fill_between(theta,r,r_f,facecolor='gray',alpha=0.2)
    ax.set_rmax(90)

def plot_losses(ax,Q_unsh,Q_sh):
    '''Bar chart of monthly radiation, showing shading losses'''
    w  = 0.8                                    # width of bar
    x  = np.array(range(len(Q_unsh)))+(1-w/2)   # x-coord of left edge of bar
    dQ = 100.0 * (Q_unsh - Q_sh)/Q_unsh         # Shading losses [%]
    ax.bar(x,Q_unsh,color='gray')
    ax.bar(x,Q_sh,  color='yellow')
    plt.xlim(0.5,12.5)
    xticklabels = ['%s\n%0.1f%%' % (m,p) for m,p in zip(calendar.month_abbr[1:13],dQ)]
    plt.xticks(range(1,13),xticklabels)
    plt.ylabel('Total monthly radiation (MJ/m2)')

def shading_losses(H,C,data):
    # Calculate solar radiation:
    i_s     = np.argsort(H.gamma)
    horizon = interp1d(H.gamma[i_s],H.alpha[i_s],kind='linear',bounds_error=False,fill_value=0)
    t       = datetime(2010,1,1,1) - timedelta(hours=1)
    days    = range(1,366)       # was range(364)
    one_day = timedelta(days=1)  # time step
    Q_unsh, Q_sh    = [],[]
    Q_m_unsh,Q_m_sh = np.arange(12),np.arange(12)

    data.set_time(t)
    print('\n Calculating daily shading losses:',end=' ')
    for n in days: 
        S  = s.solar_day(n,H.L,C)
        D  = data.day_data(n)
        shade = np.copy(S.gamma_s)
        for i in range(len(S.gamma_s)):  # Evaluate shading as a binary array for whole day
            if (pi/2 - S.theta_z[i]) <= horizon(S.gamma_s[i]): shade[i] = 0.0
            else: shade[i] = 1.0

        # Uses Tang's evacuated tube collector model; could be replaced by simpler
        F_bt, F_dt, Omega, fOmega = s.intercepted(S)
        q_unsh  = C.N_tubes*C.L_ab*C.D1 * (F_bt*D['g_n'] + F_dt*D['g_d'])
        q_sh    = C.N_tubes*C.L_ab*C.D1 * (F_bt*shade*D['g_n'] + F_dt*D['g_d'])
        Q_unsh.append(((np.sum(q_unsh)* 60.0/1000000),t.month)) #date()))  # Day total radation in MJ
        Q_sh.append(  ((np.sum(q_sh)  * 60.0/1000000),t.month))  # Day total radation in MJ
        
        # Print out n as update...
        if t.day == 1: print('\n   %s: %s' % (calendar.month_abbr[t.month],t.day),end=' ')
        else:          print(t.day,end=' ')
        sys.stdout.flush()
        t = t + one_day
        
    # Final report of shading losses:
    print('\n\n Monthly totals for shading losses:')
    for m in range(12):
        Q_m_unsh[m] = sum(q[0] for q in Q_unsh if q[1]==m+1)
        Q_m_sh[m]   = sum(q[0] for q in Q_sh   if q[1]==m+1)
        loss        = 100.0 * (Q_m_unsh[m] - Q_m_sh[m])/Q_m_unsh[m]
        print('   %s: %0.1f MJ - %0.1f MJ = %0.1f%% loss' % 
            (calendar.month_abbr[m+1],Q_m_unsh[m],Q_m_sh[m],loss))

    fig2 = plt.figure(2)
    ax2  = fig2.add_axes([0.1, 0.1, 0.8, 0.8])
    plot_losses(ax2,Q_m_unsh,Q_m_sh)
    plt.draw()

def calc_solarpath(L,gamma,alpha):
# Plot solar path:
    C     = s.collector('akb1')         # Collector object from solarfun.py
    C.beta= 0                           # Calculations for horizontal radiation

    gamma = gamma - pi                  # S = 0 deg for solar calculations & plotting
    r     = 90 - np.rad2deg(alpha)      # r in degrees
    fig = plt.figure(1)
    ax  = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
    plot_sunpath(ax,L,C)
    plot_horizon(ax,gamma,r)
    fig.savefig('test.png')
    return fig


if __name__ == "__main__":
    args  = get_args()
    L     = s.location()                    # Default location for starters
    C     = s.collector('akb1')             # Collector object from solarfun.py
    C.beta= 0                               # Calculations for horizontal radiation
    plt.ion()

    fig  = plt.figure(1)
    if args.image:
        axi = fig.add_axes([0.1, 0.1, 0.8, 0.8], frame_on=False)
        axi = make_invisible(axi)
        pic = plt.imread(args.image)
        axi.imshow(pic)
    ax   = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
    ax.patch.set_alpha(0)
    if args.horizon:    
        H    = load_horizon(args.horizon,args.location) # Horizon data object from .csv file
        plot_horizon(ax,H.gamma,H.r)
        L    = H.L
    plot_sunpath(ax,L,C)        
    if args.horizon2: 
        H2 = load_horizon(args.horizon2,args.location)
        plot_horizon(ax,H2.gamma,H2.r,'b')
    plt.show()

    if args.weather:                         # Calculate losses from weather data
        data  = s.weather_data(args.weather) # Weather data object from EPW data file
        shading_losses(H,C,data)

    i = raw_input('\n [ENTER to quit]')
    print(i)

