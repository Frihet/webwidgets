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

"""Base widgets to define the application user interface.

This module contains a set of base widgets that can be usedv to define
the user-interface of an application. In addition, it contains some
generic base ww_classes that can be used when implementing more elaborate
widgets.
"""

import types, xml.sax.saxutils, os.path, cgi, re, sys, weakref
import traceback, WebUtils.HTMLForException, pdb
import Webwidgets.Constants
import Webwidgets.ObjectMod
import Webwidgets.Utils
import Webwidgets.Utils.Gettext
import Webwidgets.Utils.FileHandling
import Webwidgets.Utils.Threads

debug_exceptions = False
print_exceptions = False
log_exceptions = True

class LazyTranslatingAttributeDict(object):
    def __init__(self, source, output_options=None):
        if output_options is not None:
            self.source = source
            self.output_options = output_options
            self.cache = {}
        elif isinstance(source, type(self)):
            self.source = source.source
            self.output_options = source.output_options
            self.cache = dict(source.cache)
        else:
            raise Exception("No output_options supplied to constructor of LazyTranslatingAttributeDict")

    def __contains__(self, key):
        return (   key in self.cache
                or hasattr(self.source, key)
                or (    key[0:17] == 'ww_untranslated__'
                    and hasattr(self.source, key[17:])))

    def __setitem__(self, key, value):
        self.cache[key] = value

    def __getitem__(self, key):
        if key in self.cache:
            res = self.cache[key]
            if isinstance(res, types.FunctionType):
                res = self.cache[key] = res()
            return res
        
        if hasattr(self.source, key):
            value = getattr(self.source, key)
            if isinstance(value, (type, types.MethodType)):
                raise KeyError(key)
            try:
                return self.source._(value, self.output_options)
            except:
                return unicode(value)

        if key[0:17] == 'ww_untranslated__':
            key2 = key[17:]
            if hasattr(self.source, key2):
                value = getattr(self.source, key2)
                if isinstance(value, (type, types.MethodType)):
                    raise KeyError(key)
                return unicode(value)
        raise KeyError(key)

    def update(self, other):
        if hasattr(other, 'iteritems'):
            other = other.iteritems()
        for (name, value) in other:
            self.cache[name] = value

    def not_implemented(self, *arg, **kw):
        raise Exception("NOT IMPLEMENTED")
    
    __iter__ = __delitem__ = __add__ = __repr__ = __str__ = clear = items = iteritems = iterkeys = itervalues = keys = pop = popitem = setdefault = values = sort = not_implemented

class Widget(Webwidgets.ObjectMod.Object):
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

    input_required = False
    """Displayed by a corresponding L{Label} in some fashion if set to
    True. See that widget for further information."""

    log_id_msg = u"""<div class="log-id">Log id for this exception is: %(log_id)s</div>"""
    """Error message displayed on widget error."""

    ww_class_orderings = set.union(Webwidgets.ObjectMod.Object.ww_class_orderings,
                                   ('display',))
                
    ww_display_pre = set()
    """Other widgets that should be displayed prior to this widget in
    lists and the like.

    Note: If you make circles, you will cause an infinite loop. That's
    usually what cirle means, so no news there :P
    """

    ww_display_post = set()
    """Other widgets that should be displayed after this widget in
    lists and the like.

    Note: If you make circles, you will cause an infinite loop. That's
    usually what cirle means, so no news there :P
    """

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
        Webwidgets.ObjectMod.Object.__init__(self, **attrs)

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
        path = Webwidgets.Utils.WidgetPath(path)
        res = self
        if path.levels is None:
            res = res.window
        else:
            for i in xrange(0, path.levels):
                res = res.parent
        for name in path.path:
            res = res[name]
        return res

    def get_path_by_widget(self, widget):
        return Webwidgets.Utils.WidgetPath(widget.path) - Webwidgets.Utils.WidgetPath(self.path)

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

    def append_exception(self, message=u''):
        """Appends the current exception to the exceptions of this
        widget. This will be shown to the user next to the widget (or
        instead of the widget if this was from the draw method
        crashing).

        Do not ever let exceptions propagate so that they kill of the
        whole page!
        """
        if print_exceptions:
            traceback.print_exc()
        log_id = None
        if Webwidgets.Utils.is_log_exceptions():
            log_id = Webwidgets.Utils.log_exception()

        if debug_exceptions:
            # Uggly hack around a bug in pdb (it apparently depends on
            # and old sys-API)
            sys.last_traceback = sys.exc_info()[2]

            print "######################### The application has crashed ##########################"
            print "Exception: %s" % (sys.exc_info()[1],)
            pdb.pm()

        self.system_errors.append(
            {'exception': sys.exc_info()[1],
             'log_id': log_id,
             'message': message,
             'traceback': WebUtils.HTMLForException.HTMLForException()})

    def draw_html_attributes(self, path):
        """Renders list of all attributes set on self starting with
        html_ not being html_attributes. Setting autocomplete="off" on
        a Widget could be done by doing widget.html_autocomplete="off"."""

        attributes = [(name[5:], getattr(self, name))
                      for name in dir(self)
                      if name.startswith('html_') and name != 'html_attributes']
        return ' '.join(['%s=%s' % (name, xml.sax.saxutils.quoteattr(value))
                         for (name, value)
                         in attributes
                         if value])

    def draw_attributes(self, output_options):
        return LazyTranslatingAttributeDict(self, output_options)

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

    @classmethod
    def class_output_style(cls, session, arguments, output_options):
        return cls.widget_style

    def output_style(self, output_options):
        return self.widget_style

    @classmethod
    def class_output_script(cls, session, arguments, output_options):
        return cls.widget_script

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
                return ('en',)

        return ()

    @classmethod
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
                                                        'path': Webwidgets.Utils.path_to_id(self.path),
                                                        'id': id(self)}

    def __add__(self, other):
        return self.get_widget_by_path(other)

    def __sub__(self, other):
        return other.get_path_by_widget(self)

class Text(Widget):
    """This widget is a simple string output widget.

    @cvar html: The "html" attribute should contain HTML code.
    """

    __wwml_html_override__ = True
    """Let Wwml-defined subclasses override the html attribute"""

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
                               %(log_id)s
                               <div class='log-message'>%(message)s</div>
                               %(traceback)s
                              </div>
                             </div>"""

    system_error_log_id_format = """<div>More information on this item can be found in the log-file with issue ID <span class="log-id">%(log_id)s</span>.</div>"""

    system_errors_log_ids_format = """<div>Please mention the following issue ID when reporting this: <span class="log-ids">%(log_ids)s</span></div>"""

    system_errors_format = """<div class="system-errors js-dialog">

                               <div class="head">Sorry, an error occured.</div>
                               <div class="body">

                                <div>Sorry, an unexpected error
                                occured. You can try to log out and
                                back in again to solve this.</div>

                                %(log_ids)s

                                <div class="content">
                                 <p>This part of the application has
                                 crashed. You can try to log out and
                                 log in again to remedy the problem,
                                 or just continue using other parts of
                                 the application. In any case, please
                                 contact the system administrator
                                 about this issue and tell him/her the
                                 steps you took that lead up to this
                                 issue and he/she will try to fix the
                                 problem as fast as possible.</p>

                                 <p>A more technical, detailed
                                 description of the error follows
                                 (click on the items to expand):</p>

                                 %(tracebacks)s
                                </div>
                               </div>

                               <div class="foot">
                                <span class="expand">Read more...</span>
                                <span class="collapse">Hide details</span>
                                <span class="hide">Hide</span>
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
            Webwidgets.HtmlWindow.register_header(self, "Status", "500 Application exception cought")
            system_error_format = self._(self.system_error_format, output_options)
            system_error_log_id_format = self._(self.system_error_log_id_format, output_options)
            system_errors_log_ids_format = self._(self.system_errors_log_ids_format, output_options)
            system_errors_format = self._(self.system_errors_format, output_options)
            errors = [system_error_format % {'exception': cgi.escape(Webwidgets.Utils.convert_to_str_any_way_possible(error['exception'])),
                                             'log_id': error['log_id'] and system_error_log_id_format % {'log_id': error['log_id']} or '',
                                             'message': error['message'],
                                             'traceback': Webwidgets.Utils.convert_to_str_any_way_possible(error['traceback'])}
                      for error in child.system_errors]
            log_ids = [error['log_id'] for error in child.system_errors
                       if error['log_id'] is not None]
            log_ids_str = ''
            if log_ids:
                log_ids_str = system_errors_log_ids_format % {'log_ids': '.'.join(log_ids)}

            result = system_errors_format % {
                'log_ids': log_ids_str,
                'tracebacks': '\n'.join(errors)} + result
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
            try:
                value = getattr(self, name, None)
            except:
                value = None
            
            if isinstance(value, type) and issubclass(value, Widget) and not value.__dict__.get('ww_explicit_load', False):
                child_classes.append((name, value))

        display_cmp = self.get_class_ordering_cmp('display')
        child_classes.sort(lambda x, y: display_cmp(x[1], y[1]))

        for (name, value) in child_classes:
            self.children[name] = value(session, win_id)

    ww_child_class_orderings = set.union(DictComposite.ww_child_class_orderings,
                                         ('display',))

class Input(Widget):
    """Base class for all input widgets, providing input field registration"""

    ww_class_orderings = set.union(Widget.ww_class_orderings,
                                   ('input',))
            
    ww_input_pre = set()
    """Other input widgets that should handle simultaneous input from
    the user _before_ this widget.

    Note: If you make circles, you will cause an infinite loop. That's
    usually what cirle means, so no news there :P
    """

    ww_input_post = set()
    """Other input widgets that should handle simultaneous input from
    the user _after_ this widget.

    Note: If you make circles, you will cause an infinite loop. That's
    usually what cirle means, so no news there :P
    """
    
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
    ignore_input_this_request = False
    """If true, input for this field is suppressed for one/current
    request. This member is reset after each request."""

    ww_bind_callback = "require"

    allways_do_field_input = False

    class HtmlClass(Widget.HtmlClass):
        def __get__(self, instance, owner):
            if instance is None:
                return None
            html_class = [Widget.HtmlClass.__get__(self, instance, owner)]

            if instance.error:
                html_class.append('ww-error')

            if instance.input_required:
                html_class.append('ww-input-required')

            if not instance.get_active(instance.path):
                html_class.append('ww-disabled')
                            
            return ' '.join(html_class)
    html_class = HtmlClass()

    @property
    def html_disabled(self):
        return ['', 'disabled'][not self.get_active(self.path)]

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

    class WwModel(Webwidgets.ObjectMod.Model):
        value = ''

        original_value = ''

        multiple = False
        """Handle multiple values"""

    @classmethod
    def reset_all_inputs(cls, widget):
        if hasattr(widget, "reset"):
            try:
                widget.reset()
            except:
                widget.append_exception()

        if hasattr(widget, "get_children"):
            for name, child in widget.get_children():
                cls.reset_all_inputs(child)

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

    ww_input_pre = (ValueInput,)

    def field_output(self, path):
        return ['']

class ActionInput(MixedInput):
    """Base class for all input widgets that only fires some
    notification and don't hold a value of some kind."""

    ww_input_pre = (MixedInput,)

class SingleActionInput(ActionInput):
    """Base class for all input widgets that only fires a single
    notification with no parameters."""

#    ww_input_pre = (ValueInput,)

    def field_input(self, path, string_value):
        if string_value != '':
            self.notify('clicked')

    def clicked(self, path):
        if path != self.path: return
        return

class MultipleActionInput(ActionInput):
    """Base class for all input widgets that can fire any of a set of
    notifications."""

#    ww_input_pre = (ValueInput,)

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

    @classmethod
    def class_output(cls, session, arguments, output_options):
        path = output_options['location']
        for item in path:
            assert item != '..'

        ext = os.path.splitext(path[-1])[1][1:]
        try:
            file = open(os.path.join(cls.base_directory,
                                     *path))
        except:
            return {Webwidgets.Constants.FINAL_OUTPUT: "File not found",
                    'Content-type': "text/plain",
                    'Cache-Control': 'public; max-age=3600',
                    'Status': '404 File not found'
                    }
        else:
            try:
                return {Webwidgets.Constants.FINAL_OUTPUT: file.read(),
                        'Content-type': Webwidgets.Utils.FileHandling.extension_to_mime_type[ext],
                        'Cache-Control': 'public; max-age=3600'
                        }
            finally:
                file.close()

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
