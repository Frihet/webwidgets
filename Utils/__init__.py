#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <redhog@redhog.org>

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

"""Miscelanous classes and functions needed to implement the rest of
Webwidgets and in implementing new widgets and other objects.
"""

import itertools

debugClassLoading = False

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
        if k in self:
            self.order.remove(k)
        return dict.pop(self, k, *arg)
        
    def popitem(self):
        if len(self) == 0: raise KeyError
        key = self.order[0]
        value = self.pop(key)
        return (key, value)
            
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

class RelativePath(object):
    """RelativePath is a representation of a path that relative one
    point in a tree identifies some other point. It consists of a
    number of steps to walk "upwards" in the tree (like cd .. in
    unix), and then some path to walk downwards from that point.
    Example: 3/foo/bar/fie means go three levels up, then down along
    the branch foo and bar and end up at the node fie.
    """
    def __new__(cls, path, levels = 0, pathAsList = False):
        """Create a new RelativePath instance. There are three formats
        for creating RelativePath instances:

         - 'RelativePath(string path)' The string should be of the
           format 3/foo-bar-fie, which is also the format output from
           L{__str__}.

         - 'RelativePath(list path, int levels = 0)' creates a
           relative path from its two components - a list of strings
           representing the path, and an integer for the levels to
           walk upwards.

         - 'RelativePath(RelativePath path)' copies an existing
           relative path.
        """

        self = super(RelativePath, cls).__new__(cls)
        
        if isinstance(path, basestring):
            if '/' in path:
                levels, path = path.split('/')
                levels = int(levels)
            if path:
                path = path.split('-')
            else:
                path = []
        elif isinstance(path, RelativePath):
            levels = path.levels
            path = path.path
        self.levels = levels
        self.path = list(path)

        if pathAsList and self.levels == 0:
            return self.path
        return self
        
    def __add__(self, child):
        """If a is rooted at c and b is rooted at a, then a + b
        references b and is rooted at c."""
        if not isinstance(child, RelativePath):
            child = type(self)(child)
        if child.levels > len(self.path):
            levels = self.levels + child.levels - len(self.path)
            path = child.path
        else:
            levels = self.levels
            path = self.path
            if child.levels:
                path = path[:-child.levels]
            path = path + child.path
        return type(self)(path, levels)
    def __radd__(self, child):
        return type(self)(child) + self
    def __sub__(self, child):
        """If a and b are both rooted at c, a - b will reference a but
        rooted at b. This _assumes_ a actually resides under b, if
        not, the result is random garbage. Examples:
        3/foo.bar.fie.naja - 3/foo.bar = 0/fie.naja
        3/foo.bar.fie.naja - 3/foo.xxx = 1/bar.fie.naja
        
        And the 'let's just assume things' ones:
        4/xxx.foo.bar.fie.naja - 3/foo.bar = 0/fie.naja
        3/foo.bar.fie.naja - 4/xxx.foo.bar = 0/fie.naja
        
        """
        if not isinstance(child, RelativePath):
            child = type(self)(child)
        selfLevels = self.levels
        selfPath = self.path
        childLevels = child.levels
        childPath = child.path
        
        if selfLevels > childLevels:
            selfPath = selfPath[selfLevels - childLevels:]
        if childLevels > selfLevels:
            childPath = childPath[childLevels - selfLevels:]
        selfLevels = childLevels = min(selfLevels, childLevels)

        # self and child paths are now rooted at the same place
        prefixLen = len(Grimoire.Utils.commonPrefix(selfPath, childPath))
        path = selfPath[prefixLen:]
        levels = len(childPath) - prefixLen
        return type(self)(path, levels)        
    def __rsub__(self, child):
        return type(self)(child) - self
    def __iter__(self):
        if self.levels != 0:
            raise TypeError('Levels non-zero')
        return iter(self.path)
    def __unicode__(self):
        return unicode(self.levels) + '/' + u'-'.join([
            item.replace('\\', '\\\\').replace('-', '\\.')
            for item in self.path])
    def __str__(self):
        return str(unicode(self))

def pathToId(path, acceptNone = False):
    """Converts a widget path to a string suitable for use in a HTML
    id attribute"""
    if path is None and acceptNone:
        return 'none'
    return '-'.join(['root'] + path)

def idToPath(id, acceptNone = False):
    """Convert a string previously created using L{pathToId} back into
    a widget path."""
    if id == 'none' and acceptNone:
        return None
    path = id.split('-')
    assert path[0] == 'root'
    return path[1:]

def isPrefix(prefix, list):
    prefixLen = len(prefix)
    return prefixLen <= len(list) and prefix == list[:prefixLen]

def loadClass(name, using = [], imp = None, globalDict = None, localDict = None, module = None):
    if debugClassLoading: print "loadClass: Importing %s using %s:" % (name, ' '.join(using))

    globalDict = globalDict or getattr(module, '__dict__', globals())
    localDict = localDict or locals()
    file = getattr(module, '__file__', '<Interactive>')
    
    def loadClassAbsolute(name):
        if debugClassLoading: print "loadClass:     Trying %s" % name
        components = name.split('.')
        mod = None
        prefix = list(components)
        while prefix:
            try:
                name = '.'.join(prefix)
                if debugClassLoading: print "loadClass:         Trying %s" % name
                mod = (imp or __import__)(name, globalDict, localDict)
                break
            except ImportError, e:
                if debugClassLoading: print "loadClass:             %s" % str(e)
            del prefix[-1]
        if mod is None:
            raise ImportError("Class does not exist:", name, using, file)
        for component in components[1:]:
            dictComponents = []
            if '-' in component:
                dictComponents = component.split('-')
                component = dictComponents[0]
                del dictComponents[0]
            mod = getattr(mod, component)
            for dictComponent in dictComponents:
                mod = mod[dictComponent]
        return mod

    for pkg in using:
        try:
            return loadClassAbsolute(pkg + '.' + name)
        except (ImportError, AttributeError), e:
            if debugClassLoading: print "loadClass:         %s" % str(e)
    try:
        return loadClassAbsolute(name)
    except (ImportError, AttributeError), e:
        if debugClassLoading: print "loadClass:         %s" % str(e)
        raise ImportError("Class does not exist:", name, using, file)

def subclassDict(superdict, members):
    res = type(superdict)(superdict)
    res.update(members)
    return res

def subclassList(superlist, members):
    return superlist + members

