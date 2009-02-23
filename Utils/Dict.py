# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import itertools, types, weakref

def subclass_dict(superdict, members):
    res = type(superdict)(superdict)
    res.update(members)
    return res

class ImmutableDict(dict):
    '''A hashable dict.'''

    def __init__(self,*args,**kwds):
        dict.__init__(self,*args,**kwds)
    def __setitem__(self,key,value):
        raise NotImplementedError, "dict is immutable"
    def __delitem__(self,key):
        raise NotImplementedError, "dict is immutable"
    def clear(self):
        raise NotImplementedError, "dict is immutable"
    def setdefault(self,k,default=None):
        raise NotImplementedError, "dict is immutable"
    def popitem(self):
        raise NotImplementedError, "dict is immutable"
    def update(self,other):
        raise NotImplementedError, "dict is immutable"
    def __hash__(self):
        return hash(tuple(self.iteritems()))

class OrderedDict(dict):
    def __init__(self, content = {}, **kw):
        dict.__init__(self)
        self.clear()
        self.update(content)
        self.update(kw)

    def __iter__(self):
        return self.order.__iter__()

    def __delitem__(self, key):
        self.order.remove(key)
        dict.__delitem__(self, key)
        
    def __setitem__(self, key, value):
        if key not in self:
            self.order.append(key)
        dict.__setitem__(self, key, value)

    def __add__(self, other):
        return type(self)(itertools.chain(self.iteritems(), other.iteritems()))

    def __repr__(self):
        return '{%s}' % ', '.join(["%s:%s" % (repr(name), repr(value))
                                   for (name, value) in self.iteritems()])

    def __str__(self):
        return repr(self)
        
    def clear(self):
        dict.clear(self)
        self.order = []

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        return itertools.imap(lambda name: (name, self[name]), self.iterkeys())

    def iterkeys(self):
        return iter(self.order)

    def itervalues(self):
        return itertools.imap(lambda (name, value): value, self.iteritems())

    def keys(self):
        return self.order

    def pop(self, k, *arg):
        try:
            return self[k]
        finally:
            del res[k]
        
    def popitem(self):
        for key in self.order:
            value = self.pop(key)
            return (key, value)
        raise KeyError
            
    def setdefault(self, k, d = None):
        if k not in self:
            self[k] = d
        return self[k]

    def update(self, other):
        if hasattr(other, 'iteritems'):
            other = other.iteritems()
        for (name, value) in other:
            self[name] = value

    def values(self):
        return list(self.itervalues())
    
    def sort(self, *arg, **kw):
        self.order.sort(*arg, **kw)

class WeakValueOrderedDict(OrderedDict):
    def _unref(self, key):
        del self[key]
               
    def __getitem__(self, key):
        res = dict.__getitem__(self, key)()
        if res is None: raise KeyError(self, key)
        return res
    
    def __setitem__(self, key, value):
        if key not in self:
            self.order.append(key)
        try:
            refvalue = weakref.ref(value, lambda value: self._unref(key))
        except TypeError:
            # Just pretend, for a second, that Python is sane and we
            # can weakref anything. Ssshhh, you didn't see this :P
            refvalue = lambda : value
        dict.__setitem__(self, key, refvalue)

    def iteritems(self):
        for key in self.iterkeys():
            try:
                yield (key, self[key])
            except KeyError:
                pass    

class LazyDict(dict):
    def __init__(self, dict_of_functions):
        self.dict_of_functions = dict_of_functions

    def __contains__(self, item):
        return item in self.dict_of_functions

    def __iter__(self):
        return self.dict_of_functions.__iter__()

    def __delitem__(self, key):
        del self.dict_of_functions[key]
        
    def __setitem__(self, key, value):
        self.dict_of_functions[key] = value

    def __getitem__(self, key):
        res = self.dict_of_functions[key]
        if isinstance(res, types.FunctionType):
            res = self.dict_of_functions[key] = res()
        return res
        
    def __repr__(self):
        return '{%s}' % ', '.join(["%s:%s" % (repr(name), repr(value))
                                   for (name, value) in self.iteritems()])

    def __str__(self):
        return repr(self)
        
    def clear(self):
        self.dict_of_functions.clear()

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        for key in self.iterkeys():
            try:
                yield (key, self[key])
            except KeyError:
                pass

    def iterkeys(self):
        return self.dict_of_functions.iterkeys()

    def itervalues(self):
        return itertools.imap(lambda (name, value): value, self.iteritems())

    def keys(self):
        return self.dict_of_functions.keys()

    def pop(self, k, *arg):
        try:
            return self[k]
        finally:
            del res[k]
        
    def popitem(self):
        for key in self.order:
            value = self.pop(key)
            return (key, value)
        raise KeyError
            
    def setdefault(self, k, d = None):
        if k not in self:
            self[k] = d
        return self[k]

    def update(self, other):
        if hasattr(other, 'dict_of_functions'):
            self.dict_of_functions.update(other.dict_of_functions)
        else:
            if hasattr(other, 'iteritems'):
                other = other.iteritems()
            for (name, value) in other:
                self[name] = value

    def values(self):
        return list(self.itervalues())
    
    def sort(self, *arg, **kw):
        self.dict_of_functions.sort(*arg, **kw)
