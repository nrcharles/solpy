# Copyright (C) 2012 Nathan Charles
#
# This program is free software. See terms in LICENSE file.

import collections
import functools
import design

def factors(n):
    #http://stackoverflow.com/questions/6800193/
    return set(reduce(list.__add__,
        ([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0)))

class memoized(object):
   '''Decorator. Caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned
   (not reevaluated).
   '''
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      if not isinstance(args, collections.Hashable):
         # uncacheable. a list, for instance.
         # better to not cache than blow up.
         return self.func(*args)
      if args in self.cache:
         return self.cache[args]
      else:
         value = self.func(*args)
         self.cache[args] = value
         return value
   def __repr__(self):
      '''Return the function's docstring.'''
      return self.func.__doc__
   def __get__(self, obj, objtype):
      '''Support instance methods.'''
      return functools.partial(self.__call__, obj)

def format(inverter):
    """'9769.5W : 13S x 3P : ratio 1.22 : 314.0 - 552.0 V'"""
    DC = inverter.array.output(1000)
    ratio = DC/inverter.Paco
    return '%sW : %s : ratio %s : %s - %s V' % (DC, inverter.array, \
            round(ratio,2), round(inverter.minV), round(inverter.maxV))

def fill(inverter, zipcode, acDcRatio = 1.2, mount="Roof", stationClass = 1, Vmax = 600, bipolar= True):
    return [format(i) for i in design.fill(**locals())]

if __name__ == "__main__":
    import inverters
    import modules
    zc='44701'
    zc='27713'
    #zc='44050'
    #zc='23173'
    #m = "Suntech Power : STP245-20-Wd"
    #m = "Mage Solar : Powertec Plus 285-6 PL"
    #m = "Mage Solar : Powertec Plus 245-6 PL *"
    m = "Mage Solar : USA Powertec Plus 250-6 MNCS"
    ms = modules.module(m)
    system = inverters.inverter("Refusol: 20 kW 480V",modules.pvArray(ms,[11]*6))
    print fill(system,zc)
    #system = inverters.inverter("Refusol: 24 kW 480V",modules.pvArray(ms,11,6))
    print fill(system,zc)
    system = inverters.inverter("SMA America: SB7000US-11 277V",modules.pvArray(ms,[14]*2))
    print fill(system,zc,mount="Roof")
    system = inverters.inverter("SMA America: SB8000US-11 277V",modules.pvArray(ms,[14]*2))
    print fill(system,zc)
    #iname = "Shanghai Chint Power Systems: CPS SCE7KTL-O US (240V) 240V"
    iname = "Refusol: 24 kW 480V"
    #system = inverters.inverter(iname,modules.pvArray(m,1,1))
    #system = inverters.inverter(iname,modules.pvArray(modules.module(m),1,1))
    #fill(system,zc,1000)

