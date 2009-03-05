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
import Webwidgets.Utils, Webwidgets.Utils.Threads

class NoOldValue(object):
    """This class is used as a marker to signify that there was no old
    attribute set when doing setattr"""

class Type(type):
    ww_class_order_nr = Webwidgets.Utils.Threads.Counter()

    def __new__(cls, name, bases, members):
        members = dict(members)
        ww_classes = []

        # This dictionary contains data specific to this class, that
        # can not be inherited.
        if 'ww_class_data' not in members:
            members['ww_class_data'] = {}
        members['ww_class_data'] = {}


        for key in members.keys():
            if key.startswith('ww_class_data__'):
                members['ww_class_data'][key[len('ww_class_data__'):]] = members[key]
                del members[key]

        members['ww_classes'] = []
        if not members['ww_class_data'].get('no_classes_name', False):
            members['ww_classes'].append(None) # Our own one is set later on
        for base in bases:
            if hasattr(base, 'ww_classes'):
                members['ww_classes'].extend(base.ww_classes)

        members['ww_class_order_nr'] = cls.ww_class_order_nr.next()

        def set_class_path(widget, path = ()):
            widget.ww_class_path = '.'.join(path)
            widget.ww_update_classes()
            sub_path = path + (widget.__name__,)
            for key, value in widget.__dict__.iteritems():
                if isinstance(value, cls):
                    set_class_path(value, sub_path)
            return widget

        return set_class_path(type.__new__(cls, name, bases, members))

    @classmethod
    def process_class_ordering(cls, name, bases, members, ordering_name):
        subordinate_member = "ww_%s_subordinates" % (ordering_name,)
        level_member = "_%s_level" % (ordering_name,)
        
        subordinates = set()
        
        if subordinate_member in members:
            subordinates = subordinates.union(set(members[subordinate_member]))
        for base in bases:
            if hasattr(base, subordinate_member):
                subordinates = subordinates.union(getattr(base, subordinate_member))

        members[level_member] = max([0] + [getattr(sub, level_member)
                                           for sub in subordinates]) + 1
        
        members[subordinate_member] = subordinates

        if getattr(cls, 'debug_class_%s_ordering' % ordering_name, False):
            print "Registering widget % ordering: %s" % (ordering_name, name)
            print "    Subordinates:", ', '.join([sub.__name__ for sub in subordinates])
            print "    Level:", members[level_member]

    def ww_update_classes(self):
        if not self.ww_class_data.get('no_classes_name', False):
            self.ww_classes[0] = Webwidgets.Utils.class_full_name(self)

class Required(object):
    """Required value, if set on a class the member must be set or
    overridden in a subclass or instance."""
    pass

class Object(object):
    """Object is a more elaborate version of object, providing a few
    extra utility methods, some extra"magic" class attributes -
    L{ww_classes}, L{ww_class_order_nr} and L{ww_class_path} and
    model/model-filter handling."""

    __metaclass__ = Type

    ww_class_data__no_classes_name = True
    """Do not include the name of this particular class in L{ww_classes}
    for subclasses of this class (and for this class itself)."""

    ww_classes = ("Webwidgets.Object",)
    """Read-only attribute containing a list of the names of all
    inherited ww_classes except ones with L{ww_class_data__no_classes_name} set to
    True. This is mainly usefull for automatic CSS class generation."""

    ww_class_order_nr = 0
    """Read-only attribute containing a sequence number for the class,
    similar too id(class), but guaranteed to be monotonically
    increasing, so that a class created after another one will have a
    greater number than the other one."""

    ww_class_path = ''
    """The path between the module (__module__) and the class
    (__name__). For ww_classes that are created directly in the module
    scope, this is the empty string. For ww_classes created as members of
    some ther class, this is the ww_class_path and __name__ of that
    other class joined. The path is dot-separated."""

    ww_model = None
    """If non-None, any attribute not found on this object will be
    searched for on this object."""

    WwModel = None
    """If non-None and the model attribute is None, this class will be
    instantiated and the instance placed in the model attribute."""

    WwFilters = []
    """Filter is a set of classes that are to be instantiated and
    chained together as filters for this object. Ech of these will
    have its filter attribute set to the next one, except for the last
    one, which will have it set to this very object."""

    def __init__(self, **attrs):
        """Creates a new object
        raise AttributeError(self, name)

        @param ww_filter: The next filter when building a filter
            tree/chain. None for the root node, next
            filter in chain otherwise.
        @param attrs: Any attributes to set for the object.
        """
        if 'ww_model' in attrs and attrs['ww_model'] is None:
            del attrs['ww_model']
        if 'ww_model' not in attrs and self.WwModel is not None:
            attrs['ww_model'] = self.WwModel()
        # FIXME: Does not attribute on ww_model as it should
        self.__dict__.update(attrs)
        self.setup_filter()

        # This should perform some extra code validation, but it
        # doesnt work, for two reasons.  Firstly, when used with any
        # slow attributes, e.g. properties, it adds several seconds to
        # log in time. Not good.  Secondly, many object properties may
        # not be called before the parent is set, which is done after
        # object construction. In other words, enabling this code will
        # throw exceptions like it's going out of style.
        if False:
            for name in dir(self):
                try:
                    attr = getattr(self, name, None)
                except:
                    attr = None

                if attr is Required:
                    raise AttributeError('Required attribute %s missing' % (name, ))

    def get_filter(cls, filter_class):
        if isinstance(filter_class, (str, unicode)):
            filter_class = getattr(cls, filter_class)
        return filter_class
    get_filter = classmethod(get_filter)

    def setup_filter(self, name = 'ww_filter', ww_filter_classes = None, ww_filter = None, object = None):
        if ww_filter is None: ww_filter = self.__dict__.get(name, self)
        if object is None: object = self.__dict__.get('object', self)
        if ww_filter_classes is None: ww_filter_classes = self.WwFilters
        for filter_class in reversed(ww_filter_classes):
            ww_filter = self.get_filter(filter_class)(ww_filter = ww_filter, object = object)
        self.__dict__[name] = ww_filter
        self.__dict__["object"] = object

    def is_first_filter(self):
        if not hasattr(self, 'object'):
            # We haven't set anything up in __init__ yet, so pretend
            # we're not first (we can't really know yet either way) so
            # that no notifications are thrown anywhere random...
            return False
        return self.object.ww_filter is self
    is_first_filter = property(is_first_filter)

    def print_filter_class_stack(cls, ww_filter_classes = None, indent = ''):
        if ww_filter_classes is None: ww_filter_classes = cls.WwFilters
        return indent + '%s.%s\n%s' % (cls.__module__, cls.__name__,
                                         ''.join([cls.get_filter(filter).print_filter_class_stack(indent = indent + '  ')
                                                  for filter in ww_filter_classes]))
    print_filter_class_stack = classmethod(print_filter_class_stack)

    def print_filter_instance_stack(self, name = 'ww_filter', attrs = []):
        ww_filter = getattr(self, name)
        ww_filters = []
        while ww_filter is not self and ww_filter is not self.ww_model:
            ww_filters.append(ww_filter)
            ww_filter = ww_filter.ww_filter
        return '\n'.join(["%s.%s @ %s %s" % (type(ww_filter).__module__, type(ww_filter).__name__, id(ww_filter),
                                             ', '.join([str(getattr(ww_filter, attr, None)) for attr in attrs]))
                          for ww_filter in ww_filters]) + '\n'

    def derive(cls, *clss, **members):
        name = 'anonymous'
        if 'name' in members:
            name = members.pop('name')
        return types.TypeType(name, (cls,) + clss, members)
    derive = classmethod(derive)

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
                and (   isinstance(value, Object)
                     or isinstance(old_value, Object)
                     or value != old_value)):
                self.object.notify('%s_changed' % name, value)

    def notify(self, message, *args, **kw):
        """See L{notify_kw}."""
        self.notify_kw(message, args, kw)

    def notify_kw(self, message, args = (), kw = {}, path = None):
        """To handle notifications for a kind of Object, override this
        method in the subclass to do something usefull."""
        pass

    def __unicode__(self):
        return object.__repr__(self)

    def __str__(self):
        return str(unicode(self))

    def __repr__(self):
        return str(self)

class Model(Object):
    pass
