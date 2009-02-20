#! /bin/env python
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

"""Miscelanous ww_classes and functions needed to implement the rest of
Webwidgets and in implementing new widgets and other objects.
"""

import itertools, types, weakref, sys, os, os.path, traceback, syslog, datetime
import Cache, Performance

debug_class_loading = False
debug_class_load_caching = False

def convert_to_str_any_way_possible(obj):
    try:
        if isinstance(obj, types.StringType):
            return unicode(obj, errors="replace")
        return unicode(obj)
    except Exception, e:
        try:
            return str(obj)
        except Exception, e2:
            return '{' + convert_type_to_str_any_way_possible(obj) + ' @ ' + str(id(obj)) + ': ' +  obj_info(e) + '}'

def convert_type_to_str_any_way_possible(obj):
    try:
        t = type(obj)
    except Exception, e:
        return '{' + obj_info(e) + '}'
    return obj_info(t)

def obj_info(obj):
    res = []
    t = type(obj)
    res += [convert_to_str_any_way_possible(obj)]
    if t == types.InstanceType:
        klass = type(obj)
        res += [obj_info(klass)]
    elif t == types.ClassType:
        klass = obj.__class__
        res += [obj_info(klass)]
    res += [convert_to_str_any_way_possible(t)]
    return '[' + ' '.join(res) + ']'

def common_prefix(l1, l2):
    for index in xrange(0, min(len(l1), len(l2))):
        if l1[index] != l2[index]:
            return l1[:index]
    return l1[:index + 1]

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


#### fixme ####
# name = "Generalize WidgetPath to some kind of WidgetSelector"
# description = """Generalize WidgetPath to some kind of
# WidgetSelector set of classes that can select widgets based on
# several different criterias, esp. doing what
# get_widgets_by_attribute is doing."""
#### end ####

class WidgetPath(object):
    """WidgetPath is a representation of a path that identifies some
    point in the widget tree (that is, some widget in your
    application).

    Relative paths consists of a number of steps (the level) to walk
    'upwards' in the tree (like cd .. in unix), and then some path to
    walk downwards from that point. Example: 3:foo-bar-fie means go
    three levels up, then down along the branch foo and bar and end up
    at the node fie.

    Absolute paths consists of just the path to walk downward from the
    root. Example: root:foo-bar-fie means to go down along the branch
    foo and bar and end up at the node fie.
    """
    def __new__(cls, path, levels = 0, path_as_list = False):
        """Create a new WidgetPath instance. There are three formats
        for creating WidgetPath instances:

         - 'WidgetPath(string path)' The string should be of the
           format 3:foo-bar-fie, which is also the format output from
           L{__str__}.

         - 'WidgetPath(list path, int levels = 0)' creates a
           relative path from its two components - a list of strings
           representing the path, and an integer for the levels to
           walk upwards or None for an absolute path.

         - 'WidgetPath(WidgetPath path)' copies an existing path.
        """

        if path is None:
            return None

        self = super(WidgetPath, cls).__new__(cls)
        
        if isinstance(path, basestring):
            if ':' in path:
                levels, path = path.split(':')
                if levels == 'root':
                    levels = None
                else:
                    levels = int(levels)
            if path:
                path = path.split('-')
            else:
                path = []
        elif isinstance(path, WidgetPath):
            levels = path.levels
            path = path.path
        self.levels = levels
        self.path = list(path)

        # Both relative and absolute paths can be represented as
        # simple lists... This ambiguity is intentional.
        if path_as_list and not self.levels:
            return self.path
        return self
        
    def __add__(self, child):
        """If a is rooted at c and b is rooted at a, then a + b
        references b and is rooted at c."""
        if not isinstance(child, WidgetPath):
            child = type(self)(child)
        if child.levels is None:
            raise ValueError("Can not add an absolute path to a relative path: %s + %s" % (self, child))
        if child.levels > len(self.path):
            if self.levels is None:
                raise ValueError("Can not add a relative pointing above the root of an absolute path: %s + %s" % (self, child))
            levels = self.levels + child.levels - len(self.path)
            path = child.path
        else:
            levels = self.levels
            path = self.path
            if child.levels:
                path = path[:-child.levels]
            path = path + child.path
        return type(self)(path, levels)
    
    def __sub__(self, child):
        """If a and b are both rooted at c, a - b will reference a but
        rooted at b. This _assumes_ a actually resides under b, if
        not, the result is: garbage in - garbage out :P. Examples:
        '3:foo-bar-fie-naja' - '3:foo-bar' = '0:fie-naja'
        '3:foo-bar-fie-naja' - '3:foo-xxx' = '1:bar-fie-naja'
        
        And the 'let's just assume things' ones:
        '4:xxx-foo-bar-fie-naja' - '3:foo-bar' = '0:fie-naja'
        '3:foo-bar-fie-naja' - '4:xxx-foo-bar' = '0:fie-naja'
        
        """
        if not isinstance(child, WidgetPath):
            child = type(self)(child)

        self_path = self.path
        child_path = child.path

        if (self.levels is None) != (child.levels is None):
            raise ValueError("Can not subtract relative path from absolute or absolute from relative: %s - %s" % (self, child))

        if self.levels is not None:
            if self.levels > child.levels:
                self_path = self_path[self.levels - child.levels:]
            elif self.levels < child.levels:
                child_path = child_path[child.levels - self.levels:]

        # self and child paths are now rooted at the same place
        prefix_len = len(common_prefix(self_path, child_path))
        path = self_path[prefix_len:]
        levels = len(child_path) - prefix_len
        return type(self)(path, levels)
    
    def __radd__(self, child):
        return type(self)(child) + self
    def __rsub__(self, child):
        return type(self)(child) - self

    def __iter__(self):
        if self.levels:
            raise TypeError('Unable to iterate over a relative path with non-zero levels')
        return iter(self.path)

    def __unicode__(self):
        levels = 'root'
        if self.levels is not None:
            levels = self.levels
        return "%s:%s" % (levels, u'-'.join([
            item.replace('\\', '\\\\').replace('-', '\\.')
            for item in self.path]))

    def __str__(self):
        return str(unicode(self))

def path_to_id(path):
    """Converts a widget path to a string suitable for use in a HTML
    id attribute"""
    return unicode(WidgetPath(path, None))

def id_to_path(id):
    """Convert a string previously created using L{path_to_id} back into
    a widget path."""
    return WidgetPath(id, path_as_list=True)

def classes_remove_bases(classes, cls):
    base_classes = set()
    for base in cls.__bases__:
        base_classes.update(base.ww_classes)
    return [cls for cls in classes if cls not in base_classes]

def classes_to_css_classes(classes, postfix = []):
    if postfix:
        postfix = ['', '_'] + postfix
    cls_set = set(classes)
    if len(cls_set) != len(classes):
        res = []
        for cls in reversed(classes):
            if cls in cls_set:
                res.append(cls)
                cls_set.remove(cls)
        classes = reversed(res)
    return ' '.join([c.replace('.', '-') + '-'.join(postfix)
                     for c in classes])

def is_prefix(prefix, list):
    prefix_len = len(prefix)
    return prefix_len <= len(list) and prefix == list[:prefix_len]

def get_existing_class_prefix(name, using = []):
    def get_existing_class_prefix(name):
        path = name.split('.')
        pos = 0
        if pos < len(path) and path[pos] in sys.modules:
            obj = sys.modules[path[pos]]
            pos += 1
            while pos < len(path) and hasattr(obj, path[pos]):
                obj = getattr(obj, path[pos])
                pos += 1
        return '.'.join(path[:pos])

    matches = []

    match = get_existing_class_prefix(name)
    if match: matches.append(match)
    
    for prefix in using:
        match = get_existing_class_prefix("%s.%s" % (prefix, name))
        if len(match) > len(prefix) + 1:
            matches.append(match)
    
    return matches

class LocalizedImportError(ImportError):
    def __init__(self, location, *args):
        ImportError.__init__(self, *args)
        self.location = location

class ModuleDoesNotExistButWeDontCare(Exception): pass


load_class_fail_cache = set()
load_class_success_cache = {}

load_class_fail_cache_hit= 0
load_class_success_cache_hit= 0
load_class_cache_miss= 0

def load_class(name, using = [], imp = None, global_dict = None, local_dict = None, module = None):
    if debug_class_loading: print "load_class: Importing %s using %s:" % (name, ' '.join(using))

    global_dict = global_dict or getattr(module, '__dict__', globals())
    local_dict = local_dict or locals()
    file = getattr(module, '__file__', '<Interactive>')

    def load_class_absolute(name):
        global load_class_cache_miss
        global load_class_fail_cache_hit
        global load_class_success_cache_hit
        global load_class_success_cache_miss

        if debug_class_loading: print "load_class:     Trying %s" % name
        components = name.split('.')
        mod = None

        for pos in xrange(1, len(components)):
            name = '.'.join(components[:pos])
            if name in load_class_fail_cache:
                load_class_fail_cache_hit += 1
                break                
            elif name in load_class_success_cache:
                load_class_success_cache_hit += 1
                mod = load_class_success_cache[name]
            else:
                load_class_cache_miss += 1

                try:
                    mod = (imp or __import__)(name, global_dict, local_dict)
                    load_class_success_cache[name] = mod
                except LocalizedImportError, e:
                    if e.location != name:
                        raise
                    if debug_class_loading: print "load_class:             %s" % str(e)
                    load_class_fail_cache.add(name)
                    break

        if debug_class_load_caching:
            print "load_class_cache: fail hits: %s, sucess hits: %s, misses: %s" % (load_class_fail_cache_hit,
                                                                                    load_class_success_cache_hit,
                                                                                    load_class_cache_miss)            
        if mod is None:
            raise ModuleDoesNotExistButWeDontCare("Class does not exist:", name, using, file)
        for component in components[1:]:
            dict_components = []
            if '-' in component:
                dict_components = component.split('-')
                component = dict_components[0]
                del dict_components[0]
            if not hasattr(mod, component):
                raise ModuleDoesNotExistButWeDontCare("Attribute does not exist", mod, component)
            mod = getattr(mod, component)
            for dict_component in dict_components:
                if dict_component not in mod:
                    raise ModuleDoesNotExistButWeDontCare("Item does not exist", mod, dict_component)
                mod = mod[dict_component]
        return mod

    for pkg in using:
        try:
            return load_class_absolute(pkg + '.' + name)
        except ModuleDoesNotExistButWeDontCare, e:
            if debug_class_loading: print "load_class:         %s" % str(e)
    try:
        return load_class_absolute(name)
    except ModuleDoesNotExistButWeDontCare, e:
        if debug_class_loading: print "load_class:         %s" % str(e)
        raise ImportError("""Class does not exist:
    Searched for: %s
    Using: %s
    Found partial matches: %s
    In: %s""" % (name, ', '.join(using), ', '.join(get_existing_class_prefix(name, using)), file))

def subclass_dict(superdict, members):
    res = type(superdict)(superdict)
    res.update(members)
    return res

def subclass_list(superlist, members):
    return superlist + members


def class_full_name(cls):
    cls_name = []
    if hasattr(cls, '__module__'):
        cls_name.append(cls.__module__)
    if getattr(cls, 'ww_class_path', ''):
        cls_name.append(cls.ww_class_path)
    cls_name.append(cls.__name__)
    return '.'.join(cls_name)

def module_file_path(module, extension='.scripts'):
    module_path = sys.modules[module].__file__
    if os.path.splitext(os.path.basename(module_path))[0] == '__init__':
        scripts_path = os.path.dirname(module_path) + extension
    else:
        scripts_path = os.path.splitext(module_path)[0] + extension

    return scripts_path

LOG_EXCEPTION_PATH="/tmp" #None
"""Path to directory where exceptions are logged with log_exception
function. If this is None exceptions are not logged."""
LOG_EXCEPTION_MAX_LOG=65534
"""Max number of logged exception files."""

def is_log_exceptions():
    return not not LOG_EXCEPTION_PATH

def get_log_exception_path():
    """Return path exception directory."""
    return LOG_EXCEPTION_PATH

def set_log_exception_path(path):
    """Set path to exception directory creating it if it does not
    exist."""
    globals()['LOG_EXCEPTION_PATH'] = None

    if path:
        if not os.path.exists(path):
            os.makedirs(path)

        if not os.path.isdir(path):
            raise ValueError('%s path is not a directory' % (path, ))

        globals()['LOG_EXCEPTION_PATH'] = path

def log_exception():
    """Log exception to file and return exception (exception, ID). On
    failure or if LOG_EXCEPTION_PATH is empty/None return (exception, None)."""

    if not LOG_EXCEPTION_PATH:
        return None

    try:
        exc_string = traceback.format_exc()

        try:
            exc_id, exc_fo = _log_exception_new()
            if exc_id and exc_fo:
                exc_fo.write(exc_string)

                syslog.syslog('%s exception logged with id %s' % (str(sys.exc_info()[1]), exc_id))
        finally:
            if exc_fo:
                exc_fo.close()
    except:
        exc_id = None

    return exc_id

def _log_exception_new():
    """Create a new exception file with ID id and return (id, fo)
    tuple where fo is an open file object."""
    exc_id = exc_fo = None

    if LOG_EXCEPTION_PATH:
        # FIXME: Make something like mkstemp here to make this safe

        i = 0
        while not exc_fo and i < LOG_EXCEPTION_MAX_LOG:
            path = os.path.join(LOG_EXCEPTION_PATH, '%05d.info' % (i, ))
            if not os.path.exists(path):
                exc_fo = open(path, 'w')
                exc_id = '%05d' % (i, )
            i += 1

    return (exc_id, exc_fo)

class Ilen(object):
    def __init__(self, itr):
        self.iter = iter(itr)
        
    def __int__(self):
        l = 0
        for obj in self.iter:
            l += 1
        return l
    
    def __cmp__(self, other):
        if not isinstance(other, Ilen):
            other = Ilen(xrange(0, other)) 
        while True:
            try:
                self.iter.next()
            except StopIteration:
                try:
                    other.iter.next()
                except StopIteration:
                    return 0
                else:
                    return -1
            try:
                other.iter.next()
            except StopIteration:
                try:
                    self.iter.next()
                except StopIteration:
                    return 0
                else:
                    return 1

class Timings(object):
    debug_timer_start = False
    debug_timer_stop = False
    debug_timer_measure = False
   
    class Timing(object):
        def __init__(self, timings, name):
            self.timings = timings
            self.name = name
            self.total = datetime.timedelta()
            self.begin = []
            self.params = []
                            
        def start(self):
            if self.timings.debug_timer_start:
                print "Timings start %s(%s, %s)" % ((self.name,) + self.params[-1])
            self.begin.append(datetime.datetime.now())

        def stop(self):
            if self.timings.debug_timer_stop:
                print "Timings stop %s(%s, %s)" % ((self.name,) + self.params[-1])
            delta = datetime.datetime.now() - self.begin.pop()
            self.measure(self.params.pop(), delta)
            for tm in self.begin:
                tm += delta

        def measure(self, params, delta):
            if self.timings.debug_timer_measure:
                print "Timings measure %s(%s, %s): %s" % ((self.name,) + params + (delta,))
            self.total += delta
            self.timings.measure(self.name, params, delta)

        def __enter__(self): self.start()
        def __exit__(self, exc_type, exc_value, traceback): self.stop()
            
    def __init__(self):
        self.timings = {}

    def __getitem__(self, name):
        return self(name)
        
    def __getattr__(self, name):
        return getattr(self.timings, name)

    def __call__(self, name, *arg, **kw):
        if name not in self.timings:
            timing = self.Timing(self, name)
            self.timings[name] = timing
        else:
            timing = self.timings[name]

        timing.params.append((arg, kw))
        return timing

    def measure(self, name, params, time):
        if params[0]:
            Performance.add(name, params[0][0], float(time.seconds) + 0.000001 * time.microseconds)

