#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

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

def generate_parts_for_node(module, node, using = [], class_path = [], bind_context = [], html_context = []):
    attributes = []
    texts = []
    for child in node.childNodes:
        if child.nodeType == node.TEXT_NODE:
            texts.append(child.data)
        elif child.nodeType == node.ELEMENT_NODE:
            if child.namespaceURI == 'http://freecode.no/xml/namespaces/wwml-1.0':
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
            elif child.namespaceURI == 'http://www.w3.org/TR/REC-html40':
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
            base_cls = ()
            try:
                base_cls += (Utils.load_class(callback_name, using, module = module),)
            except ImportError, e:
                pass
            base_cls += (node_value,)

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
            try:
                value = types.TypeType(str(attributes['classid']),
                                       base_cls,
                                       attributes)
            except TypeError, e:
                raise TypeError("Unable to instantiate widget in %s: %s(%s): %s" % (
                    module,
                    str(attributes['classid']),
                    ', '.join([str(cls) for cls in base_cls]),
                    str(e)))
        elif hasattr(node_value, '__iter__'):
            value = dict(attributes)
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

def generate_value_for_node(module, node, using = [], class_path = [], bind_context = []):
    if not node.nodeType == node.ELEMENT_NODE:
        raise Exception('Non element node given to generate_value_for_node: %s' % str(node))
    # Yes, ordered dict here, since we mix it with child nodes further
    # down, and they _do_ have order... A pity really XMl doesn't
    # preserve the order of attributes...
    attributes = Utils.OrderedDict([(key, mangle_attribute_value(key, value, module, using, class_path, bind_context))
                                    for (key, value)
                                    in node.attributes.items()])

    if 'id' in attributes:
        if 'classid' not in attributes:
            attributes['classid'] = attributes['id']
        else:
            raise Exception('Both classid and id can not be set for an object')

    if 'using' in attributes:
        using = attributes['using'].split(' ') + using

    if 'bind' in attributes:
        bind_context = attributes['bind'].split('.')
    else:
        bind_context = bind_context + [attributes.get('classid', '__unknown__')]

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
    except Exception, e:
        e.args = ("Unable to parse file %s: %s" % (filename, e.args[0]),) + e.args[1:]
        raise e
    dom_node = root_node.getElementsByTagNameNS(
        'http://freecode.no/xml/namespaces/wwml-1.0', 'wwml')[0]
    return generate_value_for_node(
        module,
        dom_node,
        ['Webwidgets'],
        [],
        bind_context)[2]

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

ihooks.install(ihooks.ModuleImporter(WwmlLoader(WwmlHooks())))


