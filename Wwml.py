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
- Wwml. It has no public classes, functions or members. Instead, when
loaded, Wwml-files can be imported using the ordinary Python methods
of importing modules, e.g.

 >>> import foo

to import the file foo.wwml.

For any introduction to wwml, see the file testwwml.wwml in the
Webwidgets directory.
"""

import Webwidgets.Widgets.Base, Utils
import xml.dom.minidom, pyexpat
import os.path, sys, types, re, time, datetime

debugLoader = False
debugSubclass = False

markupCleanSpaceRe = re.compile(r'[ \t\n]+')
def generatePartsForNode(module, node, using = [], classPath = [], bindContext = [], htmlContext = []):
    attributes = []
    texts = []
    for child in node.childNodes:
        if child.nodeType == node.TEXT_NODE:
            data = markupCleanSpaceRe.sub(' ', child.data).strip()
            if data != '':
                texts.append(data)
        elif child.nodeType == node.ELEMENT_NODE:
            if child.namespaceURI == 'http://freecode.no/xml/namespaces/wwml-1.0':
                if child.localName == 'variable':
                     texts.append("%(" + child.attributes.get('id').value + ")s")
                elif child.localName == 'pre':
                    subAttrs, subText = generatePartsForNode(module, child, using, classPath, bindContext, htmlContext)
                    attributes.extend(subAttrs)
                    attributes.append((':pre', subText))
                elif child.localName == 'post':
                    subAttrs, subText = generatePartsForNode(module, child, using, classPath, bindContext, htmlContext)
                    attributes.extend(subAttrs)
                    attributes.append((':post', subText))
                else:
                    id, classid, value = generateValueForNode(module, child, using, classPath, bindContext)
                    if isinstance(value, types.TypeType):
                        if issubclass(value, Webwidgets.Widgets.Base.Widget) and id:
                            texts.append("%(" + id + ")s")
                        #else:
                        #    print "NOT A SUBCLASS:", id
                    attributes.append((classid, value))
            elif child.namespaceURI == 'http://www.w3.org/TR/REC-html40':
                childAttributesValues = dict(child.attributes.items())
                childAttributes, childTexts = generatePartsForNode(
                    module,
                    child,
                    using,
                    classPath,
                    bindContext,
                    htmlContext = htmlContext + [childAttributesValues.get('id', child.localName)])
                if 'id' in childAttributesValues:
                    childAttributesValues['id'] = "%(attr_html_id)s_" + "-".join(htmlContext + [childAttributesValues['id']])
                if child.localName in ('br', ):
                    texts.append("<")
                    texts.append(child.localName)
                    texts.append(" ")
                    texts.extend(["%s='%s'" % item
                                  for item
                                  in childAttributesValues.iteritems()])
                    texts.append(" />\n")
                    
                else:
                    texts.append("<")
                    texts.append(child.localName)
                    texts.append(" ")
                    texts.extend(["%s='%s'" % item
                                  for item
                                  in childAttributesValues.iteritems()])
                    texts.append(">\n")
                    texts.append(childTexts)
                    texts.append("</")
                    texts.append(child.localName)
                    texts.append(">\n")
                attributes.extend(childAttributes)
    return attributes, ''.join(texts)

def mangleAttributeValue(value):
    if not value.startswith(':'):
        return value
    value = value[1:]
    if ':' in value:
        type, value = value.split(':', 1)
    else:
        type = value
        value = None
    if type == 'false': return False
    elif type == 'true': return True
    elif type == 'none': return None
    elif type == 'string': return value
    elif type == 'id': return Utils.id_to_path(value)
    elif type == 'path': return Utils.RelativePath(value, pathAsList = True)
    elif type == 'integer': return int(value)
    elif type == 'float': return float(value)
    elif type == 'time': return datetime.datetime(*(time.strptime(value, '%Y-%m-%d %H:%M:%S')[0:6]))
    raise Exception("Unknown type: %s for value '%s'" % (type, value))

def generateValueForNode(module, node, using = [], classPath = [], bindContext = []):
    if not node.nodeType == node.ELEMENT_NODE:
        raise Exception('Non element node given to generateValueForNode: %s' % str(node))
    # Yes, ordered dict here, since we mix it with child nodes further
    # down, and they _do_ have order... A pity really XMl doesn't
    # preserve the order of attributes...
    attributes = Utils.OrderedDict([(key, mangleAttributeValue(value))
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
        bindContext = attributes['bind'].split('.')
    else:
        bindContext = bindContext + [attributes.get('classid', '__unknown__')]

    classPath = classPath + [attributes.get('classid', '__unknown__')]

    children, text = generatePartsForNode(module, node, using, classPath, bindContext)
    attributes.update(children)

    if node.localName == 'false': value = False
    elif node.localName == 'true': value = True
    elif node.localName == 'none': value = None
    elif node.localName == 'string': value = text
    elif node.localName == 'id': value = Utils.id_to_path(text)
    elif node.localName == 'path': value = Utils.RelativePath(text, pathAsList = True)
    elif node.localName == 'integer': value = int(text)
    elif node.localName == 'float': value = float(text)
    elif node.localName == 'time': value = datetime.datetime(*(time.strptime(text, '%Y-%m-%d %H:%M:%S')[0:6]))
    elif node.localName == 'odict':
        value = Utils.OrderedDict(attributes)
        if 'classid' in value: del value['classid']
        if 'id' in value: del value['id']
    elif node.localName == 'dict':
        value = dict(attributes)
        if 'classid' in value: del value['classid']
        if 'id' in value: del value['id']
    elif node.localName == 'list':
        value = [value for name, value in attributes.iteritems()
                 if name not in ('classid', 'id')]
    elif node.localName == 'wwml':
        value = module
        for k, v in attributes.iteritems():
            setattr(value, k, v)
        attributes['classid'] = 'wwml'
    else:
        callbackName = '.'.join(bindContext)
        if debugSubclass:
            print "WWML: class %s(%s, %s): pass" % (attributes['classid'], callbackName, node.localName)
            print "WWML:     using: %s" % ' '.join(using)
        nodeValue = Utils.load_class(node.localName, using, module = module)
        if isinstance(nodeValue, types.TypeType) and issubclass(nodeValue, Webwidgets.Widgets.Base.Widget):
            baseCls = ()
            try:
                baseCls += (Utils.load_class(callbackName, using, module = module),)
            except ImportError, e:
                pass
            baseCls += (nodeValue,)

            if 'html' not in attributes and hasattr(nodeValue, '__wwml_html_override__') and nodeValue.__wwml_html_override__:
                attributes['html'] = text

            if ':pre' in attributes or ':post' in attributes:
                if 'html' not in attributes:
                    attributes['html'] = nodeValue.html

                if ':pre' in attributes:
                    attributes['html'] = attributes[':pre'] + attributes['html']
                    del attributes[':pre']
                if ':post' in attributes:
                    attributes['html'] = attributes['html'] + attributes[':post']
                    del attributes[':post']
                    
            if getattr(nodeValue, '__args_children__', False):
                __children__ = ()
                for cls in baseCls:
                    __children__ = getattr(cls, '__children__', __children__)
                __children__ = attributes.get('__children__', __children__)
                __children__ = list(__children__)
                for name, value in attributes.iteritems():
                    if isinstance(value, type) and issubclass(value, Webwidgets.Widgets.Base.Widget) and not value.__explicit_load__:
                        if name not in __children__:
                            __children__.append(name)
                attributes['__children__'] = tuple(__children__)
            if 'id' not in attributes:
                attributes['__explicit_load__'] = True
            if '__wwml_html_override__' not in attributes:
                attributes['__wwml_html_override__'] = False
            attributes['__classPath__'] = '.'.join(classPath[1:-1]) # Remove both the wwml-tag and self
            attributes['__module__'] = module.__name__
            #print baseCls
            try:
                value = types.TypeType(str(attributes['classid']),
                                       baseCls,
                                       attributes)
            except TypeError, e:
                raise TypeError("Unable to instantiate widget in %s: %s(%s): %s" % (
                    module,
                    str(attributes['classid']),
                    ', '.join([str(cls) for cls in baseCls]),
                    str(e)))
        elif hasattr(nodeValue, '__iter__'):
            value = dict(attributes)
            if 'classid' in value: del value['classid']
            if 'id' in value: del value['id']
            if hasattr(nodeValue, 'iteritems'):
                value = Utils.subclass_dict(nodeValue, value)
            else:
                value = Utils.subclass_list(nodeValue, value.values())
        else:
            value = nodeValue
        
    return attributes.get('id', None), attributes.get('classid', None), value


def generateWidgetsFromFile(modulename, filename, file, path = None, bindContext = ''):
    if debugLoader: print "generateWidgetsFromFile(%s, %s)" % (modulename, filename)
    if bindContext:
        bindContext = bindContext.split('.')
    else:
        bindContext = []
    module = types.ModuleType(modulename)
    module.__file__ = filename
    if path is not None:
        module.__path__ = path
    sys.modules[modulename] = module
    if '.' in modulename:
        moduleParts = modulename.split('.')
        parent = '.'.join(moduleParts[:-1])
        setattr(sys.modules[parent], moduleParts[-1], module)
    try:
        domNode = xml.dom.minidom.parse(file).getElementsByTagNameNS(
            'http://freecode.no/xml/namespaces/wwml-1.0', 'wwml')[0]
    except pyexpat.ExpatError, e:
        e.args = ("Unable to parse file %s: %s" % (filename, e.args[0]),) + e.args[1:]
        raise e
    return generateValueForNode(
        module,
        domNode,
        ['Webwidgets'],
        [],
        bindContext)[2]

import imp, ihooks

class WwmlFile(object): pass

class WwmlHooks(ihooks.Hooks):
    def get_suffixes(self):
        # add our suffixes
        return [('.wwml', 'r', WwmlFile)] + imp.get_suffixes()

class WwmlLoader(ihooks.ModuleLoader):
    def load_module(self, name, (file, filename, (suff, mode, type))):
        if debugLoader: print "WwmlLoader.load_module(%s, %s, %s)" % (name, filename, (suff, mode, type))
        # If it's a Wwml file, load it ourselves:
        if type is WwmlFile:
            return generateWidgetsFromFile(name, filename, file)
        # This is needed because for some reason, ihooks can't figure
        # this out by itself!
        elif type is ihooks.PKG_DIRECTORY:
            wwmlInit = os.path.join(filename, '__init__.wwml')
            if os.access(wwmlInit, os.F_OK):
                wwmlFile = open(wwmlInit)
                try:
                    return generateWidgetsFromFile(name, wwmlInit, wwmlFile, [filename])
                finally:
                    wwmlFile.close()
            else:
                return ihooks.ModuleLoader.load_module(self, name, (file, filename, (suff, mode, type)))
        else:
            # Otherwise, use the default handler for loading
            return ihooks.ModuleLoader.load_module(self, name, (file, filename, (suff, mode, type)))

ihooks.install(ihooks.ModuleImporter(WwmlLoader(WwmlHooks())))


