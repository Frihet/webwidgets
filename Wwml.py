# Webwidgets web developement framework
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
import os.path, sys, types, re, time

debugLoader = False
debugSubclass = False

markupCleanSpaceRe = re.compile(r'[ \t\n]+')
def generatePartsForNode(module, node, using = [], context = [], htmlContext = []):
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
                else:
                    id, classid, value = generateValueForNode(module, child, using, context)
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
                    context,
                    htmlContext = htmlContext + [childAttributesValues.get('id', child.localName)])
                childAttributesValues['id'] = "%(attr_html_id)s_" + "-".join(htmlContext + [childAttributesValues.get('id', child.localName)])
                texts.extend(["<",
                              child.localName,
                              " ",
                              " ".join(["%s='%s'" % item
                                        for item
                                        in childAttributesValues.iteritems()]),
                              ">\n",
                              childTexts,
                              "</", child.localName, ">\n"])
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
    elif type == 'integer': return int(value)
    elif type == 'float': return float(value)
    elif type == 'time': return time.strptime(value, '%Y-%m-%d %H:%M:%S')
    raise Exception("Unknown type: %s for value '%s'" % (type, value))

def generateValueForNode(module, node, using = [], context = []):
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

    if node.localName not in ('wwml', 'widgets'):
        if 'bind' in attributes:
            context = attributes['bind'].split('.')
        else:
            context = context + [attributes.get('classid', '__unknown__')]

    children, text = generatePartsForNode(module, node, using, context)
    attributes.update(children)

    if node.localName == 'false': value = False
    elif node.localName == 'true': value = True
    elif node.localName == 'none': value = None
    elif node.localName == 'string': value = text
    elif node.localName == 'integer': value = int(text)
    elif node.localName == 'float': value = float(text)
    elif node.localName == 'time': value = time.strptime(text, '%Y-%m-%d %H:%M:%S')
    elif node.localName == 'odict':
        value = Utils.OrderedDict(attributes)
        if 'classid' in value: del value['classid']
        if 'id' in value: del value['id']
    elif node.localName == 'dict':
        value = dict(attributes)
        if 'classid' in value: del value['classid']
        if 'id' in value: del value['id']
    elif node.localName == 'list':
        value = dict(attributes)
        if 'classid' in value: del value['classid']
        if 'id' in value: del value['id']
        value = value.values()
    elif node.localName == 'wwml':
        value = module
        for k, v in attributes.iteritems():
            setattr(value, k, v)
        attributes['classid'] = 'wwml'
    else:
        callbackName = '.'.join(context)
        if debugSubclass:
            print "WWML: class %s(%s): pass" % (callbackName, node.localName)
            print "WWML:     using: %s" % ' '.join(using)
        widgetCls = Utils.loadClass(node.localName, using, module = module)
        baseCls = ()
        try:
            baseCls += (Utils.loadClass(callbackName, using, module = module),)
        except ImportError, e:
            pass
        baseCls += (widgetCls,)

        if 'html' not in attributes and hasattr(widgetCls, '__wwml_html_override__') and widgetCls.__wwml_html_override__:
            attributes['html'] = text
        if 'id' not in attributes:
            attributes['__explicit_load__'] = True
        if '__wwml_html_override__' not in attributes:
            attributes['__wwml_html_override__'] = False
        attributes['__module__'] = '.'.join(context[:-1])
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
        
    return attributes.get('id', None), attributes.get('classid', None), value


def generateWidgetsFromFile(modulename, filename, file, path = None, context = ''):
    if debugLoader: print "generateWidgetsFromFile(%s, %s)" % (modulename, filename)
    if context:
        context = context.split('.')
    else:
        context = []
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
        [], context)[2]

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


