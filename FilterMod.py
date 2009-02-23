# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moller@freecode.no>
# Copyright (C) 2008 FreeCode AS, Axel Liljencrantz <axel.liljencrantz@freecode.no>

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

import Webwidgets.ObjectMod

class Filter(Webwidgets.ObjectMod.Object):
    # These getattr/hasattr/setattr are very similar to the ones of
    # Object, except they work on self.ww_filter instead of on
    # self.ww_model...

    attr_cache={}

    def attr_cache_miss(self, filter, name):
#        print "Cache miss in ", filter, name
        cache = self.attr_cache
        if name not in cache:
            cache[name] = cache_row = {}
        else:
            cache_row = cache[name]
            action = []
            for (cache_filter, cache_value) in cache_row.iteritems():
                if cache_value == filter:
                    action.append(cache_filter)
#                    print "move action pointer of field", name, "of element",cache_filter,"from", cache_value, "to", filter.ww_filter
                    
            for i in action:
                cache_row[i] = filter.ww_filter
            
        cache_row[filter] = filter.ww_filter
        

    def attr_cache_get(self, filter, name):
        cache = self.attr_cache
        if name in cache:
            cache_row = cache[name]
            if filter in cache_row:
#                print "Cache hit in ", filter, name
                return (True, getattr(cache_row[filter], name))
        
        return (False, None)


    def __getattr__(self, name):
        """Lookup order: self, self.ww_filter"""

        if not hasattr(self, 'object'):
            raise AttributeError('Filter has no object')
    
        # TODO: enable caching again when bugs are fixxored
        if False and hasattr(self.object, 'ww_filter'):
            root = self.object.ww_filter

            (status, value) = root.attr_cache_get(self, name)
            if status:
                return value

            root.attr_cache_miss(self, name)
            
        return getattr(self.ww_filter, name)

    def __hasattr__(self, name):
        """Lookup order: self, self.ww_filter"""
        ww_filter_has_name = hasattr(self.ww_filter, name)
        self_has_name = (   name in self.__dict__
                         or hasattr(type(self), name))
        return (   self_has_name
                or ww_filter_has_name)

    def _setattr_dispatch(self, name, value):
        """Lookup order: self, self.ww_filter"""
        ww_filter_has_name = hasattr(self.ww_filter, name)
        self_has_name = (   name in self.__dict__
                         or hasattr(type(self), name))
        if (  not ww_filter_has_name
            or self_has_name):
            object.__setattr__(self, name, value)
        else:
            setattr(self.ww_filter, name, value)

    def __getitem__(self, index):
        filter = self
        for i in xrange(0, index):
            filter = filter.ww_filter
        return filter


class StandardFilter(Filter):
    """This class only groups all L{Filter} subclasses that provides
    generic, reusable functionality (as opposed to widget-specific
    filters)."""

class RenameFilter(StandardFilter):
    """This filter renames one or more attributes using a dictionary
    mapping in the name_map attribute."""
    def __getattr__(self, name):
        if name != 'name_map':
            name = self.name_map.get(name, name)
        return getattr(self.ww_filter, name)

    def __setattr__(self, name, value):
        if name != 'name_map':
            name = self.name_map.get(name, name)
        setattr(self.ww_filter, name, value)

    @classmethod
    def rename(cls, **name_map):
        return cls.derive(name="RenameFilter(%s)" % (', '.join(['%s=%s' % (orig, new)
                                                                for (orig, new) in name_map.iteritems()]),),
                          name_map = name_map)

class RetrieveFromFilter(StandardFilter):
    do_retrieve = []
    dont_retrieve = ['retrieve_from']
    retrieve_from = "some_attribute"

    def get_retrieve_object(self, name):
        obj = self.ww_filter

        if (    name not in self.dont_retrieve
            and (not self.do_retrieve
                 or name in self.do_retrieve)):

            obj = getattr(obj, self.retrieve_from)
        return obj

    def __getattr__(self, name):
        obj = self.get_retrieve_object(name)
        if obj is None and self.propagate_none:
            return None
        else:
            return getattr(obj, name)

    def __setattr__(self, name, value):
        obj = self.get_retrieve_object(name)
        if obj is None and value is None and self.propagate_none:
            return
        else:
            setattr(obj, name, value)

    @classmethod
    def retrieve_from(cls, retrieve_from, propagate_none=False, **arg):
        return cls.derive(name="RetrieveFromFilter(%s, %s)" % (retrieve_from,
                                                               ', '.join(['%s=%s' % (key, value)
                                                                          for (key, value) in arg.iteritems()]),),
                          propagate_none = propagate_none,
                          retrieve_from = retrieve_from, **arg)

class RedirectFilter(StandardFilter):
    """This filter redirects model lookups and changes to (the
    ww_filter of) another widget."""

    do_redirect = []
    """If do_redirect is empty everything except the names in
    dont_redirect is redirected. If non-empty, only the named
    attributes are redirected."""
    dont_redirect = ['redirect_path']

    redirect_path = None
    """The widget path relative to this widget to redirect to."""

    redirect_attribute = None
    """Name-value pair (tuple) to search for among parent widgets to
    get the widget to redirect to. If set to a non tuple, search for
    ('__name__', value)."""

    def get_redirected_widget(self, name):
        parent = self
        if (    name not in self.dont_redirect
            and (not self.do_redirect
                 or name in self.do_redirect)):
            parent = self.object
            if self.redirect_path is not None:
                parent = parent + self.redirect_path
            if self.redirect_attribute is not None:
                name = '__name__'
                value = self.redirect_attribute
                if isinstance(value, (tuple, list)):
                    name, value = value
                parent = parent.get_ansestor_by_attribute(name, value)
        return parent

    def __getattr__(self, name):
        return getattr(self.get_redirected_widget(name).ww_filter, name)

    def __setattr__(self, name, value):
        setattr(self.get_redirected_widget(name).ww_filter, name, value)

    @classmethod
    def redirect(cls, *redirect_args, **rest):
        """Derive a subclass given a path, a set of levels (upwards)
        and optionally values for do_redirect, dont_redirect and
        redirect_attribute (see doc. for the class attributes for more
        info on how they work)."""
        relative_path = []
        if len(redirect_args) > 2:
            relative_path = redirect_args[:2]
            rest['redirect_attribute'] = redirect_args[2:]
        elif (len(redirect_args) == 2
              and isinstance(redirect_args[0], (list, tuple))
              and isinstance(redirect_args[1], int)):
            relative_path = redirect_args
        elif redirect_args:
            rest['redirect_attribute'] = redirect_args

        if 'redirect_attribute' in rest and len(rest['redirect_attribute']) == 1:
            rest['redirect_attribute'] = rest['redirect_attribute'][0]

        if relative_path:
            rest['redirect_path'] = Webwidgets.Utils.WidgetPath(*relative_path)

        return cls.derive(
            name="RedirectFilter(%s)" % (', '.join(['%s=%s' % (key, value)
                                                    for (key, value) in rest.iteritems()]),),
            **rest)

class RedirectRenameFilter(StandardFilter):
    """This is the combination of the RedirectFilter and RenameFilter
    - it first renames attributes and the redirects them to another widget."""

    WwFilters = ["RenameFilter", "RedirectFilter"]
    RenameFilter = RenameFilter
    class RedirectFilter(RedirectFilter):
        dont_redirect = ["name_map"] + RedirectFilter.dont_redirect

    @classmethod
    def redirect(cls, *redirect_args, **name_map):
        """Derive a subclass given a path, a set of levels (upwards)
        and a name map (name = name_to_rewrite_to). A value to search
        for among parent widgets (and attribute name) can optionally
        be supplied. See RenameFilter for more details."""

        return cls.derive(
            name = "RedirectRenameFilter(%s, %s)" % (', '.join([str(item) for item in redirect_args]),
                                                     ', '.join(['%s=%s' % (key, value)
                                                                for (key, value) in name_map.iteritems()])),
            RenameFilter = cls.RenameFilter.derive(name_map = name_map),
            RedirectFilter = cls.RedirectFilter.redirect(do_redirect = name_map.values(),
                                                         *redirect_args))

class MapValueFilter(StandardFilter):
    """Allows variable values to be mapped arbitrarily to other values."""
    value_maps = {}
    """Dictionary with member variable names as keys, and two
    dictionaries (one for each direction) for value mappings as
    values."""

    def __getattr__(self, name):
        res = getattr(self.ww_filter, name)
        if name != 'value_maps' and name in self.value_maps and res in self.value_maps[name][1]:
            res = self.value_maps[name][1][res]
        return res

    def __setattr__(self, name, value):
        if name != 'value_maps' and name in self.value_maps and value in self.value_maps[name][0]:
            value = self.value_maps[name][0][value]
        setattr(self.ww_filter, name, value)

    @classmethod
    def map_values(cls, **value_maps):
        value_maps = dict([(name, (value_map,
                                   dict([(map_to, map_from)
                                         for (map_from, map_to)
                                         in value_map.iteritems()])))
                           for (name, value_map)
                           in value_maps.iteritems()])


        return cls.derive(name = "MapValueFilter(%s)" % (', '.join(value_maps.keys()),),
                          value_maps = value_maps)

class DebugFilter(StandardFilter):
    debug_result = False
    debug_value = False
    debug_exception = True
    debug_getattr = True
    debug_setattr = True
    debug_collapse = True

    def __init__(self, *arg, **kw):
        self.__dict__['_collapsed'] = set()
        StandardFilter.__init__(self, *arg, **kw)

    def _print_debug(self, name, **kw): #(name, value, res, exc):
        res = "%s: %s" % (type(self).__name__, name)
        
        if 'value' in kw:
            if self.debug_value:
                res += " <- %s" % (kw['value'],)
        elif 'result' in kw:
            if self.debug_result:
                res += " -> %s" % (kw['result'],)
        if 'exception' in kw:
            if debug_exception:
                res += " -@!%§!!-> %s" % (kw['exception'],)
        print res
    
    def __getattr__(self, name):
        if not self.debug_getattr or self.debug_collapse and name in self._collapsed:
            return getattr(self.ww_filter, name)
        if self.debug_collapse:
            self._collapsed.add(name)
        try:
            res = getattr(self.ww_filter, name)
            self._print_debug(name, result=res)
            return res
        except Exception, e:
            self._print_debug(name, exception=e)
            raise

    def __setattr__(self, name, value):
        if not self.debug_setattr or self.debug_collapse and name in self._collapsed:
            return setattr(self.ww_filter, name, value)
        if self.debug_collapse:
            self._collapsed.add(name)
        try:
            setattr(self.ww_filter, name, value)
            self._print_debug(name, value=value)
        except Exception, e:
            self._print_debug(name, value=value, exception=e)
            raise

    @classmethod
    def debug(cls, name, **kw):
        return cls.derive(name = name, **dict(("debug_" + name, value) for (name, value) in kw.iteritems()))

class TeeFilter(StandardFilter):
    def _get_tee_filter_prefixes(self, name):
        return self.tee_map.get(name, self.tee_map.get('__all__', ['']))

    def __getattr__(self, name):
        if name != 'tee_map':
            name = self._get_tee_filter_prefixes(name)[0] + name
        return getattr(self.ww_filter, name)

    def __setattr__(self, name, value):
        prefixes = [""]
        if name != 'tee_map':
            prefixes = self._get_tee_filter_prefixes(name)
        for prefix in prefixes:
            setattr(self.ww_filter, prefix + name, value)

    @classmethod
    def tee(cls, **tee_map):
        return cls.derive(name = "TeeFilter(%s)" % (', '.join("%s=%s" % (name, value) for (name, value) in tee_map.iteritems()),),
                          tee_map = tee_map)

class MangleFilter(StandardFilter):
    """This is the most generic of the redirection/renaming filters.
    It allows the redirection/renaming to be done by arbitrary
    functions provided by the user."""
    @classmethod
    def mangle(cls, **mangle_rules):
        """Derive a subclass given a set of redirection rules. Every
        rule is of the form attribute_name = getter of attribute_name
        = (getter, setter)."""
        properties = {}
        for name, rule in mangle_rules.iteritems():
            if not isinstance(rule, (tuple, list)):
                rule = (rule,)
            properties[name] = property(*rule)
        return cls.derive(**properties)


class Wrapper(Webwidgets.ObjectMod.Object):
    def __init__(self, ww_model, **attrs):
        if hasattr(ww_model, 'ww_filter'):
            attrs['ww_filter'] = ww_model.ww_filter
        Webwidgets.ObjectMod.Object.__init__(self, ww_model = ww_model, **attrs)

class PersistentWrapper(Wrapper):
    def ww_wrapper_key(cls, ww_model, **attrs):
        return str(id(ww_model))
    ww_wrapper_key = classmethod(ww_wrapper_key)

    def __new__(cls, **attrs):
        if 'wrappers' not in cls.__dict__:
                cls.wrappers = {}
        wrapper_key = cls.ww_wrapper_key(**attrs)
        if wrapper_key not in cls.wrappers:
            wrapper = cls.wrappers[wrapper_key] = Wrapper.__new__(cls, **attrs)
            wrapper.ww_first_init(**attrs)
        else:
            wrapper = cls.wrappers[wrapper_key]
        return wrapper

    def __init__(self, *arg, **kw):
        self.__dict__.update(kw)

    def ww_first_init(self, *arg, **kw):
        Wrapper.__init__(self, *arg, **kw)
