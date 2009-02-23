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

import sys, os, os.path

debug_class_loading = False
debug_class_load_caching = False

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
