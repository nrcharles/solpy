# Copyright (C) 2012 Nathan Charles
#
# This program is free software. See terms in LICENSE file.
"""misc helper functions"""

import collections
import functools
import os.path

def factors(n):
    """return factors of an integer
    http://stackoverflow.com/questions/6800193/"""
    return set(reduce(list.__add__, \
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

def find_file(filename, search_path):
    """find a file in search path"""
    for path in search_path:
        if os.path.exists(os.path.join(path, filename)):
            return os.path.abspath(os.path.join(path, filename))
    raise Exception('File %s not found in Path: %s' % \
            (filename, ':'.join(search_path)))

if __name__ == "__main__":
    pass
