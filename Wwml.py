#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moeller@freecode.no>

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

"""

This module implements a XML-based syntax for defining widgets - Wwml.
It has no public classes, functions or members. Instead, when loaded,
Wwml-files can be imported using the ordinary Python methods of
importing modules, e.g.::

  import foo

to import the file C{foo.wwml}.


The Wwml user interface markup language
=======================================

  Wwml provides an alternative and much shorter
  syntax for defining widget classes than to define them using pure
  Python. It does however not add any extra functionality. That is,
  every Wwml construct can be mapped into an equivalent Python
  construct, and is indeed compiled to one when the Wwml file is
  loaded. 


The module system
=================

  Wwml integrates with Python and its module system in a way that
  makes Wwml files appear as normal Python modules to a Python
  program. Those modules can be imported and used in the same way as
  ordinary Python modules as long as the Webwidgets module has been
  loaded prior to the attempt to load a Wwml module.

  Wwml also imports Python modules (or Wwml files) along with
  widget definitions for widgets that are used in a Wwml file. When
  referring to widgets Wwml uses Python module paths (e.g.
  C{Module.SubModule.SomeClass.SomeClassWithinTheFirstClass}).

XML syntax
==========

  Wwml is an U{XML<http://www.w3.org/XML/>} application, and uses
  U{XML namespaces<http://www.w3.org/TR/REC-xml-names>} to separate
  embedded HTML code from Wwml code. Wwml tags live in the namespace
  U{http://freecode.no/xml/namespaces/wwml-1.0}. The outermost tag of
  a Wwml document is always the C{wwml} tag which serves the purpose
  of containing namespace declarationsm the callback bindings and
  declaring a search path for widgets::

    <?xml version="1.0"?>
    <w:wwml
     xmlns="http://www.w3.org/TR/REC-html40"
     xmlns:w="http://freecode.no/xml/namespaces/wwml-1.0"
     xmlns:html="http://www.w3.org/TR/REC-html40"
     >

Basic tag structure
===================

  Each tag except for the top-level C{wwml} tag defines a
  widget class. It consists of a tag name, an id attribute, any number
  of attributes, any number of child widgets and an implicit HTML
  format string (if the tag has children).

  The tag name is the name (or module path) of some existing widget
  to subclass and the id attribute defines the name of the new
  class.

  Attributes and children are interchangable and defines class
  variables for the new class. These can hold either child widgets or
  Python values (e.g. strings, integers, lists, dictionaries...).

  Example::
      
    <w:MyModule.MyWidget id="MyFirstWidget" foo="xyzzy">
     <w:OtherModule.SubMod.OtherWidget id="bar" />
    </w:MyModule.MyWidget>
  
  This compiles (roughly) into::

    import MyModule, OtherModule.SubMod

    class MyFirstWidget(MyModule.MyWidget):
        foo="xyzzy"
        class bar(OtherModule.SubMod.OtherWidget):
            pass

Special tags and attribute types
================================
  Wwml allows for attributes to hold values of different types
  (e.g. strings, integers, booleans...). By default an attribute value is
  considered a string. To define an attribute value of a different
  type the attribute value must be prefixed with a C{":type:"},
  (e.g. C{":string:My string value here"}, C{":integer:4711"},
  C{":time:2007-07-31 17:22:05"}).

  These same types are also available as tags to make attributes
  and children more interchangable.

  Example::

    <w:MyModule.MyWidget id="MyFirstWidget" foo=":integer:4711">
     <w:integer id="bar">4712</w:integer>
    </w:MyModule.MyWidget>

HTML format strings
===================

  Wwml is intended to assist in writing complicated user interfaces
  that mixes widgets and static HTML content. To help with this, Wwml
  provides widgets with a special attribute called C{html} that holds
  a Python format string corresponding to the content inside the Wwml
  tag for the widget. All non-wwml content (e.g. HTML tags and text)
  is copied as-is to this attribute while Wwml tags are replaced by
  C{%(id)s}, where id is the value of the C{id} attribute of the child
  tag.

  Example::

    <w:Html id="MySearchBox">
     <div class="SearchBox">
      <w:StringInput id="query" value="*.*" />
      <img src="http://example.org/pic.png" />
      <w:Button id="search" title="Search" />
     </div>
    </w:Html>
  
  This compiles (roughly) into::

    import MyModule, OtherModule.SubMod

    class MySearchBox(Html):
        html = '''
    <div class="SearchBox">
     %(query)s
     <img src="http://example.org/pic.png" />
     %(search)s
    </div>
    '''
    class query(StringInput):
        value = "*.*"
    class search(Button):
        title = "Search"

  This is the foundation for using the C{Html} widget, which
  uses this format string to merge the rendering of its child widgets.
  This widget is useful for implementing fancy layouts, extra CSS
  hooks and intermingle widgets with static text (e.g. labels,
  descriptions, help-texts etc).


Callback binding
================

  A user interface is nothing without interactivity, in Webwidgets
  this is provided by callback functions. Callback functions can not
  be declared within Wwml as Wwml is not a programming language but a
  purely declarative UI definition language. Instead the Wwml widget
  definition has to "bind" to some Python class implementing the
  callbacks.

  A callback class is bound to a widget using the the C{bind}
  attribute which specifies a class with callback methods.

  Example::

    <w:MyModule.MyWidget id="MyFirstWidget" foo="xyzzy" bind="MyCallBacks.MyCallbackClass" />
  
  This compiles into::

    import MyModule, MyCallBacks

    class MyFirstWidget(MyCallBacks.MyCallbackClass, MyModule.MyWidget):
        foo="xyzzy"

  To reduce code overhead, callback binding recurses through
  widgets so that child widgets are bound to member classes:

  Example::

    <w:Html id="MyFirstWidget" bind="MyCallBacks.MyCallbackClass">
     <w:Html id="SomeWidget">
      <w:Button id="SomeButton" title="Push me" />
     </w:Html>
    </w:Html>
  
  This compiles into::

    import MyModule, MyCallBacks

    class MyFirstWidget(MyCallBacks.MyCallbackClass, html):
        class SomeWidget(MyCallBacks.MyCallbackClass.SomeWidget, Html):
            class MyFirstWidget(MyCallBacks.MyCallbackClass.SomeWidget.SomeButton, Button):
                title = "Push me"

Search paths for widgets
========================

  As already stated tag names are module paths to existing widget
  classes. But these paths need not be complete - they are looked up
  along a search path of modules.

  Consider a search path consisting of C{MyProg.UI},
  C{MyLib.Widgets} and C{Webwidgets}. The tag
  C{<w:Foo.SomeWidget />} then results in a lookup for

    - C{MyProg.UI.Foo.SomeWidget}
    - C{MyLib.Widgets.Foo.SomeWidget}
    - C{Webwidgets.Foo.SomeWidget}
   
  and the first existing class in that list will be used.

  Search paths can be overridden for any widget and its children by
  specifying the C{using} attribute. The contents of this attribute is
  a space separated list of module paths which is prepended to the
  search path used to lookup the widget and all its children::

    <w:Html id="MyFirstWidget" using="Webwidgets" >
     <w:Html id="SomeWidget" using="MyProg.UI MyLib.Widgets">
      <w:Button id="SomeButton" title="Push me" />
     </w:Html>
    </w:Html>
"""

import Webwidgets.Widgets.Base, Utils
import xml.dom.minidom, pyexpat
import os.path, sys, types, time, datetime

debug_loader = False
debug_subclass = False
debug_childmerge = False

xml_namespace_wwml = 'http://freecode.no/xml/namespaces/wwml-1.0'
xml_namespace_html = 'http://www.w3.org/TR/REC-html40'

def generate_error_for_value(message, message_details, widget, attributes = {}):
    return TypeError("""%(message)s: %(message_details)s
    Widget: %(widget)s
%(attributes)s""" % {'message': message,
                     'message_details': message_details,
                     'widget': widget,
                     'attributes': '\n'.join("    %s: %s" % (name, value) for (name, value) in attributes.iteritems())})

def generate_error_for_widget(message, message_details, class_path, class_name, base_classes, attributes = {}):
    return generate_error_for_value(message, message_details,
                                    "%(class_path)s(%(base_classes)s)" % {'class_path': '.'.join(class_path + [class_name]),
                                                                          'base_classes': ', '.join(str(cls) for cls in base_classes)},
                                    attributes)

def preprocess_node(module, node, using = [], class_path = [], bind_context = [], html_context = []):
    # The following pre-processing transforms
    #
    #     <w:Foo id="Bar">
    #      <w:Foo.Bar.Fie.Naja id="Bar.Fie.Naja" />
    #     </w:Foo>
    #
    # into
    #
    #     <w:Foo id="Bar">
    #      <w:Foo.Bar id="Bar">
    #       <w:Foo.Bar.Fie.Naja id="Fie.Naja" />
    #      </w:Foo.Bar>
    #     </w:Foo>
    #
    # Note that this only happens one step at a time, as the child
    # nodes (of the Bar node in the example above), whill be mangled
    # the same way too in a later call to generate_parts_for_node.
    
    sub_children = Utils.OrderedDict()

    doc = node.ownerDocument
    
    for pos in xrange(len(node.childNodes) - 1, -1, -1):
        child = node.childNodes[pos]
        if child.nodeType != doc.ELEMENT_NODE or child.namespaceURI != xml_namespace_wwml: continue
        id_type = ['classid', 'id'][child.hasAttribute('id')]
        if not child.hasAttribute(id_type): continue
        node_id_attr = child.attributes[id_type]
        node_id = node_id_attr.value
        if '.' not in node_id: continue

        top, rest = node_id.split('.', 1)
        if top not in sub_children:
            sub_children[top] = []

        child.setAttribute(id_type, rest)
        
        sub_children[top].append(child)
        del node.childNodes[pos]

    for child in node.childNodes:
        if child.nodeType != doc.ELEMENT_NODE or child.namespaceURI != xml_namespace_wwml: continue
        node_id = child.attributes.get('id', child.attributes.get('classid', None))
        if node_id is None: continue
        node_id = node_id.value
        if node_id in sub_children:
            child.childNodes.extend(sub_children[node_id])
            del sub_children[node_id]

    for name, children in sub_children.iteritems():
        container = doc.createElement(node.tagName + '.' + name)
        container.namespaceURI = node.namespaceURI
        container.setAttribute('id', name)
        container.childNodes.extend(children)
        node.childNodes.append(container)

def generate_parts_for_node(module, node, using = [], class_path = [], bind_context = [], html_context = []):
    attributes = []
    texts = []
    preprocess_node(module, node, using, class_path, bind_context, html_context)
    for child in node.childNodes:
        if child.nodeType == node.TEXT_NODE:
            texts.append(child.data)
        elif child.nodeType == node.ELEMENT_NODE:
            if child.namespaceURI == xml_namespace_wwml:
                if child.localName == 'variable':
                     texts.append("%(" + child.attributes.get('id').value + ")s")
                elif child.localName == 'pre':
                    sub_attrs, sub_text = generate_parts_for_node(module, child, using, class_path, bind_context, html_context)
                    attributes = sub_attrs + attributes
                    attributes.append((':pre', sub_text))
                elif child.localName == 'post':
                    sub_attrs, sub_text = generate_parts_for_node(module, child, using, class_path, bind_context, html_context)
                    attributes.extend(sub_attrs)
                    attributes.append((':post', sub_text))
                else:
                    id, classid, value = generate_value_for_node(module, child, using, class_path, bind_context)
                    if isinstance(value, types.TypeType):
                        if issubclass(value, Webwidgets.Widgets.Base.Widget) and id:
                            texts.append("%(" + id + ")s")
                        #else:
                        #    print "NOT A SUBCLASS:", id
                    attributes.append((classid, value))
            elif child.namespaceURI == xml_namespace_html:
                child_attributes_values = dict(child.attributes.items())
                child_attributes, child_texts = generate_parts_for_node(
                    module,
                    child,
                    using,
                    class_path,
                    bind_context,
                    html_context = html_context + [child_attributes_values.get('id', child.localName)])
                if 'id' in child_attributes_values:
                    child_attributes_values['id'] = "%(html_id)s_" + "-".join(html_context + [child_attributes_values['id']])
                if child.localName in ('br', ):
                    texts.append("<")
                    texts.append(child.localName)
                    texts.append(" ")
                    texts.extend(["%s='%s'" % item
                                  for item
                                  in child_attributes_values.iteritems()])
                    texts.append(" />\n")
                    
                else:
                    texts.append("<")
                    texts.append(child.localName)
                    texts.append(" ")
                    texts.extend(["%s='%s'" % item
                                  for item
                                  in child_attributes_values.iteritems()])
                    texts.append(">\n")
                    texts.append(child_texts)
                    texts.append("</")
                    texts.append(child.localName)
                    texts.append(">\n")
                attributes.extend(child_attributes)
    return attributes, ''.join(texts)

def merge_child_widgets(module, widget, binding, attributes={}, name=None, indent = ''):
    name = name or '%sMerged' % (widget.__name__, )

    if debug_childmerge:
        print indent, "MERGING %s as %s with %s IN %s..." % (name, str(widget), str(binding), str(module))

    merged_members = {}

    if binding:
        for child_name in dir(binding):
            widget_member = getattr(widget, child_name, None)
            binding_member = getattr(binding, child_name, None)
            if ( widget_member is not binding_member
                 and not child_name.startswith('__')
                 and child_name not in attributes
                 and isinstance(widget_member, type)
                 and issubclass(widget_member, Webwidgets.Widget)
                 and isinstance(binding_member, type)):
                merged_members[child_name] = merge_child_widgets(module, widget_member, binding_member, indent = indent + '    ')
            elif getattr(binding_member, "ww_bind_widget", None) == "require":
                raise TypeError("No child widget for binding %s in widget %s" % (binding_member, widget))

    # Override merged members with attributes from WWML
    merged_members.update(attributes)

    # Binding can be widget if we are merging children of a binding
    # that inherits from the superclass of the widget it is bound
    # to...
    if not binding or binding is widget:
        base_cls = (widget, )
    else:
        base_cls = (binding, widget)

    try:
        return types.TypeType(name, base_cls, merged_members)
    except TypeError, e:
        raise TypeError("""Unable to instantiate widget: %s
    In: %s
    Widget: %s(%s)""" % (
                str(e),
                module,
                name,
                ', '.join([str(cls) for cls in base_cls]),
                ))


wwml_bind_status_names = ['require',
                          'forbid',
                          'dont-require',
                          'fallback']

def generate_value(type_name, text, attributes, module, using, class_path, bind_context):
    """Binding:

    Source:   Wwml         Widget class        Callback class       Result: Bind is
    Variable: bind         ww_bind_callback    ww_bind_widget
    |         require                                               required
    |         forbid                                                forbidden
    |         dont-require                     dont-require         allowed
    |         dont-require                     require              required
    |         fallback     forbid                                   forbidden
    |         fallback     require                                  required
    |         fallback     dont-require        dont-require         allowed
    |         fallback     dont-require        require              required
    """

    value_classid = attributes.get('classid', None)
    value_id = attributes.get('id', None)
    if 'classid' in attributes: del attributes['classid']
    if 'id' in attributes: del attributes['id']

    if type_name == 'false': value = False
    elif type_name == 'true': value = True
    elif type_name == 'none': value = None
    elif type_name == 'string': value = text
    elif type_name == 'id': value = Utils.id_to_path(text)
    elif type_name == 'path': value = Utils.WidgetPath(text, path_as_list = True)
    elif type_name == 'integer': value = int(text)
    elif type_name == 'float': value = float(text)
    elif type_name == 'time': value = datetime.datetime(*(time.strptime(text, '%Y-%m-%d %H:%M:%S')[0:6]))
    elif type_name == 'odict':
        value = Utils.OrderedDict(attributes)
    elif type_name == 'dict':
        value = dict(attributes)
    elif type_name == 'list':
        value = attributes.values()
    else:
        callback_name = '.'.join(bind_context)
        if debug_subclass:
            if type_name != 'wwml':
                print "WWML: class %s(%s, %s): pass" % ('.'.join(class_path + [value_classid]), callback_name, type_name)
                print "WWML:     using: %s" % ' '.join(using)

        wwml_bind_status = attributes.get('bind', 'fallback')

        node_value = None
        if type_name != 'wwml':
            node_value = Utils.load_class(type_name, using, module = module)
        widget_bind_status = getattr(node_value, 'ww_bind_callback', "dont-require")

        bind_status = widget_bind_status
        if wwml_bind_status != "fallback":
            bind_status = wwml_bind_status
        
        binding = None
        try:
            binding = Utils.load_class(callback_name, using, module = module)
        except ImportError, e:
            if bind_status == "require":
                print "widget_bind_status", widget_bind_status
                print "wwml_bind_status", wwml_bind_status
                raise

        callback_bind_status = getattr(binding, 'ww_bind_widget', "fallback")
        if callback_bind_status != "fallback":
            bind_status = callback_bind_status

        if binding is not None and bind_status == "forbid":
            raise generate_error_for_widget("Binding forbidden but present anyway", "",
                                            class_path, value_id or value_classid, (type_name, binding))

        if type_name == 'wwml':
            value = module
            for k, v in attributes.iteritems():
                setattr(value, k, v)
            value_classid = 'wwml'
        else:
            if isinstance(node_value, types.TypeType) and issubclass(node_value, Webwidgets.Widgets.Base.Widget):
                if 'html' not in attributes and hasattr(node_value, '__wwml_html_override__') and node_value.__wwml_html_override__:
                    attributes['html'] = text

                if ':pre' in attributes or ':post' in attributes:
                    if 'html' not in attributes:
                        attributes['html'] = getattr(node_value, 'html', '')

                    if ':pre' in attributes:
                        attributes['html'] = attributes[':pre'] + attributes['html']
                        del attributes[':pre']
                    if ':post' in attributes:
                        attributes['html'] = attributes['html'] + attributes[':post']
                        del attributes[':post']

                if value_id is None:
                    attributes['ww_explicit_load'] = True
                if '__wwml_html_override__' not in attributes:
                    attributes['__wwml_html_override__'] = False
                attributes['ww_bind_callback'] = 'dont-require'
                attributes['__module__'] = module.__name__

                # Create class
                if debug_childmerge:
                    print "MERGE TOP LEVEL", node_value, binding, module
                value = merge_child_widgets(module, node_value, binding, attributes, str(value_classid))

            elif hasattr(node_value, '__iter__'):
                value = Utils.OrderedDict(attributes)
                if hasattr(node_value, 'iteritems'):
                    value = Utils.subclass_dict(node_value, value)
                else:
                    value = Utils.subclass_list(node_value, value.values())
            else:
                #value = node_value
                raise generate_error_for_widget("Unable to inherit from specified object:",
                                                "Object must be a subclass of Widget, a list or a dict",
                                                class_path, value_id or value_classid, (type_name, ))
    return value_id, value_classid, value

def generate_value_for_attribute(attribute, text, module, using, class_path, bind_context):
    if not text.startswith(':'):
        return text
    text = text[1:]
    if ':' in text:
        type_name, text = text.split(':', 1)
    else:
        type_name = text
        text = None
    return generate_value(type_name, text,
                          {'id': attribute, 'classid': attribute},
                          module, using, class_path + [attribute], bind_context + [attribute]
                          )[2]

def generate_value_for_node(module, node, using = [], class_path = [], bind_context = [], is_root_node = False):
    if not node.nodeType == node.ELEMENT_NODE:
        raise Exception('Non element node given to generate_value_for_node: %s' % str(node))

    sys_attributes = {}
    if is_root_node:
        if not node.localName == 'wwml':
            raise Exception('The root node must be a wwml tag: %s' % str(node))
        if node.attributes.has_key('id') or node.attributes.has_key('classid'):
            raise Exception('The root node must not have an id or classid: %s' % str(node))
        sys_attributes['classid'] = 'wwml'
    else:
        if node.attributes.has_key('id') == node.attributes.has_key('classid'):
            raise Exception('One of classid and id, and only one, must be set for an object: %s' % str(node))

        if node.attributes.has_key('id'):
            sys_attributes['classid'] = node.attributes['id'].value
        else:
            sys_attributes['classid'] = node.attributes['classid'].value

    if node.attributes.has_key('using'):
        using = node.attributes['using'].value.split(' ') + using

    # If bind is the name of a class or module, set that as
    # bind-context, otherwize append the name of the widget to the
    # bind context of the parent widget.
    if node.attributes.has_key('bind') and node.attributes['bind'].value not in wwml_bind_status_names:
        bind_context = node.attributes['bind'].value.split('.')
    else:
        bind_context = bind_context + [sys_attributes.get('classid', '__unknown__')]

    if is_root_node:
        class_path = []
    else:
        class_path = class_path + [sys_attributes.get('classid', '__unknown__')]

    # Yes, ordered dict here, since we mix it with child nodes further
    # down, and they _do_ have order... A pity really XMl doesn't
    # preserve the order of attributes...
    attributes = Utils.OrderedDict([(key, generate_value_for_attribute(key, value, module, using, class_path, bind_context))
                                    for (key, value)
                                    in node.attributes.items()])

    children, text = generate_parts_for_node(module, node, using, class_path, bind_context)
    attributes.update(children)

    attributes.update(sys_attributes)

    return generate_value(node.localName,
                          text,
                          attributes,
                          module,
                          using,
                          class_path,
                          bind_context)


def generate_widgets_from_file(modulename, filename, file, path = None, bind_context = ''):
    if debug_loader: print "generate_widgets_from_file(%s, %s)" % (modulename, filename)
    if bind_context:
        bind_context = bind_context.split('.')
    else:
        bind_context = []
    module = types.ModuleType(modulename)
    module.__file__ = filename
    if path is not None:
        module.__path__ = path
    sys.modules[modulename] = module
    if '.' in modulename:
        module_parts = modulename.split('.')
        parent = '.'.join(module_parts[:-1])
        setattr(sys.modules[parent], module_parts[-1], module)
    try:
        root_node = xml.dom.minidom.parse(file)
        dom_node = root_node.getElementsByTagNameNS(
            xml_namespace_wwml, 'wwml')[0]
        return generate_value_for_node(
            module,
            dom_node,
            ['Webwidgets'],
            [],
            bind_context,
            True)[2]
    except Exception, e:
        if e.args:
            e.args = ("Unable to parse file %s:\n%s" % (filename, e.args[0]),) + e.args[1:]
        else:
            e.args = ("Unable to parse file %s" % (filename,),)
        raise type(e), e, sys.exc_info()[2]

import imp, ihooks

class WwmlFile(object): pass

class WwmlHooks(ihooks.Hooks):
    def get_suffixes(self):
        # add our suffixes
        return [('.wwml', 'r', WwmlFile)] + imp.get_suffixes()

class WwmlLoader(ihooks.ModuleLoader):
    def load_module(self, name, (file, filename, (suff, mode, type))):
        if debug_loader: print "WwmlLoader.load_module(%s, %s, %s)" % (name, filename, (suff, mode, type))
        # If it's a Wwml file, load it ourselves:
        if type is WwmlFile:
            return generate_widgets_from_file(name, filename, file)
        # This is needed because for some reason, ihooks can't figure
        # this out by itself!
        elif type is ihooks.PKG_DIRECTORY:
            wwml_init = os.path.join(filename, '__init__.wwml')
            if os.access(wwml_init, os.F_OK):
                wwml_file = open(wwml_init)
                try:
                    return generate_widgets_from_file(name, wwml_init, wwml_file, [filename])
                finally:
                    wwml_file.close()
            else:
                return ihooks.ModuleLoader.load_module(self, name, (file, filename, (suff, mode, type)))
        else:
            # Otherwise, use the default handler for loading
            return ihooks.ModuleLoader.load_module(self, name, (file, filename, (suff, mode, type)))

class ModuleImporter(ihooks.ModuleImporter):
    def find_head_package(self, parent, name):
        if '.' in name:
            i = name.find('.')
            head = name[:i]
            tail = name[i+1:]
        else:
            head = name
            tail = ""
        if parent:
            qname = "%s.%s" % (parent.__name__, head)
        else:
            qname = head
        q = self.import_it(head, qname, parent)
        if q: return q, (tail, name)
        if parent:
            qname = head
            parent = None
            q = self.import_it(head, qname, parent)
            if q: return q, (tail, name)
        raise Utils.LocalizedImportError(name, "No module named " + qname)

    def load_tail(self, q, (tail, name)):
        m = q
        while tail:
            i = tail.find('.')
            if i < 0: i = len(tail)
            head, tail = tail[:i], tail[i+1:]
            mname = "%s.%s" % (m.__name__, head)
            m = self.import_it(head, mname, m)
            if not m:
                raise Utils.LocalizedImportError(name, "No module named " + mname)
        return m

ihooks.install(ModuleImporter(WwmlLoader(WwmlHooks())))


