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

"""Base widgets to define the application user interface.

This module contains a set of base widgets that can be usedv to define
the user-interface of an application. In addition, it contains some
generic base classes that can be used when implementing more elaborate
widgets.
"""

import types, xml.sax.saxutils, os.path, cgi, re, sys
import Webwidgets.Utils, Webwidgets.Utils.Gettext, Webwidgets.Constants
import Webwidgets.Utils.FileHandling
import Webwidgets.Utils.Threads

debugNotifications = False

class Widget(object):
    """Widget is the base class for all widgets. It manages class name
    collection, attribute handling, child instantiation and
    notifications.

    Attributes are special class variables that can also be overridden
    by instance variables set using keyword arguments to L{__init__}..
    Attributes for a class must be listed in the L{__attributes__}
    member.

    The class name collection system gathers the names of all
    base-classes for a class and uses these to construct a string
    suitable for use in an HTML 'class' attribute.

    When a widget is instantiated, any class variables themselves
    holding widget classes (that do not have L{__explicit_load__} set
    to False) are instantiated automatically, and the instances
    assigned to instance variables with the same names.

    See L{Webwidgets.Program.Program.Session.notify} for an
    explanation of notifications.
    """

    __explicit_load__ = False
    """Controls wether the widget class is automatically instantiated
    when the parent widget is instantiated."""

    __attributes__ = ('visible', 'classes', 'title', 'html_attributes')
    """List of all attributes that can be set for the widget using
    either class members or arguments to __init__"""

    __html_attributes__ = ('id', 'class',)

    classes = ("Webwidgets.Widget",)
    """Read-only attribute containing a list of the names of all
    inherited classes except ones with L{__no_classes_name__} set to
    True. This is mainly usefull for automatic CSS class generation."""

    html_class = 'Webwidgets-Widget'
    """Read-only attribute containing the information in L{classes}
    but in a format suitable for inclusion in the 'class' attribute in
    HTML."""

    __no_classes_name__ = False
    """Do not include the name of this particular class in L{classes}
    for subclasses of this class (and for this class itself)."""

    visible = True
    """Whether the widget is shown on screen or not."""

    title = None
    """The (human readable) title for the widget, used for pages,
    items in lists etc. If None, the widget path is used."""

    root = False
    parent = None
    name = None

    class __metaclass__(type):
        class_order_nr = Webwidgets.Utils.Threads.Counter()
        
        def __new__(cls, name, bases, members):
            members = dict(members)
            classes = []

            if '__no_classes_name__' not in members or not members['__no_classes_name__']:
                cls_name = []
                if '__module__' in members:
                    cls_name.append(members['__module__'])
                if '__classPath__' in members and members['__classPath__']:
                    cls_name.append(members['__classPath__'])
                cls_name.append(name)
                classes.append('.'.join(cls_name))
            if '__no_classes_name__' in members:
                del members['__no_classes_name__'] # No inheritance! This is a magic marker, not an attribute
            
            for base in bases:
                if hasattr(base, 'classes'):
                    classes.extend(base.classes)
            members['classes'] = tuple(classes)

            members['class_order_nr'] = cls.class_order_nr.next()

            return type.__new__(cls, name, bases, members)

    def derive(cls, name = None, **members):
        return types.TypeType(name or 'anonymous', (cls,), members)
    derive = classmethod(derive)

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

        @param attrs: Any attributes to set for the widget. The list
        of keywords are documented (and this is enforced) in
        L{__attributes__}.
        
        """
        
        self.session = session
        self.win_id = win_id
        self.__dict__.update(attrs)
        self.__attributes__ += tuple(['html_' + name for name in self.__html_attributes__])
        for attr in self.__attributes__:
            if not hasattr(self, attr):
                raise TypeError('Required attribute not set:', str(self), attr)

    class HtmlId(object):
        def __get__(self, instance, owner):
            if instance.parent is None:
                return None
            return Webwidgets.Utils.path_to_id(instance.path)
    html_id = HtmlId()

    class HtmlClass(object):
        def __get__(self, instance, owner):
            classes = owner.classes
            if instance:
                classes = instance.classes
            return ' '.join([c.replace('.', '-')
                             for c in classes])
    html_class = HtmlClass()

    class HtmlAttributes(object):
        def __get__(self, instance, owner):
            if instance.parent is None:
                return None
            return instance.draw_html_attributes(instance.path)            
    html_attributes = HtmlAttributes()

    class Path(object):
        def __get__(self, instance, owner):
            """Returns the path of the widget within the widget tree."""
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

    def get_widgets_by_attribute(self, attribute = '__name__'):
        if hasattr(self, attribute):
            return {getattr(self, attribute): self}
        return {}

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
        attributes = [(name, getattr(self, 'html_' + name))
                      for name in self.__html_attributes__]
        return ' '.join(['%s=%s' % (name, xml.sax.saxutils.quoteattr(value))
                         for (name, value)
                         in attributes
                         if value])

    def draw_attributes(self, output_options):
        return Webwidgets.Utils.OrderedDict([('attr_' + key, self._(getattr(self, key), output_options))
                                             for key in self.__attributes__])

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
        return self.title or Webwidgets.Utils.path_to_id(path)

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
            "<script language='javascript'>%s</script>" % (script,))

    def register_style(self, name, style):
        self.register_head_content(
            name,
            "<style>%s</style>" % (style,))

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
                              document.getElementById('root-_-body-form').submit();
                             });
                            """ % info)

    def register_value(self, name, value):
        self.register_head_content('value: ' + name,
                                 """<script language="javascript">webwidgets_values['%(name)s'] = '%(value)s';</script>""" % {'name': name,
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
            return parse_languages(self.session.program.request().environ().get('HTTP_ACCEPT_LANGUAGE', 'en'))

        return ()

    def __get_translations__(cls, languages, fallback = False):
        if not hasattr(cls, '__translations__'): cls.__translations__ = {}
        if languages not in cls.__translations__:
            obj = Webwidgets.Utils.Gettext.NullTranslations()
            for base in cls.__bases__:
                if hasattr(base, '__get_translations__'):
                    obj = base.__get_translations__(languages, fallback = obj)
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
    __get_translations__ = classmethod(__get_translations__)

    def get_translations(self, output_options, languages = None):
        if languages is None:
            languages = self.get_languages(output_options)
        return self.__get_translations__(languages)

    def _(self, message, output_options):
        return self.get_translations(output_options)._(message)

    def __unicode__(self):
        return "<%(module)s.%(name)s/%(path)s at %(id)s>" % {'module': type(self).__module__,
                                                             'name': type(self).__name__,
                                                             'path': self.path and Webwidgets.Utils.path_to_id(self.path) or 'None',
                                                             'id': id(self)}

    def __str__(self):
        return str(unicode(self))

    def __repr__(self):
        return str(self)

    def __add__(self, other):
        return self.get_widget_by_path(other)

    def __setattr__(self, name, value):
        if not hasattr(self, name) or value is not getattr(self, name):
            object.__setattr__(self, name, value)    
            if name in self.__attributes__:
                self.notify('%s_changed' % name, value)

class TextWidget(Widget):
    """This widget is a simple string output widget.

    @cvar html: The "html" attribute should contain HTML code.
    """

    __attributes__ = ('html',)
    __wwml_html_override__ = True
    """Let Wwml-defined subclasses override the html attribute"""

    html = ""

    def draw(self, output_options):
        return self._(self.html, output_options)

class ChildNodes(Webwidgets.Utils.OrderedDict):
    """Dictionary of child widgets to a widget; any widgets inserted
    in the dictionary will automatically have their name and parentn
    member variables set correctly."""
    def __init__(self, node, *arg, **kw):
        """@param node: The widget the children held in this
        dictinary are children to.
        @param arg: Sent to L{dict.__init__}
        @param kw: Sent to L{dict.__init__}
        """
        self.node = node
        super(ChildNodes, self).__init__(*arg, **kw)
        self.__ensure__()

    def __ensure__(self):
        for name, value in self.iteritems():
            if isinstance(value, Widget):
                value.parent = self.node
                value.name = name

    def __setitem__(self, *arg, **kw):
        super(ChildNodes, self).__setitem__(*arg, **kw)
        self.__ensure__()

    def update(self, *arg, **kw):
        super(ChildNodes, self).update(*arg, **kw)
        self.__ensure__()

    def setdefault(self, *arg, **kw):
        super(ChildNodes, self).setdefault(*arg, **kw)
        self.__ensure__()

class Composite(Widget):
    """Base class for all composite widgets, handling the drawing of
    children and the visibility attribute of children."""
    __no_classes_name__ = True
    def __init__(self, session, win_id, **attrs):
        super(Composite, self).__init__(
            session, win_id, **attrs)

    def draw_child(self, path, child, output_options, invisible_as_empty = False):
        """Renders a child widget to HTML using its draw() method.
        Also handles visibility of the child: if invisible_as_empty is
        False, rendering an invisible child will yeild None, otherwize
        it will yield the empty string."""
        invisible = [None, ''][invisible_as_empty]
        if isinstance(child, Widget):
            if not child.get_visible(path): return invisible
            return child.draw(output_options)
        else:
            if not self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id, path):
                return invisible
            return self._(child, output_options)

    def draw_children(self, output_options, invisible_as_empty = False, include_attributes = False):
        """Renders all child widgets to HTML using their draw methods.
        Also handles visibility of the children - invisible children
        are not included in the output.

        @return: dictionary of child_names and HTML for the respective
                 children.
        """
        
        res = Webwidgets.Utils.OrderedDict()

        for name, child in self.get_children():
            child = self.draw_child(self.path + [name], child, output_options, invisible_as_empty)
            if child is not None:
                res[name] = child

        if include_attributes:
            res.update(self.draw_attributes(output_options))
        return res

    def get_children(self):
        """@return: a dictionary of child widget names and their
        respective widgets.
        """
        raise NotImplemented

    def get_child(self, name):
        """@return: a child widget."""
        raise NotImplemented

    def get_widgets_by_attribute(self, attribute = '__name__'):
        fields = Widget.get_widgets_by_attribute(self, attribute)
        for name, child in self:
            if isinstance(child, Widget):
                fields.update(child.get_widgets_by_attribute(attribute))
        return fields

    def __getitem__(self, name):
        """@return: a child widget."""
        return self.get_child(name)

    def __iter__(self):
        return self.get_children()
        
class StaticComposite(Composite):
    """Base class for all composite widgets, handling children
    instantiation of children classes. Children instantiated (or
    gotten from arguments) are put in the children member variable.
    This class also handles drawing of children and the visibility
    attribute of children."""

    __no_classes_name__ = True
    
    def __init__(self, session, win_id, **attrs):
        __attributes__ = set(attrs.get('__attributes__', self.__attributes__))

        super(StaticComposite, self).__init__(
            session, win_id,
            **attrs)
        self.children = ChildNodes(self, getattr(self, 'children', {}))

        # Class members have no intrinsic order, so we sort them on
        # their order of creation, which if created through the Python
        # class statement, is the same as their textual order :)
        
        child_classes = []
        for name in dir(self):
            if name == '__class__': continue
            value = getattr(self, name)
            if isinstance(value, type) and issubclass(value, Widget) and not value.__explicit_load__:
                child_classes.append((name, value))
            elif isinstance(value, Widget):
                self.children[name] = value
                
        child_classes.sort(lambda x, y: cmp(x[1].class_order_nr, y[1].class_order_nr))
        
        for (name, value) in child_classes:
            self.children[name] = value(session, win_id)

    def get_children(self):
        return self.children.iteritems()

    def get_child(self, name):
        try:
            return self.children[name]
        except:
            raise KeyError("No such child %s to %s" % (name, str(self)))

    def __setitem__(self, name, value):
        """Adds a new child widget"""
        self.children[name] = value

    def __delitem__(self, name):
        """Deletes a child widget"""
        del self.children[name]

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
            def raise_dominants(dominants, inputLevel):
                for dom in dominants:
                    if dom._input_level <= inputLevel:
                        dom._input_level = inputLevel + 1
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

    __attributes__ = Widget.__attributes__ + ('active', 'argument_name', 'error',
                                              '__input_subordinates__', '__input_dominants__')

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
    
    __attributes__ = Input.__attributes__ + ('value',)
    value = ''

    def field_input(self, path, string_value):
        self.value = string_value

    def field_output(self, path):
        return [unicode(self.value)]

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

    def field_input(self, path, string_value):
        if string_value != '':
            self.notify('clicked')

    def field_output(self, path):
        return []

    def clicked(self, path):
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
                    'Content-type': Webwidgets.Utils.FileHandling.extension_to_mime_type[ext]}
        finally:
            file.close()
    class_output = classmethod(class_output)


class Window(Widget):
    """Window is the main widget and should allways be the top-level
    widget of any application. It has an attribute for the HTTP
    headers and handles form submission values and URL arguments."""

    __attributes__ = ('headers', 'languages')
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
    __attributes__ = StaticComposite.__attributes__ + ('headers', 'encoding', 'doctype')
    headers = {'Status': '200 OK'}
    title = 'Page not available'
    body = TextWidget.derive(html = 'Page not available')
    head = TextWidget.derive(html = '')
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
            result['body'] = body
        if title is None: title = self.get_title(self.path)
        result['title'] = '<title>' + title + '</title>'
        result['doctype'] = self.doctype
        result['uri'] = cgi.escape(self.session.program.request()._environ['REQUEST_URI'])
        result['name'] = result['id'] = Webwidgets.Utils.path_to_id(self.path)
        result['base'] = self.session.program.request_base()

        for (all1, name1, value1, all2, value2, name2) in self.findallvalues.findall(result['body']):
            self.register_value('fieldValue' + '_' + (name1 or name2), (value1 or value2))

        result['head_content'] = '\n'.join(self.head_content.values())
        
        return ("""
%(doctype)s
<html xmlns="http://www.w3.org/1999/xhtml">
 <head>
  <base href='%(base)s' />
  %(head_content)s
  %(title)s
  %(head)s
 </head>
 <body %(attr_html_attributes)s>
  <form name="%(name)s" method='post' enctype='multipart/form-data' action='%(uri)s' id="%(attr_html_id)s-_-body-form">
   %(body)s
  </form>
 </body>
</html>""" % result).encode(self.encoding)
