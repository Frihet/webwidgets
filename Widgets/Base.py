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

import types, xml.sax.saxutils, os.path, cgi, re
import Webwidgets.Utils, Webwidgets.Constants

debugNotifications = False

class Widget(object):
    """Widget is the base class for all widgets. It manages class name
    collection, attribute handling, child instantiation and
    notifications.

    Attributes are special class variables that can also be overridden
    by instance variables set using keyword arguments to L{__init__}..
    Attributes for a class must be listed in the L{__attributes__}
    member. They are used 

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

    __attributes__ = ('visible', 'classes', 'title', 'htmlAttributes')
    """List of all attributes that can be set for the widget using
    either class members or arguments to __init__"""

    __htmlAttributes__ = ('id', 'class',)

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

    class __metaclass__(type):
        def __new__(cls, name, bases, members):
            members = dict(members)
            classes = []
            if '__no_classes_name__' not in members or not members['__no_classes_name__']:
                classes.append(members['__module__'] + '.' + name)
            if '__no_classes_name__' in members:
                del members['__no_classes_name__'] # No inheritance! This is a magic marker, not an attribute
            for base in bases:
                if hasattr(base, 'classes'):
                    classes.extend(base.classes)
            members['classes'] = tuple(classes)
            return type.__new__(cls, name, bases, members)

    def __init__(self, session, winId, **attrs):
        """Creates a new widget
        
        @param session: L{Webwidgets.Program.Session} instance. Must be
                       same as for any parent widget.

        @param winId: The "window identifier". Must be same as for any
                     parent widget. The window identifier is a
                     pair of the path to the Webware page that serves
                     the current Webwidgets application, and any extra
                     window id string added as a first part of an
                     extra path. Example: if we are accessing

                     http://myserver/WKMod/MyContext/MyPage/:popup/foo/bar?fie=hehe

                     the winId will be

                     ('MyContext/MyPage', 'popup')

        @param attrs: Any attributes to set for the widget. The list
        of keywords are documented (and this is enforced) in
        L{__attributes__}.
        
        """
        
        self.session = session
        self.winId = winId
        for name in dir(type(self)):
            if name == '__class__': continue
            item = getattr(self, name)
            if isinstance(item, type) and issubclass(item, Widget) and not item.__explicit_load__:
                setattr(self, name, item(session, winId))
        self.__dict__.update(attrs)
        self.__attributes__ += tuple(['html_' + name for name in self.__htmlAttributes__])
        for attr in self.__attributes__:
            if not hasattr(self, attr):
                raise TypeError('Required attribute not set:', str(self), attr)

    class htmlId(object):
        def __get__(self, instance, owner):
            if not hasattr(instance, 'parent'):
                return None
            return Webwidgets.Utils.pathToId(instance.path)
    html_id = htmlId()

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
            if not hasattr(instance, 'parent'):
                return None
            return instance.drawHtmlAttributes(instance.path)            
    htmlAttributes = HtmlAttributes()

    class Path(object):
        def __get__(self, instance, owner):
            """Returns the path of the widget within the widget tree."""
            if not hasattr(instance, 'parent'):
                return None
            if instance.parent.path is None:
                return None
            return instance.parent.path + [instance.name]
    path = Path()

    class Window(object):
        def __get__(self, instance, owner):
            if not hasattr(instance, 'session'):
                return None
            return instance.session.windows.get(instance.winId, None)
    window = Window()
    
    def getVisible(self, path):
        return self.visible and self.session.AccessManager(Webwidgets.Constants.VIEW, self.winId, path)

    def getWidgetByPath(self, path):
        path = Webwidgets.Utils.RelativePath(path)
        res = self
        for i in xrange(0, path.levels):
            res = res.parent
        for name in path.path:
            res = res[name]
        return res

    def getWidgetsByAttribute(self, attribute = '__name__'):
        if hasattr(self, attribute):
            return {getattr(self, attribute): self}
        return {}

    def pathToSubwidgetPath(self, path):
        widgetPath = self.path
        if not Webwidgets.Utils.isPrefix(widgetPath + ['_'], path):
            raise Webwidgets.Constants.NotASubwidgetException('%s: Not a subwidget path %s' % (str(self), path,))
        return path[len(widgetPath) + 1:]

    def notify(self, message, *args, **kw):
        """See L{notifyKw}."""
        self.notifyKw(message, args, kw)

    def notifyKw(self, message, args = (), kw = {}, path = None):
        """Enques a message (method name and arguments) for the
        widget. Please see the documentation for
        L{Webwidgets.Program.Program.Session.notify} for more
        information on the message passing mechanism."""        
        self.session.notify(self, message, args, kw, path)

    def drawHtmlAttributes(self, path):
        attributes = [(name, getattr(self, 'html_' + name))
                      for name in self.__htmlAttributes__]
        return ' '.join(['%s=%s' % (name, xml.sax.saxutils.quoteattr(value))
                         for (name, value)
                         in attributes
                         if value])

    def drawAttributes(self, outputOptions):
        return Webwidgets.Utils.OrderedDict([('attr_' + key, getattr(self, key))
                                             for key in self.__attributes__])

    def draw(self, outputOptions):
        """Renders the widget to HTML. Path is where the full path to
        the widget to render, that is what might go into the id-field
        of an HTML-tag for the widget. Use
        L{Webwidgets.Utils.pathToId} for this purpose. Any extra
        sub-widget id:s should be constructed by appending an
        underscore followed by any string."""
        self.registerStyles(outputOptions)
        return ''

    def registerStyles(self, outputOptions):
        cls = type(self)
        def registerClassStyles(cls):
            bases = list(cls.__bases__)
            bases.reverse()
            for base in bases:
                registerClassStyles(base)
            if cls.__dict__.get('widgetStyle', None):
                self.registerStyleLink(self.calculateUrl({'widgetClass': cls.__module__ + '.' + cls.__name__,
                                                          'aspect': 'style'},
                                                         {}))
            if cls.__dict__.get('widgetScript', None):
                self.registerScriptLink(self.calculateUrl({'widgetClass': cls.__module__ + '.' + cls.__name__,
                                                           'aspect': 'script'},
                                                          {}))
        registerClassStyles(cls)
        if self.__dict__.get('widgetStyle', None):
            self.registerStyleLink(self.calculateUrl({'widget': Webwidgets.Utils.pathToId(self.path),
                                                      'aspect': 'style'},
                                                     {}))
        if self.__dict__.get('widgetScript', None):
            self.registerScriptLink(self.calculateUrl({'widget': Webwidgets.Utils.pathToId(self.path),
                                                       'aspect': 'script'},
                                                      {}))

    def classOutput_style(cls, window, outputOptions):
        return cls.widgetStyle
    classOutput_style = classmethod(classOutput_style)

    def output_style(self, outputOptions):
        return self.widgetStyle

    def classOutput_script(cls, window, outputOptions):
        return cls.widgetScript
    classOutput_script = classmethod(classOutput_script)

    def output_script(self, outputOptions):
        return self.widgetScript

    def getTitle(self, path):
        return self.title or Webwidgets.Utils.pathToId(path)

    def registerHeadContent(self, contentName, content):        
        self.session.windows[self.winId].headContent[contentName] = content

    def registerScriptLink(self, *uris):
        contentName = 'script: ' + ' '.join(uris)
        self.registerHeadContent(
            contentName,
            '\n'.join(["<script src='%s' type='text/javascript' ></script>" % (cgi.escape(uri),)
                       for uri in uris]))
        
    def registerStyleLink(self, *uris):
        contentName = 'style: ' + ' '.join(uris)
        self.registerHeadContent(
            contentName,
            '\n'.join(["<link href='%s' rel='stylesheet' type='text/css' />" % (cgi.escape(uri),)
                       for uri in uris]))

    def registerScript(self, name, script):
        self.registerHeadContent(
            name,
            "<script language='javascript'>%s</script>" % (script,))

    def registerStyle(self, name, style):
        self.registerHeadContent(
            name,
            "<style>%s</style>" % (style,))

    def registerSubmitAction(self, path, event):
        info = {'id': Webwidgets.Utils.pathToId(path),
                'event': event}
        self.registerScript('submitAction: %(id)s: %(event)s' % info,
                            """
                            webwidgets_add_event_handler_once_loaded(
                             '%(id)s',
                             '%(event)s',
                             'webwidgets_submit_action',
                             function () {
                              document.getElementById('root-_-body-form').submit();
                             });
                            """ % info)

    def registerValue(self, name, value):
        self.registerHeadContent('value: ' + name,
                                 """<script language="javascript">webwidgets_values['%(name)s'] = '%(value)s';</script>""" % {'name': name,
                                                                                                                              'value': value})

    def calculateUrl(self, outputOptions, arguments = None):
        location, generatedArguments = self.session.generateArguments(self.session.getWindow(self.winId))
        if arguments is None: arguments = generatedArguments
        return self.session.calculateUrl(self.winId, location, arguments,
                                         outputOptions)
        
    def getLanguages(self, outputOptions):
        def parseLanguages(languages):
            return [item.split(';')[0]
                    for item in languages.split(',')]
        
        if 'languages' in outputOptions:
            return parseLanguages(outputOptions['languages'])
        if self.window is not None:
            if self.window.languages is not None:
                return self.window.languages
        if hasattr(self, 'session'):
            if self.session.languages is not None:
                return self.session.languages
            return parseLanguages(self.session.program.request().environ().get('HTTP_ACCEPT_LANGUAGE', 'en'))

        return []

    def __unicode__(self):
        return "<%(module)s.%(name)s/%(path)s at %(id)s>" % {'module': type(self).__module__,
                                                             'name': type(self).__name__,
                                                             'path': self.path and Webwidgets.Utils.pathToId(self.path) or 'None',
                                                             'id': id(self)}

    def __str__(self):
        return str(unicode(self))

    def __repr__(self):
        return str(self)

    def __add__(self, other):
        return self.getWidgetByPath(other)

    def __setattr__(self, name, value):
        if not hasattr(self, name) or value is not getattr(self, name):
            object.__setattr__(self, name, value)    
            if name in self.__attributes__:
                self.notify('%sChanged' % name, value)

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
    def __init__(self, session, winId, **attrs):
        super(Composite, self).__init__(
            session, winId, **attrs)

    def drawChild(self, path, child, outputOptions, invisibleAsEmpty = False):
        """Renders a child widget to HTML using its draw() method.
        Also handles visibility of the child: if invisibleAsEmpty is
        False, rendering an invisible child will yeild None, otherwize
        it will yield the empty string."""
        invisible = [None, ''][invisibleAsEmpty]
        if isinstance(child, Widget):
            if not child.getVisible(path): return invisible
            return child.draw(outputOptions)
        else:
            if not self.session.AccessManager(Webwidgets.Constants.VIEW, self.winId, path):
                return invisible
            return unicode(child)

    def drawChildren(self, outputOptions, invisibleAsEmpty = False, includeAttributes = False):
        """Renders all child widgets to HTML using their draw methods.
        Also handles visibility of the children - invisible children
        are not included in the output.

        @return: dictionary of childnames and HTML for the respective
                 children.
        """
        
        res = Webwidgets.Utils.OrderedDict()

        for name, child in self.getChildren():
            child = self.drawChild(self.path + [name], child, outputOptions, invisibleAsEmpty)
            if child is not None:
                res[name] = child

        if includeAttributes:
            res.update(self.drawAttributes(outputOptions))
        return res

    def getChildren(self):
        """@return: a dictionary of child widget names and their
        respective widgets.
        """
        raise NotImplemented

    def getChild(self, name):
        """@return: a child widget."""
        raise NotImplemented

    def getWidgetsByAttribute(self, attribute = '__name__'):
        fields = Widget.getWidgetsByAttribute(self, attribute)
        for name, child in self:
            if isinstance(child, Widget):
                fields.update(child.getWidgetsByAttribute(attribute))
        return fields

    def __getitem__(self, name):
        """@return: a child widget."""
        return self.getChild(name)

    def __iter__(self):
        return self.getChildren()
        
class StaticComposite(Composite):
    """Base class for all composite widgets, handling children
    instantiation of children classes explicitly named in __children__
    (or all if __widget_children__ is true). Children instantiated (or
    gotten from arguments if __args_children__ is true) are put in the
    children member variable. This class also handles drawing of
    children and the visibility attribute of children."""
    __no_classes_name__ = True
    __children__ = ()
    __args_children__ = True
    __widget_children__ = True
    def __init__(self, session, winId, **attrs):
        __attributes__ = '__attributes__' in attrs and attrs['__attributes__'] or self.__attributes__
        __children__ = '__children__' in attrs and attrs['__children__'] or self.__children__
        super(StaticComposite, self).__init__(
            session, winId,
            __attributes__ = __attributes__ + __children__,
            **attrs)
        self.children = ChildNodes(self)
        if self.__args_children__:
            __children__ = __children__ + tuple(set(attrs.keys()) - set(__attributes__))
        if self.__widget_children__:
            for name, item in self.__dict__.iteritems():
                if isinstance(item, Widget):
                    __children__ += (name,)
        for childname in __children__:
            self.children[childname] = getattr(self, childname)

    def getChildren(self):
        return self.children.iteritems()

    def getChild(self, name):
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
        debugInputOrder = False
        
        def __new__(cls, name, bases, members):
            subordinates = set()
            dominants = set()
            if '__inputSubordinates__' in members:
                subordinates = subordinates.union(set(members['__inputSubordinates__']))
            if '__inputDominants__' in members:
                dominants = dominants.union(set(members['__inputDominants__']))
            for base in bases:
                if hasattr(base, '__inputSubordinates__'):
                    subordinates = subordinates.union(base.__inputSubordinates__)
                if hasattr(base, '__inputDominants__'):
                    dominants = dominants.union(base.__inputDominants__)
            members['_inputLevel'] = max([0] + [sub._inputLevel
                                                for sub in subordinates]) + 1
            def raiseDominants(dominants, inputLevel):
                for dom in dominants:
                    if dom._inputLevel <= inputLevel:
                        dom._inputLevel = inputLevel + 1
                        raiseDominants(dom.__inputDominants__, dom._inputLevel)
            raiseDominants(dominants, members['_inputLevel'])
            members['__inputSubordinates__'] = subordinates
            members['__inputDominants__'] = dominants

            if cls.debugInputOrder:
                print "Registering input widget:", name
                print "    Subordinates:", ', '.join([sub.__name__ for sub in subordinates])
                print "    Dominants:", ', '.join([sub.__name__ for sub in dominants])
                print "    Level:", members['_inputLevel']
            
            return Widget.__metaclass__.__new__(cls, name, bases, members)

    def inputOrder(cls, other):
        if isinstance(other, Input):
            other = type(other)
        return cmp(cls._inputLevel, other._inputLevel) or cmp(cls, other) or cmp(id(cls), id(other))
    inputOrder = classmethod(inputOrder)

    __attributes__ = Widget.__attributes__ + ('active', 'argumentName', 'error',
                                              '__inputSubordinates__', '__inputDominants__')

    active = True
    """Enables the user to actually use this input field."""

    argumentName = None
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

    __inputSubordinates__ = ()
    """Other input widgets that should handle simultaneous input from
    the user _before_ this widget."""    

    __inputDominants__ = ()
    """Other input widgets that should handle simultaneous input from
    the user _after_ this widget."""    

    class HtmlClass(Widget.HtmlClass):
        def __get__(self, instance, owner):
            err = ''
            if instance.error:
                err = ' error'
            return Widget.HtmlClass.__get__(self, instance, owner) + err
    html_class = HtmlClass()

    def registerInput(self, path = None, argumentName = None, field = True):
        if path is None: path = self.path
        active = self.getActive(path)
        if active:
            if field:
                self.session.windows[self.winId].fields[Webwidgets.Utils.pathToId(path)] = self
            if argumentName:
                self.session.windows[self.winId].arguments[argumentName] = {'widget':self, 'path': path}
        return active

    def fieldInput(self, path, *stringValues):
        raise NotImplementedError(self, "fieldInput")
    
    def fieldOutput(self, path):
        raise NotImplementedError(self, "fieldOutput")
    
    def draw(self, outputOptions):
        self.registerInput(self.path, self.argumentName)
        return ''

    def getActive(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        return self.active and self.session.AccessManager(Webwidgets.Constants.EDIT, self.winId, path)

class ValueInput(Input):
    """Base class for all input widgets that holds some kind of value
    (e.g. all butt buttons). It defines a notification for changing
    the value hold by the widget."""
    
    __attributes__ = Input.__attributes__ + ('value',)
    value = ''

    def fieldInput(self, path, stringValue):
        self.value = stringValue

    def fieldOutput(self, path):
        return [unicode(self.value)]

    def valueChanged(self, path, value):
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

    __inputSubordinates__ = (ValueInput,)

    def fieldInput(self, path, stringValue):
        if stringValue != '':
            self.notify('clicked')

    def fieldOutput(self, path):
        return []

    def clicked(self, path):
        if path != self.path: return
        return

class Window(Widget):
    """Window is the main widget and should allways be the top-level
    widget of any application. It has an attribute for the HTTP
    headers and handles form submission values and URL arguments."""
    __attributes__ = ('headers', 'languages')
    headers = {'Status': '404 Page not implemented'}
    languages = None

    def __init__(self, session, winId, **attrs):
        super(Window, self).__init__(session, winId, **attrs)
        self.fields = {}
        self.arguments = {}

    path = []

    def output(self, outputOptions):
        result = {Webwidgets.Constants.OUTPUT: self.draw(outputOptions)}
        result.update(self.headers)
        return result

    def draw(self, outputOptions):
        self.fields = {}
        self.arguments = {}
        return ''


file = open(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         'Widgets.css'))
genericStyle = file.read()
file.close()

file = open(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         'Widgets.js'))
genericScript = file.read()
file.close()

class HtmlWindow(Window, StaticComposite):
    """HtmlWindow is the main widget for any normal application window
    displaying HTML. It has two children - head and body aswell as
    attributes for title, encoding and doctype"""
    __attributes__ = StaticComposite.__attributes__ + ('headers', 'encoding', 'doctype')
    __children__ = ('head', 'body')
    headers = {'Status': '200 OK'}
    title = 'Page not available'
    body = 'Page not available'
    head = ''
    encoding = 'UTF-8'
    doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'

    widgetStyle = {Webwidgets.Constants.FINAL_OUTPUT: genericStyle,
                   'Content-type': 'text/css',
                   'Cache-Control': 'public; max-age=3600',
                   }
    widgetScript = {Webwidgets.Constants.FINAL_OUTPUT: genericScript,
                   'Content-type': 'application/x-javascript',
                   'Cache-Control': 'public; max-age=3600',
                   }

    findallvalues = re.compile(
        r"""(id=["']([^"'<>]*)["'][^<>]*value=["']([^"'<>]*)["'])|(value=["']([^"'<>]*)["'][^<>]*id=["']([^"'<>]*)["'])""",
        re.MULTILINE)

    def output(self, outputOptions):
        result = Window.output(self, outputOptions)
        result['Content-Type'] = 'text/html; charset=%(encoding)s' % {'encoding': self.encoding}
        return result

    def draw(self, outputOptions, body = None, title = None):
        Window.draw(self, outputOptions)
        self.headContent = Webwidgets.Utils.OrderedDict()

        self.registerStyles(outputOptions)

        result = self.drawChildren(
            outputOptions,
            invisibleAsEmpty = True,
            includeAttributes = True)

        if body is not None:
            result['body'] = body
        if title is None: title = self.getTitle(self.path)
        result['title'] = '<title>' + title + '</title>'
        result['doctype'] = self.doctype
        result['uri'] = cgi.escape(self.session.program.request()._environ['REQUEST_URI'])
        result['name'] = result['id'] = Webwidgets.Utils.pathToId(self.path)
        result['base'] = self.session.program.requestBase()

        for (all1, name1, value1, all2, value2, name2) in self.findallvalues.findall(result['body']):
            self.registerValue('fieldValue' + '_' + (name1 or name2), (value1 or value2))

        result['headContent'] = '\n'.join(self.headContent.values())
        
        return ("""
%(doctype)s
<html xmlns="http://www.w3.org/1999/xhtml">
 <head>
  <base href='%(base)s' />
  %(headContent)s
  %(title)s
  %(head)s
 </head>
 <body %(attr_htmlAttributes)s>
  <form name="%(name)s" method='post' enctype='multipart/form-data' action='%(uri)s' id="%(attr_html_id)s-_-body-form">
   %(body)s
  </form>
 </body>
</html>""" % result).encode(self.encoding)
