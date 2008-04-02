#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

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
import traceback

debug_exceptions = True
                        
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
            if key.startswith('class_data_'):
                members['ww_class_data'][key[len('class_data_'):]] = members[key]
                del members[key]

        members['ww_classes'] = []
        if not members['ww_class_data'].get('ww_class_data__no_classes_name', False):
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
        if not self.ww_class_data.get('ww_class_data__no_classes_name', False):
            self.ww_classes[0] = Webwidgets.Utils.class_full_name(self)

class Object(object):
    """Object is a more elaborate version of object, providing a few
    extra utility methods, some extra"magic" class attributes -
    L{ww_classes}, L{ww_class_order_nr} and L{ww_class_path} and
    model/model-filter handling."""
    
    __metaclass__ = Type

    ww_class_data__no_classes_name = False
    """Do not include the name of this particular class in L{ww_classes}
    for subww_classes of this class (and for this class itself)."""

    ww_classes = ("Webwidgets.Widget",)
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
                       tree/chain. None for the root node, next filter
                       in chain otherwise.
        @param attrs: Any attributes to set for the object.
        """
        if "ww_model" in attrs:
            self.ww_model = attrs.pop('ww_model')
        if self.ww_model is None and self.WwModel is not None:
            self.ww_model = self.WwModel()
        self.__dict__.update(attrs)
        self.setup_filter()

    def setup_filter(self, name = 'ww_filter', ww_filter_classes = None, ww_filter = None, object = None):
        if ww_filter is None: ww_filter = self.__dict__.get(name, self)
        if object is None: object = self.__dict__.get('object', self)
        if ww_filter_classes is None: ww_filter_classes = self.WwFilters
        for filter_class in reversed(ww_filter_classes):
            if isinstance(filter_class, (str, unicode)):
                filter_class = getattr(self, filter_class)
            ww_filter = filter_class(ww_filter = ww_filter, object = object)
        setattr(self, name, ww_filter) 

    def derive(cls, name = None, **members):
        return types.TypeType(name or 'anonymous', (cls,), members)
    derive = classmethod(derive)

    def __getattr__(self, name):
        if self.ww_model is None:
            raise AttributeError(self, name)
        return getattr(self.ww_model, name)
        
    def __hasattr__(self, name):
        return name in self.__dict__ or self.ww_model is not None and hasattr(self.ww_model, name)

    def __setattr__(self, name, value):
        if (   self.ww_model is None
            or name in self.__dict__
            or not hasattr(self.ww_model, name)):
            object.__setattr__(self, name, value)
        else:
            setattr(self.ww_model, name, value)

    def __unicode__(self):
        return object.__repr__(self)
        
    def __str__(self):
        return str(unicode(self))

    def __repr__(self):
        return str(self)

class Wrapper(Object):
    def __init__(self, ww_model, **attrs):
        Object.__init__(self, ww_model, ww_filter = getattr(ww_model, 'ww_filter', None), **attrs)

class PersistentWrapper(Wrapper):
    def __new__(cls, ww_model, **attrs):
        if 'wrappers' not in cls.__dict__:
                cls.wrappers = {}
        if id(ww_model) not in cls.wrappers:
            cls.wrappers[id(ww_model)] = Object.__new__(cls, ww_model, **attrs)
        else:
            cls.wrappers[id(ww_model)].__dict__.update(attrs)
        return cls.wrappers[id(ww_model)]

class Model(Object):
    pass

class Filter(Object):
    def __getattr__(self, name):
        return getattr(self.ww_filter, name)
    
    def __hasattr__(self, name):
        return name in self.__dict__ or hasattr(self.ww_filter, name)

    def __setattr__(self, name, value):
        if (   name in self.__dict__
            or not hasattr(self.ww_filter, name)):
            object.__setattr__(self, name, value)
        else:
            setattr(self.ww_filter, name, value)
        
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
        
        self.session = session
        self.win_id = win_id
        self.system_errors = []
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

    def get_widgets_by_attribute(self, attribute = '__name__', direction_down = True):
	res = {}
	if not direction_down and self.parent:
            if hasattr(self.parent, 'get_widgets_by_attribute'):
                res.update(self.parent.get_widgets_by_attribute(attribute, False))
        if hasattr(self, attribute):
            res[getattr(self, attribute)] = self
        elif hasattr(type(self), attribute):
            res[getattr(type(self), attribute)] = self
        return res

    def path_to_subwidget_path(self, path):
        widget_path = self.path
        if not Webwidgets.Utils.is_prefix(widget_path + ['_'], path):
            raise Webwidgets.Constants.NotASubwidgetException('%s: Not a subwidget path %s' % (str(self), path,))
        return path[len(widget_path) + 1:]

    def notify(self, message, *args, **kw):
        """See L{notify_kw}."""
        self.notify_kw(message, args, kw)

    def notify_kw(self, message, args = (), kw = {}, path = None):
        """Enques a message (method name and arguments) for the
        widget. Please see the documentation for
        L{Webwidgets.Program.Program.Session.notify} for more
        information on the message passing mechanism."""        
        self.session.notify(self, message, args, kw, path)

    def draw_html_attributes(self, path):
        attributes = [(name[5:], getattr(self, name))
                      for name in dir(self)
                      if name.startswith('html_') and name != 'html_attributes']
        return ' '.join(['%s=%s' % (name, xml.sax.saxutils.quoteattr(value))
                         for (name, value)
                         in attributes
                         if value])

    def draw_attributes(self, output_options):
        res = Webwidgets.Utils.OrderedDict()
        for key in dir(self):
            #if key.startswith('_'): continue
            value = getattr(self, key)
            if isinstance(value, (type, types.MethodType)): continue
	    res[key] = res['ww_untranslated__' + key] = unicode(value)
            try:
                res[key] = self._(value, output_options)
            except:
                pass
        return res

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
        cls = type(self)
        def register_class_styles(cls):
            bases = list(cls.__bases__)
            bases.reverse()
            for base in bases:
                register_class_styles(base)
            if cls.__dict__.get('widget_style', None):
                self.register_style_link(self.calculate_url({'widget_class': cls.__module__ + '.' + cls.__name__,
                                                          'aspect': 'style'},
                                                         {}))
            if cls.__dict__.get('widget_script', None):
                self.register_script_link(self.calculate_url({'widget_class': cls.__module__ + '.' + cls.__name__,
                                                           'aspect': 'script'},
                                                          {}))
        register_class_styles(cls)
        if self.__dict__.get('widget_style', None):
            self.register_style_link(self.calculate_url({'widget': Webwidgets.Utils.path_to_id(self.path),
                                                      'aspect': 'style'},
                                                     {}))
        if self.__dict__.get('widget_script', None):
            self.register_script_link(self.calculate_url({'widget': Webwidgets.Utils.path_to_id(self.path),
                                                       'aspect': 'script'},
                                                      {}))

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

    def register_head_content(self, content_name, content):        
        self.session.windows[self.win_id].head_content[content_name] = content

    def register_script_link(self, *uris):
        content_name = 'script: ' + ' '.join(uris)
        self.register_head_content(
            content_name,
            '\n'.join(["<script src='%s' type='text/javascript' ></script>" % (cgi.escape(uri),)
                       for uri in uris]))
        
    def register_style_link(self, *uris):
        content_name = 'style: ' + ' '.join(uris)
        self.register_head_content(
            content_name,
            '\n'.join(["<link href='%s' rel='stylesheet' type='text/css' />" % (cgi.escape(uri),)
                       for uri in uris]))

    def register_script(self, name, script):
        self.register_head_content(
            name,
            "<script language='javascript' type='text/javascript'>%s</script>" % (script,))

    def register_style(self, name, style):
        self.register_head_content(
            name,
            "<style type='text/css'>%s</style>" % (style,))

    def register_submit_action(self, path, event):
        info = {'id': Webwidgets.Utils.path_to_id(path),
                'event': event}
        self.register_script('submit_action: %(id)s: %(event)s' % info,
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

    def register_value(self, name, value):
        self.register_head_content('value: ' + name,
                                 """<script language="javascript" type='text/javascript'>webwidgets_values['%(name)s'] = '%(value)s';</script>""" % {'name': name,
                                                                                                                              'value': value})

    def calculate_url(self, output_options, arguments = None):
        output_options = dict(output_options)
        location, new_arguments = self.session.generate_arguments(
            self.session.get_window(self.win_id))
        if arguments is None:
            arguments = new_arguments
        if 'win_id' not in output_options:
            output_options['win_id'] = self.win_id
        if 'location' not in output_options:
            output_options['location'] = location
        return self.session.calculate_url(output_options,
                                         arguments)
        
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
                return parse_languages(self.session.program.request().environ().get('HTTP_ACCEPT_LANGUAGE', 'en'))
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

    def __setattr__(self, name, value):
        if not hasattr(self, name) or value is not getattr(self, name):
            object.__setattr__(self, name, value)    
            self.notify('%s_changed' % name, value)

class Text(Widget):
    """This widget is a simple string output widget.

    @cvar html: The "html" attribute should contain HTML code.
    """

    __wwml_html_override__ = True
    """Let Wwml-defined subww_classes override the html attribute"""

    html = ""

    def draw(self, output_options):
        return self._(self.html, output_options)

class BaseChildNodes(object):
    def __init__(self, node):
        self.node = node

    def class_child_to_widget(self, cls):
        return cls(self.node.session, self.node.win_id)

    def ensure(self):
        for name in self.iterkeys():
            value = self[name]
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

    system_error_format = """<div class="system-error hover-expand">
                              <div class="header">%(exception)s</div>
                              <div class="content">
                               %(traceback)s
                              </div>
                             </div>"""

    system_errors_format = """<div class="system-errors click-expand">
                               <div class="header">Error</div>
                               <div class="content">
                                This widget caused errors:
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
                    if debug_exceptions: traceback.print_exc()
                    result = ''
                    import WebUtils.HTMLForException
                    child.system_errors.append(
                        (sys.exc_info()[1],
                         WebUtils.HTMLForException.HTMLForException()))
            elif isinstance(child, type) and issubclass(child, Widget):
                raise Exception("The child %(child)s to %(self)s is a class, not an instance" % {
                    'child': Webwidgets.Utils.obj_info(child),
                    'self': Webwidgets.Utils.obj_info(self)})
            else:
                result = self._(child, output_options)
        else:
            result = [None, ''][invisible_as_empty]

        if result is not None and getattr(child, 'system_errors', []):
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
        
        res = Webwidgets.Utils.OrderedDict()

        if include_attributes:
            res.update(self.draw_attributes(output_options))

        for name, child in self.get_children():
            child = self.draw_child(self.path + [name], child, output_options, invisible_as_empty)
            if child is not None:
                res[name] = child

        return res

    def get_children(self):
        """@return: a dictionary of child widget names and their
        respective widgets.
        """
        raise NotImplemented

    def get_child(self, name):
        """@return: a child widget."""
        raise NotImplemented

    def get_widgets_by_attribute(self, attribute = '__name__', direction_down = True):
        fields = Widget.get_widgets_by_attribute(self, attribute, direction_down)
        if direction_down:
            for name, child in self:
                if isinstance(child, Widget):
                    fields.update(child.get_widgets_by_attribute(attribute))
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
            if isinstance(value, type) and issubclass(value, Widget) and not value.ww_explicit_load:
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

    error = None
    """Displayed by a corresponding L{Label} if set to non-None.
    See that widget for further information."""

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
        return self.active and self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, path)

class ValueInput(Input):
    """Base class for all input widgets that holds some kind of value
    (e.g. all butt buttons). It defines a notification for changing
    the value hold by the widget."""

    original_value = ''
    
    value = ''

    multiple = False
    """Handle multiple values"""

    def reset(self):
        self.value = self.original_value

    def field_input(self, path, *values):
        if not self.multiple:
            values = values[0]
        self.value = values

    def field_output(self, path):
        values = self.value
        if not self.multiple or not isinstance(values, types.ListType):
            values = [values]
        return [unicode(value) for value in values]

    def value_changed(self, path, value):
        """This notification is sent to notify the widget that its value,
        as entered by the user, has changed. If you override this,
        make sure to call the base class implementation, as the value
        will be reset otherwise."""
        if path != self.path: return
        self.error = None

    def __cmp__(self, other):
        return cmp(self.value, other)

class ActionInput(Input):
    """Base class for all input widgets that only fires some
    notification and don't hold a value of some kind."""

    __input_subordinates__ = (ValueInput,)

    def field_output(self, path):
        return []

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
    class BaseDirectory(object):
        def __get__(self, instance, owner):
            filePath = sys.modules[owner.__module__].__file__
            return os.path.splitext(filePath)[0] + '.scripts'
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


file = open(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         'Widgets.css'))
generic_style = file.read()
file.close()

file = open(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         'Widgets.js'))
generic_script = file.read()
file.close()

class HtmlWindow(Window, StaticComposite):
    """HtmlWindow is the main widget for any normal application window
    displaying HTML. It has two children - head and body aswell as
    attributes for title, encoding and doctype"""

    headers = {'Status': '200 OK'}
    title = 'Page not available'
    Head = Text.derive(html = '')
    Body = Text.derive(html = 'Page not available')
    encoding = 'UTF-8'
    doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'

    widget_style = {Webwidgets.Constants.FINAL_OUTPUT: generic_style,
                   'Content-type': 'text/css',
                   'Cache-Control': 'public; max-age=3600',
                   }
    widget_script = {Webwidgets.Constants.FINAL_OUTPUT: generic_script,
                   'Content-type': 'application/x-javascript',
                   'Cache-Control': 'public; max-age=3600',
                   }

    findallvalues = re.compile(
        r"""(id=["']([^"'<>]*)["'][^<>]*value=["']([^"'<>]*)["'])|(value=["']([^"'<>]*)["'][^<>]*id=["']([^"'<>]*)["'])""",
        re.MULTILINE)

    def output(self, output_options):
        result = Window.output(self, output_options)
        result['Content-Type'] = 'text/html; charset=%(encoding)s' % {'encoding': self.encoding}
        return result

    def draw(self, output_options, body = None, title = None):
        Window.draw(self, output_options)
        self.head_content = Webwidgets.Utils.OrderedDict()

        self.register_styles(output_options)

        result = self.draw_children(
            output_options,
            invisible_as_empty = True,
            include_attributes = True)

        if body is not None:
            result['Body'] = body
        if title is None: title = self.get_title(self.path)
        result['title'] = '<title>' + title + '</title>'
        result['doctype'] = self.doctype
        result['ww_untranslated__uri'] = cgi.escape(self.session.program.request()._environ['REQUEST_URI'])
        result['ww_untranslated__base'] = self.session.program.request_base()

        for (all1, name1, value1, all2, value2, name2) in self.findallvalues.findall(result['Body']):
            self.register_value('field_value' + '_' + (name1 or name2), (value1 or value2))

        result['ww_untranslated__head_content'] = '\n'.join(self.head_content.values())
        
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
   %(Body)s
  </form>
 </body>
</html>""" % result).encode(self.encoding)
