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

"""Base widgets to define the application user interface.

This module contains a set of base widgets that can be usedv to define
the user-interface of an application. In addition, it contains some
generic base ww_classes that can be used when implementing more elaborate
widgets.
"""

import types, xml.sax.saxutils, os.path, cgi, re, sys, weakref
import Webwidgets.Utils, Webwidgets.Utils.Gettext, Webwidgets.Constants
import Webwidgets.Utils.FileHandling
import Webwidgets.Utils.Threads
import traceback, WebUtils.HTMLForException, pdb
        
debug_exceptions = False
log_exceptions = True

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

    def ww_update_classes(self):
        if not self.ww_class_data.get('no_classes_name', False):
            self.ww_classes[0] = Webwidgets.Utils.class_full_name(self)

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

class Wrapper(Object):
    def __init__(self, ww_model, **attrs):
        if hasattr(ww_model, 'ww_filter'):
            attrs['ww_filter'] = ww_model.ww_filter
        Object.__init__(self, ww_model = ww_model, **attrs)

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

class Model(Object):
    pass

class Filter(Object):
    # These getattr/hasattr/setattr are very similar to the ones of
    # Object, except they work on self.ww_filter instead of on
    # self.ww_model...
    def __getattr__(self, name):
        """Lookup order: self, self.ww_filter"""
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

    def rename(cls, **name_map):
        return cls.derive(name="RenameFilter(%s)" % (', '.join(['%s=%s' % (orig, new)
                                                                for (orig, new) in name_map.iteritems()]),),
                          name_map = name_map)
    rename = classmethod(rename)


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

    def retrieve_from(cls, retrieve_from, propagate_none=False, **arg):
        return cls.derive(name="RetrieveFromFilter(%s, %s)" % (retrieve_from,
                                                               ', '.join(['%s=%s' % (key, value)
                                                                          for (key, value) in arg.iteritems()]),),
                          propagate_none = propagate_none,
                          retrieve_from = retrieve_from, **arg)
    retrieve_from = classmethod(retrieve_from)

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
            rest['redirect_path'] = Webwidgets.Utils.RelativePath(*relative_path)

        return cls.derive(
            name="RedirectFilter(%s)" % (', '.join(['%s=%s' % (key, value)
                                                    for (key, value) in rest.iteritems()]),),
            **rest)
    redirect = classmethod(redirect)
    
class RedirectRenameFilter(StandardFilter):
    """This is the combination of the RedirectFilter and RenameFilter
    - it first renames attributes and the redirects them to another widget."""
    
    WwFilters = ["RenameFilter", "RedirectFilter"]
    RenameFilter = RenameFilter
    class RedirectFilter(RedirectFilter):
        dont_redirect = ["name_map"] + RedirectFilter.dont_redirect

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
    redirect = classmethod(redirect)

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

    def map_values(cls, **value_maps):
        value_maps = dict([(name, (value_map,
                                   dict([(map_to, map_from)
                                         for (map_from, map_to)
                                         in value_map.iteritems()])))
                           for (name, value_map)
                           in value_maps.iteritems()])

                                   
        return cls.derive(name = "MapValueFilter(%s)" % (', '.join(value_maps.keys()),),
                          value_maps = value_maps)
    map_values = classmethod(map_values)

class MangleFilter(StandardFilter):
    """This is the most generic of the redirection/renaming filters.
    It allows the redirection/renaming to be done by arbitrary
    functions provided by the user."""
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
    mangle = classmethod(mangle)

class Widget(Object):
    """Widget is the base class for all widgets. It manages class name
    collection, attribute handling, child instantiation and
    notifications.

    The class name collection system gathers the names of all
    base-ww_classes for a class and uses these to construct a string
    suitable for use in an HTML 'class' attribute.

    See L{Webwidgets.Program.Program.Session.notify} for an
    explanation of notifications.
    """
    
    ww_explicit_load = False
    """Controls wether the widget class is automatically instantiated
    when the parent widget is instantiated."""

    html_class = 'Webwidgets-Widget'
    """Read-only attribute containing the information in L{ww_classes}
    but in a format suitable for inclusion in the 'class' attribute in
    HTML."""

    visible = True
    """Whether the widget is shown on screen or not."""

    title = None
    """The (human readable) title for the widget, used for pages,
    items in lists etc. If None, the widget path is used."""

    root = False
    parent = None
    name = 'anonymous'

    system_errors = []

    error = None
    """Displayed by a corresponding L{Label} if set to non-None.
    See that widget for further information."""

    def __init__(self, session, win_id, **attrs):
        """Creates a new widget
        
        @param session: L{Webwidgets.Program.Session} instance. Must be
                       same as for any parent widget.

        @param win_id: The "window identifier". Must be same as for any
                     parent widget. The window identifier is a
                     pair of the path to the Webware page that serves
                     the current Webwidgets application, and any extra
                     window id string added as a first part of an
                     extra path. Example: if we are accessing

                     http://myserver/WKMod/MyContext/MyPage/:popup/foo/bar?fie=hehe

                     the win_id will be

                     ('MyContext/MyPage', 'popup')

        @param attrs: Any attributes to set for the widget.
        
        """

        # We update __dict__ not to have to bother with __setattr__
        # and notifications.
        # Set name and parent here as an optimization...
        self.__dict__.update({
            'session': session,
            'win_id': win_id,
            'system_errors': [],
            'name': 'anonymous',
            'parent': None})
        Object.__init__(self, **attrs)

    class HtmlId(object):
        def __get__(self, instance, owner):
            if instance is None or instance.parent is None:
                return None
            return Webwidgets.Utils.path_to_id(instance.path)
    html_id = HtmlId()

    class HtmlClass(object):
        def __get__(self, instance, owner):
            ww_classes = owner.ww_classes
            if instance:
                ww_classes = instance.ww_classes
            return Webwidgets.Utils.classes_to_css_classes(ww_classes)
    html_class = HtmlClass()

    class HtmlAttributes(object):
        def __get__(self, instance, owner):
            if instance is None or instance.parent is None:
                return None
            return instance.draw_html_attributes(instance.path)            
    html_attributes = HtmlAttributes()

    #### fixme ####
    # name = "Iterative definition of self.path"
    # type = "optimization"
    # description = "The path attribute could be set by the parent
    # widget and be a normal variable instead of a property. This
    # would probably speed things up a bit."
    #### end ####
    class Path(object):
        def __get__(self, instance, owner):
            """Returns the path of the widget within the widget tree."""
            if instance is None:
                return None
            node = instance
            path = []
            while node.parent and not node.root:
                path.append(node.name)
                node = node.parent
            if not node.root:
                return None
            path.reverse()
            return path
    path = Path()

    class Window(object):
        def __get__(self, instance, owner):
            if not hasattr(instance, 'session'):
                return None
            return instance.session.windows.get(instance.win_id, None)
    window = Window()
    
    def get_visible(self, path):
        return self.visible and self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id, path)

    def get_widget_by_path(self, path):
        path = Webwidgets.Utils.RelativePath(path)
        res = self
        for i in xrange(0, path.levels):
            res = res.parent
        for name in path.path:
            res = res[name]
        return res

    def get_ansestor_by_attribute(self, *arg, **kw):
        """
        Searches for a ansestor widget with a certain member
        variable, optionally set to a certain value.

        C{get_ansestor_by_attribute(value)}
        C{get_ansestor_by_attribute(name, value)}
        C{get_ansestor_by_attribute(name=SOMENAME, value=SOMEVALUE)}
        C{get_ansestor_by_attribute(value=SOMEVALUE)}

        @param name: The member variable name to search for. Defaults
        to C{"__name__"}.

        @param value: If set, only search for widgets that has the
        variable set to this value.

        @return: An ansestor widget to the current widget.
        """

        if 'name' not in kw:
            kw['name'] = "__name__"

        if arg:
            kw['value'] = arg[-1]
            if len(arg) == 2:
                kw['name'] = arg[0]

        if (    hasattr(self, kw['name'])
            and (   'value' not in kw
                 or getattr(self, kw['name']) == kw['value'])):
            return self
        elif self.parent and hasattr(self.parent, 'get_ansestor_by_attribute'):
            try:
                return self.parent.get_ansestor_by_attribute(**kw)
            except KeyError:
                pass
        raise KeyError("No such parent", self, kw)

    def get_widgets_by_attribute(self, attribute = '__name__', direction_down = True, recursive = True):
	res = {}
	if not direction_down and self.parent:
            if hasattr(self.parent, 'get_widgets_by_attribute'):
                res.update(self.parent.get_widgets_by_attribute(attribute, direction_down, recursive))
        if hasattr(self, attribute):
            res[getattr(self, attribute)] = self
        # FIXME: What is the purpose of this??!?
        elif hasattr(type(self), attribute):
            res[getattr(type(self), attribute)] = self
        return res

    def path_to_subwidget_path(self, path):
        widget_path = self.path
        if not Webwidgets.Utils.is_prefix(widget_path + ['_'], path):
            raise Webwidgets.Constants.NotASubwidgetException('%s: Not a subwidget path %s' % (str(self), path,))
        return path[len(widget_path) + 1:]

    def notify_kw(self, message, args = (), kw = {}, path = None):
        """Enques a message (method name and arguments) for the
        widget. Please see the documentation for
        L{Webwidgets.Program.Program.Session.notify} for more
        information on the message passing mechanism."""        
        self.session.notify(self, message, args, kw, path)

    def append_exception(self):
        """Appends the current exception to the exceptions of this
        widget. This will be shown to the user next to the widget (or
        instead of the widget if this was from the draw method
        crashing).

        Do not ever let exceptions propagate so that they kill of the
        whole page!
        """
        if log_exceptions:
             traceback.print_exc()
        if debug_exceptions:
            # Uggly hack around a bug in pdb (it apparently depends on
            # and old sys-API)
            sys.last_traceback = sys.exc_info()[2]
            pdb.pm()
        self.system_errors.append(
            (sys.exc_info()[1],
             WebUtils.HTMLForException.HTMLForException()))

    def draw_html_attributes(self, path):
        attributes = [(name[5:], getattr(self, name))
                      for name in dir(self)
                      if name.startswith('html_') and name != 'html_attributes']
        return ' '.join(['%s=%s' % (name, xml.sax.saxutils.quoteattr(value))
                         for (name, value)
                         in attributes
                         if value])

    def draw_attributes(self, output_options):
        def get_value_for_key(key):
            def get_value():
                value = getattr(self, key)
                if isinstance(value, (type, types.MethodType)):
                    raise KeyError
                return unicode(value)
            return get_value        
        def get_translated_value_for_key(key):
            def get_value():
                value = getattr(self, key)
                if isinstance(value, (type, types.MethodType)):
                    raise KeyError
                try:
                    return self._(value, output_options)
                except:
                    return unicode(value)
            return get_value

        res = Webwidgets.Utils.OrderedDict()
        for key in dir(self):
            #if key.startswith('_'): continue
            res['ww_untranslated__' + key] = get_value_for_key(key)
            res[key] = get_translated_value_for_key(key)
        return Webwidgets.Utils.LazyDict(res)

    def draw(self, output_options):
        """Renders the widget to HTML. Path is where the full path to
        the widget to render, that is what might go into the id-field
        of an HTML-tag for the widget. Use
        L{Webwidgets.Utils.path_to_id} for this purpose. Any extra
        sub-widget id:s should be constructed by appending an
        underscore followed by any string."""
        self.register_styles(output_options)
        return ''

    def register_styles(self, output_options):
        def calculate_url(**args):
            args['transaction'] = output_options['transaction']
            return self.calculate_url(args, {})
        def calculate_class_url(cls, aspect):
            return calculate_url(widget_class = cls.__module__ + '.' + cls.__name__,
                                 aspect = aspect)
        def calculate_widget_url(slef, aspect):
            return calculate_url(widget = Webwidgets.Utils.path_to_id(self.path),
                                 aspect = aspect)
        def register_class_styles(cls):
            bases = list(cls.__bases__)
            bases.reverse()
            for base in bases:
                register_class_styles(base)
            if cls.__dict__.get('widget_style', None):
                HtmlWindow.register_style_link(self, calculate_class_url(cls, 'style'))
            if cls.__dict__.get('widget_script', None):
                HtmlWindow.register_script_link(self, calculate_class_url(cls, 'script'))
        register_class_styles(type(self))
        if self.__dict__.get('widget_style', None):
            HtmlWindow.register_style_link(self, calculate_widget_url(self, 'style'))
        if self.__dict__.get('widget_script', None):
            HtmlWindow.register_script_link(self, calculate_widget_url(self, 'script'))

    def class_output_style(cls, session, arguments, output_options):
        return cls.widget_style
    class_output_style = classmethod(class_output_style)

    def output_style(self, output_options):
        return self.widget_style

    def class_output_script(cls, session, arguments, output_options):
        return cls.widget_script
    class_output_script = classmethod(class_output_script)

    def output_script(self, output_options):
        return self.widget_script

    def get_title(self, path):
        if self.title is not None:
            return self.title
        return Webwidgets.Utils.path_to_id(path)

    def calculate_url(self, output_options, arguments = None):
        output_options = dict(output_options)
        location, new_arguments = self.session.generate_arguments(
            self.session.get_window(self.win_id, output_options))
        if arguments is None:
            arguments = new_arguments
        if 'win_id' not in output_options:
            output_options['win_id'] = self.win_id
        if 'location' not in output_options:
            output_options['location'] = location
        return self.session.calculate_url(output_options,
                                         arguments)
        
    def validate(self):
        """Validate the state of the widget and any child widgets
        created by previous user input. Returns True or False. Widgets
        that return False shoudl try to display some kind of error
        message to the user detailing the reasons for the validation
        failure.

        Run all validate_ methods on ourselves stopping on the first
        returning False, setting self.error to the value of the member
        variable with the same suffix and the prefix invalid_, if such
        a variable exists. If it does not, self.error is set to the
        name of the method without the validate_ prefix.

        @return: True if all validations returned True, else False.
        """
        validated = False
        for method in dir(self):
            if not method.startswith('validate_'):
                continue
            validated = True

            if not getattr(self, method)():
                validate_name = method[len('validate_'):]
                self.error = getattr(self, 'invalid_' + validate_name, validate_name)
                return False

        # Clear error message if validation routine was run
        # successful, do not clear if there is no validation
        if validated:
            self.error = None

        return True
    
    def get_languages(self, output_options):
        def parse_languages(languages):
            return tuple([item.split(';')[0]
                          for item in languages.split(',')])
        
        if 'languages' in output_options:
            return parse_languages(output_options['languages'])
        if self.window is not None:
            if self.window.languages is not None:
                return self.window.languages
        if hasattr(self, 'session'):
            if self.session.languages is not None:
                return self.session.languages
            try:
                return parse_languages(output_options['transaction'].request().environ().get('HTTP_ACCEPT_LANGUAGE', 'en'))
            except:
                return 'en'

        return ()

    def _get_translations(cls, languages, fallback = False):
        if '__translations__' not in cls.__dict__: cls.__translations__ = {}
        if languages not in cls.__translations__:
            obj = Webwidgets.Utils.Gettext.NullTranslations()
            for base in cls.__bases__:
                if hasattr(base, '_get_translations'):
                    obj = base._get_translations(languages, fallback = obj)
            module = sys.modules[cls.__module__]
            if hasattr(module, '__file__'):
                localedir = os.path.splitext(module.__file__)[0] + '.translations'
                obj = Webwidgets.Utils.Gettext.translation(
                    domain = "Webwidgets",
                    localedir = localedir,
                    languages = languages,
                    fallback = obj)

            cls.__translations__[languages] = obj
        return cls.__translations__[languages]
    _get_translations = classmethod(_get_translations)

    def get_translations(self, output_options, languages = None):
        if languages is None:
            languages = self.get_languages(output_options)
        return self._get_translations(languages)

    def _(self, message, output_options):
        # Optimize a bit...
        if isinstance(message, (types.IntType, types.FloatType,
                                types.BooleanType, types.NoneType,
                                types.DictType, types.TupleType, types.ListType)):
            return str(message)
        try:
            return self.get_translations(output_options)._(message)
        except TypeError, e:
            e.args = (self, str(message)) + e.args
            raise e
        
    def __unicode__(self):
        class_path = type(self).__module__
        if getattr(type(self), 'ww_class_path', ''):
            class_path += '.' + type(self).ww_class_path
        class_path += '.' + type(self).__name__
        return "<%(class_path)s/%(path)s at %(id)s>" % {'class_path': class_path,
                                                        'path': Webwidgets.Utils.path_to_id(self.path, accept_None = True),
                                                        'id': id(self)}

    def __add__(self, other):
        return self.get_widget_by_path(other)

class Text(Widget):
    """This widget is a simple string output widget.

    @cvar html: The "html" attribute should contain HTML code.
    """

    __wwml_html_override__ = True
    """Let Wwml-defined subww_classes override the html attribute"""

    html = ""

    def draw(self, output_options):
        return self._(self.ww_filter.html, output_options)

class BaseChildNodes(object):
    def __init__(self, node):
        self.node = node

    def class_child_to_widget(self, cls):
        return cls(self.node.session, self.node.win_id)

    def ensure(self):
        for name, value in self.iteritems():
            if isinstance(value, type) and issubclass(value, Widget):
                value = self[name] = self.class_child_to_widget(value)
            if isinstance(value, Widget):
                if self.node is value:
                    raise Exception("Object's parent set to itself!", value)
                
                value.parent = self.node
                value.name = name

class BaseChildNodeDict(BaseChildNodes):
    def __setitem__(self, *arg, **kw):
        super(BaseChildNodeDict, self).__setitem__(*arg, **kw)
        self.ensure()

    def update(self, *arg, **kw):
        super(BaseChildNodeDict, self).update(*arg, **kw)
        self.ensure()

    def setdefault(self, *arg, **kw):
        super(BaseChildNodeDict, self).setdefault(*arg, **kw)
        self.ensure()

class ChildNodeDict(BaseChildNodeDict, Webwidgets.Utils.OrderedDict):
    """Dictionary of child widgets to a widget; any widgets inserted
    in the dictionary will automatically have their name and parent
    member variables set correctly."""
    def __init__(self, node, *arg, **kw):
        """@param node: The widget the children held in this
        dictinary are children to.
        @param arg: Sent to L{dict.__init__}
        @param kw: Sent to L{dict.__init__}
        """
        BaseChildNodeDict.__init__(self, node)
        Webwidgets.Utils.OrderedDict.__init__(self, *arg, **kw)

class WeakChildNodeDict(BaseChildNodeDict, Webwidgets.Utils.WeakValueOrderedDict):
    """Like ChildNodeDict but the dirctionbary only keeps a weak
    reference to the children; this should be used to track/cache
    children that are really stored in some other structure.."""
    def __init__(self, node, *arg, **kw):
        """@param node: The widget the children held in this
        dictinary are children to.
        @param arg: Sent to L{dict.__init__}
        @param kw: Sent to L{dict.__init__}
        """
        self.class_children = weakref.WeakKeyDictionary()
        BaseChildNodeDict.__init__(self, node)
        Webwidgets.Utils.WeakValueOrderedDict.__init__(self, *arg, **kw)

    def class_child_to_widget(self, cls):
        widget = BaseChildNodeDict.class_child_to_widget(self, cls)
        self.class_children[cls] = widget
        return widget

class ChildNodeList(BaseChildNodes, list):
    """List of child widgets to a widget; any widgets inserted in the
    list will automatically have their name and parent member
    variables set correctly, the name being the index in the list."""
    def __init__(self, node, *arg, **kw):
        """@param node: The widget the children held in this
        list are children to.
        @param arg: Sent to L{list.__init__}
        @param kw: Sent to L{list.__init__}
        """
        BaseChildNodes.__init__(self, node)
        self.extend(*arg, **kw)
    
    def iteritems(self):
        for index, value in enumerate(self):
            yield (str(index), value)

    def iterkeys(self):
        for index in xrange(0, len(self)):
            yield str(index)

    def __getitem__(self, name):
        if isinstance(name, (str, unicode)): name = int(name)
        return super(ChildNodeList, self).__getitem__(name)

    def __setitem__(self, name, value):
        if isinstance(name, (str, unicode)): name = int(name)
        super(ChildNodeList, self).__setitem__(name, value)
        self.ensure()

    def __delitem__(self, name):
        if isinstance(name, (str, unicode)): name = int(name)
        super(ChildNodeList, self).__delitem__(name)
        self.ensure()

    def extend(self, *arg, **kw):
        super(ChildNodeList, self).extend(*arg, **kw)
        self.ensure()

    def append(self, *arg, **kw):
        super(ChildNodeList, self).append(*arg, **kw)
        self.ensure()

    def insert(self, *arg, **kw):
        super(ChildNodeList, self).insert(*arg, **kw)
        self.ensure()

    def reverse(self, *arg, **kw):
        super(ChildNodeList, self).reverse(*arg, **kw)
        self.ensure()
    
    def sort(self, *arg, **kw):
        super(ChildNodeList, self).sort(*arg, **kw)
        self.ensure()

class Composite(Widget):
    """Base class for all composite widgets, handling the drawing of
    children and the visibility attribute of children."""
    ww_class_data__no_classes_name = True

    system_error_format = """<div class="system-error click-expand">
                              <div class="header">%(exception)s</div>
                              <div class="content">
                               %(traceback)s
                              </div>
                             </div>"""

    system_errors_format = """<div class="system-errors click-expand">

                               <div class="header">Sorry, an error
                               occured.<br />
                               You can try to log out and
                               back in again to solve this.
                               <div class="sub-header">Read more...</div>
                               </div>

                               <div class="content">
                                <p>This part of the application has
                                crashed. You can try to log out and
                                log in again to remedy the problem. In
                                any case, please contact the system
                                administrator about this issue and
                                tell him/her the steps you took that
                                lead up to this issue and he/she will
                                try to fix the problem as fast as
                                possible.</p>

                                <p>A more technical, detailed
                                description of the error follows
                                (click on the items to expand):</p>

                                %(tracebacks)s
                               </div>
                              </div>"""


    def __init__(self, session, win_id, **attrs):
        super(Composite, self).__init__(
            session, win_id, **attrs)

    def draw_child(self, path, child, output_options, invisible_as_empty = False):
        """Renders a child widget to HTML using its draw() method.
        Also handles visibility of the child: if invisible_as_empty is
        False, rendering an invisible child will yeild None, otherwize
        it will yield the empty string."""
        if isinstance(child, Widget):
            visible = child.get_visible(path)
        else:
            visible = self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id, path)

        if visible:
            if isinstance(child, Widget):
                try:
                    result = child.draw(output_options)
                except Exception, e:
                    result = ''
                    child.append_exception()
            elif isinstance(child, type) and issubclass(child, Widget):
                raise Exception("The child %(child)s to %(self)s is a class, not an instance" % {
                    'child': Webwidgets.Utils.obj_info(child),
                    'self': Webwidgets.Utils.obj_info(self)})
            else:
                result = self._(child, output_options)
        else:
            result = [None, ''][invisible_as_empty]

        if result is not None and getattr(child, 'system_errors', []):
            HtmlWindow.register_header(self, "Status", "500 Application exception cought")
            system_error_format = self._(self.system_error_format, output_options)
            system_errors_format = self._(self.system_errors_format, output_options)
            errors = [system_error_format % {'exception': cgi.escape(Webwidgets.Utils.convert_to_str_any_way_possible(error[0])),
                                             'traceback': Webwidgets.Utils.convert_to_str_any_way_possible(error[1])}
                      for error in child.system_errors]
            result = system_errors_format % {'tracebacks': '\n'.join(errors)} + result
            del child.system_errors[:]

        if 'internal' in output_options and 'draw_wrapper' in output_options['internal']:
            result = output_options['internal']['draw_wrapper'](
                self, path, child, visible, result, output_options, invisible_as_empty)
        return result

    def draw_children(self, output_options, invisible_as_empty = False, include_attributes = False):
        """Renders all child widgets to HTML using their draw methods.
        Also handles visibility of the children - invisible children
        are not included in the output.

        @return: dictionary of child_names and HTML for the respective
                 children.
        """
        
        if include_attributes:
            res = self.draw_attributes(output_options)
        else:
            res = Webwidgets.Utils.LazyDict(Webwidgets.Utils.OrderedDict())

        def get_value_for_name_and_child(name, child):
            def get_value():
                res = self.draw_child(self.path + [name], child, output_options, invisible_as_empty)
                if res is None:
                    raise KeyError
                return res
            return get_value
        
        for name, child in self.get_children():
            res[name] = get_value_for_name_and_child(name, child)
        
        return res

    def get_children(self):
        """@return: a dictionary of child widget names and their
        respective widgets.
        """
        raise NotImplemented

    def get_child(self, name):
        """@return: a child widget."""
        raise NotImplemented

    def validate(self):
        """Validate all child widgets. Returns True only if all of
        them returns True."""
        res = Widget.validate(self)
        for name, child in self.get_children():
            if hasattr(child, "validate"):                
                res = child.validate() and res
        return res

    def get_widgets_by_attribute(self, attribute = '__name__', direction_down = True, recursive = True):
        fields = Widget.get_widgets_by_attribute(self, attribute, direction_down, recursive)
        if direction_down and (recursive or not fields):
            for name, child in self:
                if isinstance(child, Widget):
                    fields.update(child.get_widgets_by_attribute(attribute, direction_down, recursive))
        return fields

    def get(self, name, default = None):
        """@return: a child widget."""
        try:
            return self.get_child(name)
        except KeyError:
            return default
        
    def __getitem__(self, name):
        """@return: a child widget."""
        return self.get_child(name)

    def __contains__(self, name):
        try:
            self.get_child(name)
            return True
        except:
            return False
        
    def __iter__(self):
        return self.get_children()

class DictComposite(Composite):
    ww_class_data__no_classes_name = True

    ChildNodeDict = ChildNodeDict
    
    def __init__(self, session, win_id, **attrs):
        super(DictComposite, self).__init__(
            session, win_id, **attrs)
        self.children = self.ChildNodeDict(self, getattr(self, 'children', {}))

    def get_children(self):
        return self.children.iteritems()

    def get_child(self, name):
        try:
            return self.children[name]
        except:
            try:
                e = sys.exc_info()
                raise KeyError, ("No such child %s to %s" % (name, str(self)), e[1]), e[2]
            finally:
                del e

    def __setitem__(self, name, value):
        """Adds a new child widget"""
        self.children[name] = value

    def __delitem__(self, name):
        """Deletes a child widget"""
        del self.children[name]

class CachingComposite(DictComposite):
    """Only keeps week references to the children - if any child is
    not referenced by some other part of the code, it is silently
    removed."""
    ww_class_data__no_classes_name = True
    ChildNodeDict = WeakChildNodeDict
    
class StaticComposite(DictComposite):
    """Base class for all composite widgets, handling child class
    instantiation, drawing of children and the visibility attribute of
    children.

    When instantiated, any class variables holding widget instances
    are added to the instance member variable L{children}. In
    addition, any class variables holding widget ww_classes (that do not
    have L{ww_explicit_load} set to False) are instantiated
    automatically and then added to L{children}.
    """

    ww_class_data__no_classes_name = True
    
    def __init__(self, session, win_id, **attrs):
        super(StaticComposite, self).__init__(
            session, win_id, **attrs)

        # Class members have no intrinsic order, so we sort them on
        # their order of creation, which if created through the Python
        # class statement, is the same as their textual order :)
        
        child_classes = []
        for name in dir(self):
            if name in ('__class__', 'parent', 'window'): continue
            value = getattr(self, name)
            if isinstance(value, type) and issubclass(value, Widget) and not value.__dict__.get('ww_explicit_load', False):
                child_classes.append((name, value))
                
        child_classes.sort(lambda x, y: cmp(x[1].ww_class_order_nr, y[1].ww_class_order_nr))
        
        for (name, value) in child_classes:
            self.children[name] = value(session, win_id)

class Input(Widget):
    """Base class for all input widgets, providing input field registration"""
    class __metaclass__(Widget.__metaclass__):
        debug_input_order = False
        
        def __new__(cls, name, bases, members):
            subordinates = set()
            dominants = set()
            if '__input_subordinates__' in members:
                subordinates = subordinates.union(set(members['__input_subordinates__']))
            if '__input_dominants__' in members:
                dominants = dominants.union(set(members['__input_dominants__']))
            for base in bases:
                if hasattr(base, '__input_subordinates__'):
                    subordinates = subordinates.union(base.__input_subordinates__)
                if hasattr(base, '__input_dominants__'):
                    dominants = dominants.union(base.__input_dominants__)
            members['_input_level'] = max([0] + [sub._input_level
                                                for sub in subordinates]) + 1
            # FIXME: This does _not_ find descendants of dominants, so it does not work. At all.
            def raise_dominants(dominants, input_level):
                for dom in dominants:
                    if dom._input_level <= input_level:
                        dom._input_level = input_level + 1
                        raise_dominants(dom.__input_dominants__, dom._input_level)
            raise_dominants(dominants, members['_input_level'])
            members['__input_subordinates__'] = subordinates
            members['__input_dominants__'] = dominants

            if cls.debug_input_order:
                print "Registering input widget:", name
                print "    Subordinates:", ', '.join([sub.__name__ for sub in subordinates])
                print "    Dominants:", ', '.join([sub.__name__ for sub in dominants])
                print "    Level:", members['_input_level']
            
            return Widget.__metaclass__.__new__(cls, name, bases, members)

    def input_order(cls, other):
        if isinstance(other, Input):
            other = type(other)
        return cmp(cls._input_level, other._input_level) or cmp(cls, other) or cmp(id(cls), id(other))
    input_order = classmethod(input_order)

    active = True
    """Enables the user to actually use this input field."""

    argument_name = None
    """'Publishes' the value of this input field as a parameter in the
    URL to the page if set to non-None.

    Beware: This variable holds the full name used as argument name in
    the URL; that is, it has to be unique for the whole window. This
    name is not auto-prefixed with the path to the widget, like
    everything else. This is very intentional, as this is intended to
    be used to provide readable (and bookmarkable) URLs!
    """

    __input_subordinates__ = ()
    """Other input widgets that should handle simultaneous input from
    the user _before_ this widget."""    

    __input_dominants__ = ()
    """Other input widgets that should handle simultaneous input from
    the user _after_ this widget."""    

    class HtmlClass(Widget.HtmlClass):
        def __get__(self, instance, owner):
            if instance is None:
                return None
            err = ''
            if instance.error:
                err = ' error'
            return Widget.HtmlClass.__get__(self, instance, owner) + err
    html_class = HtmlClass()

    def register_input(self, path = None, argument_name = None, field = True):
        if path is None: path = self.path
        active = self.get_active(path)
        if active:
            if field:
                self.session.windows[self.win_id].fields[Webwidgets.Utils.path_to_id(path)] = self
            if argument_name:
                self.session.windows[self.win_id].arguments[argument_name] = {'widget':self, 'path': path}
        return active

    def field_input(self, path, *string_values):
        raise NotImplementedError(self, "field_input")
    
    def field_output(self, path):
        raise NotImplementedError(self, "field_output")
    
    def draw(self, output_options):
        self.register_input(self.path, self.argument_name)
        return ''

    def get_active(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        return self.ww_filter.active and self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, path)

class ValueInput(Input):
    """Base class for all input widgets that holds some kind of value
    (e.g. all butt buttons). It defines a notification for changing
    the value hold by the widget."""

    class WwModel(Model):
        value = ''

        original_value = ''

        multiple = False
        """Handle multiple values"""

    def reset(self):
        self.ww_filter.value = self.ww_filter.original_value

    def field_input(self, path, *values):
        if not self.multiple:
            values = values[0]
        self.ww_filter.value = values

    def field_output(self, path):
        values = self.ww_filter.value
        if not self.ww_filter.multiple or not isinstance(values, types.ListType):
            values = [values]
        return [unicode(value) for value in values]

    def value_changed(self, path, value):
        """This notification is sent to notify the widget that its value,
        as entered by the user, has changed. If you override this,
        make sure to call the base class implementation, as the value
        will be reset otherwise."""
        if path != self.path: return
        self.ww_filter.error = None

    def __cmp__(self, other):
        return cmp(self.ww_filter.value, other)

class MixedInput(Input):
    """Base class for composiute input widgets that fires
    notifications and hold values."""

    __input_subordinates__ = (ValueInput,)

    def field_output(self, path):
        return []

class ActionInput(MixedInput):
    """Base class for all input widgets that only fires some
    notification and don't hold a value of some kind."""

    __input_subordinates__ = (MixedInput,)

class SingleActionInput(ActionInput):
    """Base class for all input widgets that only fires a single
    notification with no parameters."""

    __input_subordinates__ = (ValueInput,)

    def field_input(self, path, string_value):
        if string_value != '':
            self.notify('clicked')

    def clicked(self, path):
        if path != self.path: return
        return

class MultipleActionInput(ActionInput):
    """Base class for all input widgets that can fire any of a set of
    notifications."""

    __input_subordinates__ = (ValueInput,)

    def field_input(self, path, string_value):
        if string_value != '':
            self.notify('selected', string_value)

    def selected(self, path, value):
        if path != self.path: return
        return

class DirectoryServer(Widget):
    """Mix-in class that adds a L{class_output} that serves files from
    a directory named the same as the current python module, but with
    the C{.py} replaces by C{.scripts}."""
    ww_class_data__no_classes_name = True

    class BaseDirectory(object):
        def __get__(self, instance, owner):
            return Webwidgets.Utils.module_file_path(owner.__module__)
    base_directory = BaseDirectory()
    
    def class_output(cls, session, arguments, output_options):
        path = output_options['location']
        for item in path:
            assert item != '..'

        ext = os.path.splitext(path[-1])[1][1:]
        file = open(os.path.join(cls.base_directory,
                                 *path))
        try:
            return {Webwidgets.Constants.FINAL_OUTPUT: file.read(),
                    'Content-type': Webwidgets.Utils.FileHandling.extension_to_mime_type[ext],
                    'Cache-Control': 'public; max-age=3600'
                    }
        finally:
            file.close()
    class_output = classmethod(class_output)

    def calculate_url_to_directory_server(self, widget_class, location, output_options):
        """Calculates a URL to a file in the directory served by this class.

        @param widget_class: The python path to this widget class.

        @param location: A python list of path components of the path
        relative to the .scripts-directory to the file to serve. E.g.
        C{['css-files', 'main.css']}.
        """
        
        return self.calculate_url({'transaction': output_options['transaction'],
                                   'widget_class': widget_class,
                                   'location': location},
                                  {})

class Window(Widget):
    """Window is the main widget and should allways be the top-level
    widget of any application. It has an attribute for the HTTP
    headers and handles form submission values and URL arguments."""

    headers = {'Status': '404 Page not implemented'}
    languages = None

    root = True
    path = []
    
    def __init__(self, session, win_id, **attrs):
        super(Window, self).__init__(session, win_id, **attrs)
        self.fields = {}
        self.arguments = {}
    def output(self, output_options):
        result = {Webwidgets.Constants.OUTPUT: self.draw(output_options)}
        result.update(self.headers)
        return result

    def draw(self, output_options):
        self.fields = {}
        self.arguments = {}
        return ''


class HtmlWindow(Window, StaticComposite, DirectoryServer):
    """HtmlWindow is the main widget for any normal application window
    displaying HTML. It has two children - head and body aswell as
    attributes for title, encoding and doctype"""

    headers = {'Status': '200 OK'}
    title = 'Page not available'
    Head = Text.derive(html = '')
    Body = Text.derive(html = 'Page not available')
    encoding = 'UTF-8'
    doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'

    findallvalues = re.compile(
        r"""(id=["']([^"'<>]*)["'][^<>]*value=["']([^"'<>]*)["'])|(value=["']([^"'<>]*)["'][^<>]*id=["']([^"'<>]*)["'])""",
        re.MULTILINE)

    def output(self, output_options):
        result = Window.output(self, output_options)
        result['Content-Type'] = 'text/html; charset=%(encoding)s' % {'encoding': self.encoding}
        return result

    def draw(self, output_options, body = None, title = None):
        Window.draw(self, output_options)
        self.headers = {}
        self.head_content = Webwidgets.Utils.OrderedDict()
        self.replaced_content = Webwidgets.Utils.OrderedDict()

        HtmlWindow.register_style_link(
            self,
            self.calculate_url_to_directory_server('Webwidgets.HtmlWindow',
                                                   ['Widgets.css'],
                                                   output_options))
        HtmlWindow.register_script_link(
            self,
            self.calculate_url_to_directory_server('Webwidgets.HtmlWindow',
                                                   ['Widgets.js'],
                                                   output_options))
        #self.register_styles(output_options)

        result = self.draw_children(
            output_options,
            invisible_as_empty = True,
            include_attributes = True)

        result.update(self.headers)
        
        if body is not None:
            result['Body'] = body
        if title is None: title = self.get_title(self.path)
        result['title'] = '<title>' + title + '</title>'
        result['doctype'] = self.doctype
        result['ww_untranslated__uri'] = cgi.escape(output_options['transaction'].request()._environ['REQUEST_URI'])
        result['ww_untranslated__base'] = self.session.program.request_base(output_options['transaction'])

        for (all1, name1, value1, all2, value2, name2) in self.findallvalues.findall(result['Body']):
            HtmlWindow.register_value(self, 'field_value' + '_' + (name1 or name2), (value1 or value2))

        result['ww_untranslated__head_content'] = '\n'.join(self.head_content.values())
        result['ww_untranslated__replaced_content'] = '\n'.join(self.replaced_content.values())

        return ("""
%(doctype)s
<html xmlns="http://www.w3.org/1999/xhtml">
 <head>
  <base href='%(ww_untranslated__base)s' />
  %(ww_untranslated__head_content)s
  %(title)s
  %(Head)s
 </head>
 <body %(ww_untranslated__html_attributes)s>
  <form name="%(ww_untranslated__html_id)s" method='post' enctype='multipart/form-data' action='%(ww_untranslated__uri)s' id="%(ww_untranslated__html_id)s-_-body-form">
   %(ww_untranslated__replaced_content)s
   %(Body)s
  </form>
 </body>
</html>""" % result).encode(self.encoding)

    def register_header(cls, widget, name, value):
        widget.session.windows[widget.win_id].headers[name] = value
    register_header = classmethod(register_header)

    def register_head_content(cls, widget, content, content_name):
        content_name = content_name or Webwidgets.Utils.path_to_id(widget.path)
        widget.session.windows[widget.win_id].head_content[content_name] = content
    register_head_content = classmethod(register_head_content)
   
    def register_replaced_content(cls, widget, content, content_name = None):
        content_name = content_name or Webwidgets.Utils.path_to_id(widget.path)
        widget.session.windows[widget.win_id].replaced_content[content_name] = content
    register_replaced_content = classmethod(register_replaced_content)

    def register_script_link(cls, widget, *uris):
        cls.register_head_content(
            widget,
            '\n'.join(["<script src='%s' type='text/javascript' ></script>" % (cgi.escape(uri),)
                       for uri in uris]),
            'script: ' + ' '.join(uris))
    register_script_link = classmethod(register_script_link)
        
    def register_style_link(cls, widget, *uris):
        cls.register_head_content(
            widget,
            '\n'.join(["<link href='%s' rel='stylesheet' type='text/css' />" % (cgi.escape(uri),)
                       for uri in uris]),
            'style: ' + ' '.join(uris))
    register_style_link = classmethod(register_style_link)
    
    def register_script(cls, widget, name, script):
        cls.register_head_content(
            widget,
            "<script language='javascript' type='text/javascript'>%s</script>" % (script,),
            name)
    register_script = classmethod(register_script)
        
    def register_style(cls, widget, name, style):
        cls.register_head_content(
            widget,
            "<style type='text/css'>%s</style>" % (style,),
            name)
    register_style = classmethod(register_style)

    def register_submit_action(cls, widget, path, event):
        info = {'id': Webwidgets.Utils.path_to_id(path),
                'event': event}
        cls.register_script(
            widget,
            'submit_action: %(id)s: %(event)s' % info,
            """
            webwidgets_add_event_handler_once_loaded(
             '%(id)s',
             '%(event)s',
             'webwidgets_submit_action',
             function () {
              webwidgets_submit_button_iefix();
              document.getElementById('root-_-body-form').submit();
             });
            """ % info)
    register_submit_action = classmethod(register_submit_action)

    def register_value(cls, widget, name, value):
        cls.register_head_content(
            widget,
            """<script language="javascript" type='text/javascript'>webwidgets_values['%(name)s'] = '%(value)s';</script>""" % {
                'name': name,
                'value': value},
            'value: ' + name)
    register_value = classmethod(register_value)
