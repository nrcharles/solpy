#!/usr/bin/env python
import numpy as np
from scipy import interpolate
from datetime import datetime, timedelta


class weather_data():
    def __init__(self, placename):
        self.filename = placename
        try:
            self.csvfile = open(self.filename)
        except:
            self.filename = '/Users/daniel/work/solar/weather_data/EPW_data/BGD_%s/BGD_%s.epw' % \
                      (placename,placename)
            self.csvfile = open(self.filename)
        else:
            print "File not found"
            self.csvfile = None
            sys.exit(1)
        self.header = ''
        for i in range(8): self.header +=  self.csvfile.readline()
        self.d      = self.read_EPW()

        self.time   = datetime(2010,1,1,1)
        self.step   = timedelta(hours=1)
        self.curr   = 0
        
    def read_EPW(self):
        EPW_vars  = ('year','month','day','hour','minute','datasource','t_amb','t_dp',
            'rh_amb','press','g_o','g_on','ir_sky','g','g_n','g_d','ill','ill_n','ill_d',
            'zen_lum','winddir','windspeed','sky_t','sky_o','visibility','ceiling',
            'presweathobs','presweathcodes','precipwtr','aerosoloptdepth','snowdepth',
            'dayslastsnow','albedo','rain','rain_hr')
        out_vars = ['time','t_amb','t_dp','rh_amb','press',
            'g_o','g_on','ir_sky','g','g_n','g_d','winddir','windspeed']  # Add as needed
        out_types = tuple(['object'] + ['float']*12)    
        self.units  = ('-','C','C','%','Pa','Wh/m2','Wh/m2','Wh/m2','Wh/m2',
            'Wh/m2','Wh/m2','deg','m/s')
        
        raw = np.genfromtxt(self.filename,dtype=None,delimiter=',',skiprows=8)  
        raw.dtype.names = EPW_vars
        data = raw.astype(zip(out_vars,out_types))
        data['time'] = [datetime(y,m,d,h-1,30) for y,m,d,h in zip(raw['year'],raw['month'],raw['day'],raw['hour'])]
        print('\n  Read from file %s:  data for %s' % (self.filename, data['time'][0].strftime("%b %d, %Y (%A)") ))
        return data
        
#     def __getitem__(self,var):
#         if isinstance(var,tuple):
#             if var[1] == 'next': self.next()
#             else:                self.set_time(var[1])
#             return self.d[var[0]][self.curr]
#         if isinstance(var,str):
#             return self.d[var][self.curr]
#     def next(self):
#         self.curr += 1
#         self.time += self.step #= self.time.replace(hour=self.time.hour+1)
#     def set_time(self, t):
#         self.time = t
#         for i in range(len(self.d)):
#             if self.d['month'][i]==t.month and self.d['day'][i]==t.day and self.d['hour'][i]==t.hour:
#                 self.curr = i
#     def day_total(self,var):
#         #print "self.curr =",self.curr
#         if self.time.hour != 1: print 'WARNING: sum not starting from beginning of day.'
#         return sum(self.d[var][i] for i in range(self.curr,self.curr+23))
        
    def day_data(self,n):
        '''Returns a numpy array with 1-minute data, interpolated from the EPW hourly data'''
        day = np.copy(self.d[0:1440])       # New array with 24x60 rows
        day['time'][0] = self.d['time'][(n-1)*24].replace(minute=0)
        for i in range(1,1440):
            day['time'][i] = day['time'][i-1] + timedelta(minutes=1) 
        x = 30 + np.array(range(24))*60
        x[0] = 0
        x[-1] = 1439
        x_new = range(24*60)
        i_min,i_max = (n-1)*24, n*24
        for var in day.dtype.names[1:]:  #range(len(self.d.dtype))
            y = self.d[var][i_min:i_max]
            f = interpolate.interp1d(x,y,kind='linear',bounds_error=False,fill_value=0)
            day[var] = f(x_new)
        return day

    def __del__(self):
        pass

if __name__ == "__main__":
    test = weather_data('Bogra')
    day  = test.day_data(60)
    print(day)
