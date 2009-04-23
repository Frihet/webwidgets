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
        cls._set_class_order_nr(members)
        cls._mangle_class_data(members)

        self = type.__new__(cls, name, bases, members)

        self._init_classes()
        self._init_class_subclasses()
        self._set_class_path()
        self.process_class_orderings()
        self.process_child_class_orderings()
        
        return self


    @classmethod
    def _set_class_order_nr(cls, members):
        members['ww_class_order_nr'] = cls.ww_class_order_nr.next()

    @classmethod
    def _mangle_class_data(cls, members):
        # This dictionary contains data specific to this class, that
        # can not be inherited.
        if 'ww_class_data' not in members:
            members['ww_class_data'] = {}
        for key in members.keys():
            if key.startswith('ww_class_data__'):
                members['ww_class_data'][key[len('ww_class_data__'):]] = members[key]
                del members[key]


class Required(object):
    """Required value, if set on a class the member must be set or
    overridden in a subclass or instance."""
    pass

class Object(object):
    """Object is a more elaborate version of object, providing a few
    extra utility methods, some extra 'magic' class attributes -
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

    ww_class_orderings = set(())
    """Set of orderings applied to this class. See ww_ORDERINGNAME_pre
    and ww_ORDERINGNAME_post for each ordering for more information on
    what it's used for."""

    ww_child_class_orderings = set(('filter',))
    """Set of orderings applied to member classes of this class. See
    ww_ORDERINGNAME_pre and ww_ORDERINGNAME_post on members for each
    ordering for more information on what it's used for."""

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

    @classmethod
    def _init_classes(cls):
        cls.ww_classes = []
        if not cls.ww_class_data.get('no_classes_name', False):
            cls.ww_classes.append(None) # Our own one is set later on
        for base in cls.__bases__:
            if hasattr(base, 'ww_classes'):
                cls.ww_classes.extend(base.ww_classes)

    @classmethod
    def ww_update_classes(cls):
        if not cls.ww_class_data.get('no_classes_name', False):
            cls.ww_classes[0] = Webwidgets.Utils.class_full_name(cls)

    @classmethod
    def _init_class_subclasses(cls):
        cls.ww_class_subclasses = Webwidgets.Utils.WeakSet()
        for base in cls.__bases__:
            if hasattr(base, 'ww_class_subclasses'):
                base.ww_class_subclasses.add(cls)

    @classmethod
    def _set_class_path(cls, path = ()):
        cls.ww_class_path = '.'.join(path)
        cls.ww_update_classes()
        sub_path = path + (cls.__name__,)
        for key, value in cls.__dict__.iteritems():
            if hasattr(value, '_set_class_path'):
                value._set_class_path(sub_path)
        return cls

    @classmethod
    def _update_class_ordering_metadata(cls, ordering_name):
        pre_member = "ww_%s_pre" % (ordering_name,)
        post_member = "ww_%s_post" % (ordering_name,)
        metadata_member = "ww_%s_metadata" % (ordering_name,)

        if metadata_member not in cls.__dict__:
            metadata = {'pre': Webwidgets.Utils.WeakSet(),
                        'post': Webwidgets.Utils.WeakSet(),
                        'pre_backlink': Webwidgets.Utils.WeakSet(),
                        'post_backlink': Webwidgets.Utils.WeakSet(),
                        'level': 0}
            setattr(cls, metadata_member, metadata)
        else:
            metadata = getattr(cls, metadata_member)
            metadata['pre'].clear()
            metadata['post'].clear()
            metadata['level'] = 0

        # Copy pres and posts from the user-set attributes
        metadata['pre'].update(getattr(cls, pre_member, ()))
        metadata['post'].update(getattr(cls, post_member, ()))

        # Find intermediates between bases
        def find_path_between_bases(node, intermediaries, max_level, path):
            for successor in  set.union(set(getattr(node, metadata_member, {'post': ()})['post']),
                                        getattr(node, metadata_member, {'post_backlink': ()})['post_backlink']):
                if successor in bases:
                    intermediaries.update(path)
                elif getattr(successor, metadata_member)['level'] <= max_level:
                    find_path_between_bases(successor, intermediaries, max_level, set.union(path, set((successor,))))

        bases = set(cls.__bases__)
        max_level = max(getattr(base, metadata_member, {'level': 0})['level']
                        for base in bases)
        intermediaries = set(bases)
        for base in bases:
            find_path_between_bases(base, intermediaries, max_level, set())

        # Append inherited pre:s and post:s
        bases = set(cls.__bases__)
        for base in bases:
            if ordering_name in getattr(base, 'ww_class_orderings', ()):
                if not hasattr(base, metadata_member):
                    raise TypeError("%s.%s:s %s oredring has not been initialized while initializing a subclass %s.%s" % (
                        base.__module__, base.__name__, ordering_name, cls.__module__, cls.__name__))
                base_metadata = getattr(base, metadata_member)
                metadata['pre'].update(base_metadata['pre'] - intermediaries)
                metadata['post'].update(base_metadata['post'] - intermediaries)
                metadata['pre_backlink'].update(base_metadata['pre_backlink'] - intermediaries)
                metadata['post_backlink'].update(base_metadata['post_backlink'] - intermediaries)
        
        # Update linked objects
        for pre in metadata['pre']:
            if not hasattr(pre, metadata_member):
                raise TypeError("%s.%s:s %s oredring has not been initialized while initializing a successor %s.%s" % (
                    pre.__module__, pre.__name__, ordering_name, cls.__module__, cls.__name__))
            getattr(pre, metadata_member)['post_backlink'].add(cls)
        for post in metadata['post']:
            if not hasattr(post, metadata_member):
                raise TypeError("%s.%s:s %s oredring has not been initialized while initializing a predesessor %s.%s" % (
                    post.__module__, post.__name__, ordering_name, cls.__module__, cls.__name__))
            getattr(post, metadata_member)['pre_backlink'].add(cls)

    @classmethod
    def _report_ordering_cicrle(cls, ordering_name, done):
        metadata_member = "ww_%s_metadata" % (ordering_name,)

        def find_base_cause(cls, other, direction = 'post'):
            direction_backlink = direction + '_backlink'
            for base in cls.__bases__:
                if (   other in getattr(base, metadata_member, {direction: ()})[direction]
                    or other in getattr(base, metadata_member, {direction_backlink: ()})[direction_backlink]):
                    return [cls] + find_base_cause(base, other, direction)
            return [cls]

        loop = done[done.index(cls):]
        raise Exception("""Ordering circle encountered for %s ordering of classes:
Post-links:
 %s
Pre-links:
 %s""" % (
            ordering_name,
            '\n '.join(' <- '.join('%s%s' % (parent.ww_classes[0],
                                             (    next_loop_cls in getattr(parent, metadata_member, {'post_backlink': ()})['post_backlink']
                                              and '(backlnk)'
                                              or  next_loop_cls in getattr(parent, metadata_member, {'post': ()})['post']
                                              and '(forlnk)'
                                              or  '(FAIL)'))
                                           for parent in find_base_cause(loop_cls, next_loop_cls, 'post'))
                       for (loop_cls, next_loop_cls) in zip(loop + loop[:1], loop[1:] + loop[:2])),
            '\n '.join(' <- '.join('%s%s' % (parent.ww_classes[0],
                                             (    next_loop_cls in getattr(parent, metadata_member, {'post_backlink': ()})['post_backlink']
                                              and '(backlnk)'
                                              or  next_loop_cls in getattr(parent, metadata_member, {'post': ()})['post']
                                              and '(forlnk)'
                                              or  '(FAIL)'))
                                   for parent in find_base_cause(loop_cls, next_loop_cls, 'post'))
                       for (loop_cls, next_loop_cls) in zip(loop + loop[:1], loop[1:] + loop[:2]))))

    @classmethod
    def _update_class_level(cls, ordering_name, level = None, done = []):
        metadata_member = "ww_%s_metadata" % (ordering_name,)

        if level is None:
            level = max([0] + [getattr(pre, metadata_member, {'level': 0})['level']
                               for pre in Webwidgets.Utils.WeakSet.union(getattr(cls, metadata_member)['pre'],
                                                                         getattr(cls, metadata_member)['pre_backlink'])]) + 1
            
        # Update our level and levels downstream in the network
        # Note: If you make circles, you will cause an infinite loop.
        # That's usually what cirle means, so no news there :P
        if cls in done:
            cls._report_ordering_cicrle(ordering_name, done)
        cls_metadata = getattr(cls, metadata_member)
        cls_metadata['level'] = level
        for post in Webwidgets.Utils.WeakSet.union(cls_metadata['post'], cls_metadata['post_backlink']):
            post_metadata = getattr(post, metadata_member)
            if post_metadata['level'] <= level:
                post._update_class_level(ordering_name, level + 1, done + [cls])
  
    @classmethod
    def process_class_ordering(cls, ordering_name):
        cls._update_class_ordering_metadata(ordering_name)
        cls._update_class_level(ordering_name)

        # Update sublcasses
        for subclass in cls.ww_class_subclasses:
            subclass.process_class_ordering(ordering_name)

        if getattr(cls, 'ww_debug_%s_ordering' % ordering_name, False):
            print "Registering widget % ordering: %s" % (ordering_name, cls.__name__)
            print "    Pre:", ', '.join(pre.__name__ for pre in metadata['pre'])
            print "    Post:", ', '.join(post.__name__ for post in metadata['post'])
            print "    Level:", metadata['level']

    @classmethod
    def add_class_in_ordering(cls, ordering_name, pre = set(), post = set()):
        pre_member = "ww_%s_pre" % (ordering_name,)
        post_member = "ww_%s_post" % (ordering_name,)

        if pre:
            setattr(cls, pre_member, set.union(getattr(cls, pre_member, set()), pre))
        if post:
            setattr(cls, post_member, set.union(getattr(cls, post_member, set()), post))
        cls.process_class_ordering(ordering_name)
        return cls


    @classmethod
    def process_child_class_auto_ordering(cls, ordering_name):
        pass
#         metadata_member = "ww_%s_metadata" % (ordering_name,)

#         children = cls.get_child_class_ordering(ordering_name)
#         children.sort(lambda a, b: cmp(a.ww_class_order_nr, b.ww_class_order_nr))

#         children = [(child, getattr(child, metadata_member)['level']) for child in children]

#         for ((child, level), (next_child, next_level)) in zip(children, children[1:]):
#             if level <=  next_level:
#                 child.add_class_in_ordering(ordering_name, post = [next_child])

    @classmethod
    def process_child_class_ordering(cls, ordering_name):
        #print "process_child_class_ordering %s for %s" % (ordering_name, cls)
        first_member = "ww_%s_first" % (ordering_name,)
        last_member = "ww_%s_last" % (ordering_name,)

        # FIXME: Add all the first and last nodes of ordering is a forrest
        total_order = cls.get_child_class_ordering(ordering_name)
        first = set()
        last = set()
        if total_order:
            first.add(total_order[0])
            last.add(total_order[-1])
        setattr(cls, first_member, first)
        setattr(cls, last_member, last)

    @classmethod
    def get_class_ordering_cmp(cls, ordering_name):
        metadata_member = "ww_%s_metadata" % (ordering_name,)
        return lambda a, b: (   cmp(getattr(a, metadata_member)['level'],
                                    getattr(b, metadata_member)['level'])
                             or cmp(a, b)
                             or cmp(id(a), id(b)))

    @classmethod
    def get_child_class_ordering(cls, ordering_name):
        """Gives you a full ordering of all children that are ordered
        according to ordering_name."""

        metadata_member = "ww_%s_metadata" % (ordering_name,)
        child_classes = [child_cls
                         for child_cls in (getattr(cls, name, None) for name in dir(cls))
                         if hasattr(child_cls, metadata_member)]
        child_classes.sort(cls.get_class_ordering_cmp(ordering_name))
        return child_classes

    @classmethod
    def print_child_class_ordering(cls, ordering_name, indent = ''):
        return indent + '%s.%s\n%s' % (cls.__module__, cls.__name__,
                                       ''.join([child_cls.print_child_class_ordering(ordering_name, indent = indent + '  ')
                                                for child_cls in cls.get_child_class_ordering(ordering_name)]))

    @classmethod
    def process_class_orderings(cls):
        for ordering in cls.ww_class_orderings:
            cls.process_class_ordering(ordering)
    
    @classmethod
    def process_child_class_orderings(cls):
        for ordering in cls.ww_child_class_orderings:
            cls.process_child_class_auto_ordering(ordering)
            cls.process_child_class_ordering(ordering)

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
