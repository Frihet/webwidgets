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

import types, sys
import Webwidgets.Utils, Webwidgets.BaseObjectMod

class NoOldValue(object):
    """This class is used as a marker to signify that there was no old
    attribute set when doing setattr"""

class FilteredObject(Webwidgets.BaseObjectMod.OrderableObject):
    """FilteredObject provides filter chaining for attribute access.
    Filters provide a flexible approach to overriding specific
    behaviour in in a base class."""

    ww_child_class_orderings = set(('filter',))

    ww_model = None
    """If non-None, any attribute not found on this object will be
    searched for on this object."""

    WwModel = None
    """If non-None and the model attribute is None, this class will be
    instantiated and the instance placed in the model attribute."""

    def __init__(self, **attrs):
        Webwidgets.BaseObjectMod.OrderableObject.__init__(self, **attrs)

        if self.ww_model is None and type(self).WwModel is not None:
            self.__dict__['ww_model'] = self.WwModel()

        self.setup_filter()

    @classmethod
    def print_filter_class_stack(cls, indent = ''):
        return cls.print_child_class_ordering('filter')    

    def setup_filter(self):
        ww_filter = self.__dict__.get('ww_filter', self)
        object = self.__dict__.get('object', self)
        # Note the reversal of order. What this means is: Highest
        # _filter_level first, that is, the last filter in the chain
        # first. We build the chain backwards, feeding the last built
        # one to the ww_filter attribute when building the next one
        for filter_class in reversed(self.get_child_class_ordering('filter')):
            ww_filter = filter_class(ww_filter = ww_filter, object = object)
        self.__dict__['ww_filter'] = ww_filter
        self.__dict__["object"] = object

    def is_first_filter(self):
        if not hasattr(self, 'object'):
            # We haven't set anything up in __init__ yet, so pretend
            # we're not first (we can't really know yet either way) so
            # that no notifications are thrown anywhere random...
            return False
        return self.object.ww_filter is self
    is_first_filter = property(is_first_filter)

    def print_filter_instance_stack(self, name = 'ww_filter', attrs = []):
        ww_filter = getattr(self, name)
        ww_filters = []
        while ww_filter is not self and ww_filter is not self.ww_model:
            ww_filters.append(ww_filter)
            ww_filter = ww_filter.ww_filter
        return '\n'.join(["%s.%s @ %s %s" % (type(ww_filter).__module__, type(ww_filter).__name__, id(ww_filter),
                                             ', '.join([str(getattr(ww_filter, attr, None)) for attr in attrs]))
                          for ww_filter in ww_filters]) + '\n'

    #### fixme ####
    # name = "Inheriting properties from parent widget"
    #
    # description = """It would be usefull to have widgets inherit
    # (read-only) attributes from their parent widgets. This would be
    # especially usefull for database sessions and the like, where the
    # session could be overridden for a part of an application and all
    # of its sub-parts.
    #
    # This has been tested, but was found to be too slow (when an
    # attribute is not found, it still had to traverse the whole tree
    # to the root every time), and the code was removed."""
    #### end ####

    def __getattr__(self, name):
        """Lookup order: self, self.ww_model"""
        if self.ww_model is None:
            raise AttributeError(self, name)
        try:
            return getattr(self.ww_model, name)
        except:
            e = sys.exc_info()[1]
            e.args = (self,) + e.args
            raise type(e), e, sys.exc_info()[2]

    def __hasattr__(self, name):
        """Lookup order: self, self.ww_model"""
        model_has_name = (   self.ww_model is not None
                          and hasattr(self.ww_model, name))
        self_has_name = (   name in self.__dict__
                         or hasattr(type(self), name))
        return (   self_has_name
                or model_has_name)

    def _setattr_dispatch(self, name, value):
        """Lookup order: self, self.ww_model"""
        model_has_name = (   self.ww_model is not None
                          and hasattr(self.ww_model, name))
        self_has_name = (   name in self.__dict__
                         or hasattr(type(self), name))
        if (   not model_has_name
            or self_has_name):
            object.__setattr__(self, name, value)
        else:
            setattr(self.ww_model, name, value)

    def __setattr__(self, name, value):
        """Lookup order: self, self.ww_model"""
        old_value = getattr(self, name, NoOldValue)

        if value is not old_value:
            self._setattr_dispatch(name, value)

            # Don't compare Objects, e.g. widgets - might not allways
            # work, and it's sort of meaningless anyway in this
            # context.
            if (    self.is_first_filter
                and (   isinstance(value, FilteredObject)
                     or isinstance(old_value, FilteredObject)
                     or value != old_value)):
                self.object.notify('%s_changed' % name, value)


class Filter(FilteredObject):
    ww_class_orderings = set.union(FilteredObject.ww_class_orderings,
                                   ('filter',))

    """About filter ordering:

    Filters are chained so that ww_filter on each points to the next
    filter, the last one pointing on the widget itself.

    The getattr/hasattr/setattr methods on filters defaults to
    accessing the ww_filter attribute (the next filter), not ww_model
    as Object's ones does."""

    ww_filter_pre = set()
    """List of filters that are to be placed before this filter in the
    filter chain.

    Note: If you make circles, you will cause an infinite loop. That's
    usually what cirle means, so no news there :P
    """

    ww_filter_post = set()
    """List of filters that are to be placed before this filter in the
    filter chain.

    Note: If you make circles, you will cause an infinite loop. That's
    usually what cirle means, so no news there :P
    """

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
