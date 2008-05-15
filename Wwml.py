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

"""This module implements a new, XML-based syntax for defining widgets
- Wwml. It has no public ww_classes, functions or members. Instead, when
loaded, Wwml-files can be imported using the ordinary Python methods
of importing modules, e.g.

 >>> import foo

to import the file foo.wwml.

For any introduction to wwml, see the file testwwml.wwml in the
Webwidgets directory.
"""

import Webwidgets.Widgets.Base, Utils
import xml.dom.minidom, pyexpat
import os.path, sys, types, time, datetime

debug_loader = False
debug_subclass = False
debug_childmerge = False

xml_namespace_wwml = 'http://freecode.no/xml/namespaces/wwml-1.0'
xml_namespace_html = 'http://www.w3.org/TR/REC-html40'

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
            elif getattr(binding_member, "ww_bind", None) == "require":
                raise Exception("No child widget for binding %s in widget %s" % (binding_member, widget))

    # Override merged members with attributes from WWML
    merged_members.update(attributes)

    if binding:
        base_cls = (binding, widget)
    else:
        base_cls = (widget, )

    try:
        return types.TypeType(name, base_cls, merged_members)

    except TypeError, e:
        raise TypeError("Unable to instantiate widget in %s: %s(%s): %s" % (
                module, name,
                ', '.join([str(cls) for cls in base_cls]),
                str(e)))


def generate_value(type_name, text, attributes, module, using, class_path, bind_context):
    if type_name == 'false': value = False
    elif type_name == 'true': value = True
    elif type_name == 'none': value = None
    elif type_name == 'string': value = text
    elif type_name == 'id': value = Utils.id_to_path(text)
    elif type_name == 'path': value = Utils.RelativePath(text, path_as_list = True)
    elif type_name == 'integer': value = int(text)
    elif type_name == 'float': value = float(text)
    elif type_name == 'time': value = datetime.datetime(*(time.strptime(text, '%Y-%m-%d %H:%M:%S')[0:6]))
    elif type_name == 'odict':
        value = Utils.OrderedDict(attributes)
        if 'classid' in value: del value['classid']
        if 'id' in value: del value['id']
    elif type_name == 'dict':
        value = dict(attributes)
        if 'classid' in value: del value['classid']
        if 'id' in value: del value['id']
    elif type_name == 'list':
        value = [value for name, value in attributes.iteritems()
                 if name not in ('classid', 'id')]
    elif type_name == 'wwml':
        value = module
        for k, v in attributes.iteritems():
            setattr(value, k, v)
        attributes['classid'] = 'wwml'
    else:
        callback_name = '.'.join(bind_context)
        if debug_subclass:
            print "WWML: class %s(%s, %s): pass" % (attributes['classid'], callback_name, type_name)
            print "WWML:     using: %s" % ' '.join(using)
        node_value = Utils.load_class(type_name, using, module = module)
        if isinstance(node_value, types.TypeType) and issubclass(node_value, Webwidgets.Widgets.Base.Widget):
            try:
                binding = Utils.load_class(callback_name, using, module = module)
            except ImportError, e:
                binding = None

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
                    
            if 'id' not in attributes:
                attributes['ww_explicit_load'] = True
            if '__wwml_html_override__' not in attributes:
                attributes['__wwml_html_override__'] = False
            attributes['__module__'] = module.__name__

            # Create class
            if debug_childmerge:
                print "MERGE TOP LEVEL", node_value, binding, module
            value = merge_child_widgets(module, node_value, binding, attributes, str(attributes['classid']))

        elif hasattr(node_value, '__iter__'):
            value = Utils.OrderedDict(attributes)
            if 'classid' in value: del value['classid']
            if 'id' in value: del value['id']
            if hasattr(node_value, 'iteritems'):
                value = Utils.subclass_dict(node_value, value)
            else:
                value = Utils.subclass_list(node_value, value.values())
        else:
            value = node_value

    return value

def mangle_attribute_value(attribute, text, module, using, class_path, bind_context):
    if not text.startswith(':'):
        return text
    text = text[1:]
    if ':' in text:
        type_name, text = text.split(':', 1)
    else:
        type_name = text
        text = None
    return generate_value(type_name, text, {'id': attribute, 'classid': attribute}, module, using, class_path, bind_context + [attribute])

def generate_value_for_node(module, node, using = [], class_path = [], bind_context = [], is_root_node = False):
    if not node.nodeType == node.ELEMENT_NODE:
        raise Exception('Non element node given to generate_value_for_node: %s' % str(node))
    # Yes, ordered dict here, since we mix it with child nodes further
    # down, and they _do_ have order... A pity really XMl doesn't
    # preserve the order of attributes...
    attributes = Utils.OrderedDict([(key, mangle_attribute_value(key, value, module, using, class_path, bind_context))
                                    for (key, value)
                                    in node.attributes.items()])

    if ('id' in attributes) == ('classid' in attributes) and not is_root_node:
        raise Exception('One of classid and id, and only one, must be set for an object: %s' % str(node))

    if 'id' in attributes:
        attributes['classid'] = attributes['id']

    if 'using' in attributes:
        using = attributes['using'].split(' ') + using

    # If bind="require" we ignore it, for all purposes except the
    # forced loading below.
    if 'bind' in attributes and attributes['bind'] != 'require':
        bind_context = attributes['bind'].split('.')
    else:
        bind_context = bind_context + [attributes.get('classid', '__unknown__')]

    if 'bind' in attributes:
        # Just check that it exists and barf otherwize - we'll load it
        # again later when we actually need it or a part of it (at
        # this point, it does not matter if the name points to a class
        # or just to a module).
        Utils.load_class('.'.join(bind_context), using, module = module)

    class_path = class_path + [attributes.get('classid', '__unknown__')]

    children, text = generate_parts_for_node(module, node, using, class_path, bind_context)
    attributes.update(children)

    return (attributes.get('id', None),
            attributes.get('classid', None),
            generate_value(node.localName,
                          text,
                          attributes,
                          module,
                          using,
                          class_path,
                          bind_context))


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
        e.args = ("Unable to parse file %s: %s" % (filename, e.args[0]),) + e.args[1:]
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


