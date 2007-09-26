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

"""Output formatting widgets.
"""

import types, StringIO, cgi
import Webwidgets.Utils, Webwidgets.Constants
import Base, TableModel

class List(Base.StaticComposite):
    """Concatenates all children in name order, drawing the "sep"
    child inbetween each and the "pre" and "post" children before and
    after the whole list, respectively. Note: sep should not be an
    input widget, or all hell breaks lose."""
    __no_classes_name__ = True
    __children__ = ('pre', 'sep', 'post')
    pre = sep = post = ''
    def draw(self, outputOptions):
        children = self.drawChildren(outputOptions)
        return children['pre'] + children['sep'].join([child
                                                       for name, child in children.iteritems()
                                                       if name not in ('pre', 'sep', 'post')]) + children['post']

class Html(Base.StaticComposite):
    """This widget is the base widget for most output widgets and the
    main method of concatenating and grouping widgets. It provides a
    way to "format" together other widgets with some custom HTML
    around them.

    @cvar html: The "html" attribute should contain HTML code with python format strings like
    %(name)s embedded. These should correspond to children of the html
    widget, or if prefixed with 'attr_', to attributes. In addition
    the special name"id" will insert the widget id (path) of the current widget, which is usefull
    for CSS styling).
    """
    __no_classes_name__ = True
    """Don't include the classname of this class in L{classes}."""
    __wwml_html_override__ = True
    """Let Wwml-defined subclasses override the html attribute"""
    __attributes__ = Base.StaticComposite.__attributes__ + ('html','topLevel')
    html = ''
    topLevel = None
    def draw(self, outputOptions):
        children = self.drawChildren(
            outputOptions,
            invisibleAsEmpty = True,
            includeAttributes = True)
        try:
            html = self.html
            if self.topLevel is not None:
                html = "<%(attr_topLevel)s %(attr_htmlAttributes)s>" + html + "</%(attr_topLevel)s>"
            return html % children
        except KeyError, e:
            e.args = (self, self.path) + e.args + (self.html,)
            raise e

class Div(Html):
    """Adds a single div with the widget id as id around the single
    child "child"
    """
    __no_classes_name__ = True
    __wwml_html_override__ = False
    __children__ = Html.__children__ + ('child',)
    html = """<div %(attr_htmlAttributes)s>%(child)s</div>"""

class Span(Html):
    """Adds a single span with the widget id as id around the single
    child "child"
    """
    __no_classes_name__ = True
    __wwml_html_override__ = False
    __children__ = Html.__children__ + ('child',)
    html = """<span %(attr_htmlAttributes)s>%(child)s</span>"""

class Style(Html):
    """Includes the css style from the child "style"
    """
    __children__ = Html.__children__ + ('style',)
    __wwml_html_override__ = False
    style = ''
    html = """<style %(attr_htmlAttributes)s type='text/css'>%(style)s</style>"""
    
class StyleLink(Html):
    """Includes the css style from the URL specified with the
    attribute "style"
    """
    __attributes__ = Base.Widget.__attributes__ + ('style', 'title')
    __wwml_html_override__ = False
    style = ''
    """URI to the stylesheet to include."""
    title = ''
    html = """<link %(attr_htmlAttributes)s href="%(attr_style)s" title="%(attr_title)s" rel="stylesheet" type="text/css" />"""

class Message(Html):
    """Informative message display. If no message is set, this widget
    is invisible."""
    __wwml_html_override__ = False
    __children__ = Html.__children__ + ('message',)
    message = ''
    def draw(self, outputOptions):
        if self.children['message']:
            self.html = '<div %(attr_htmlAttributes)s>%(message)s</div>'
        else:
            self.html = ''
        return Html.draw(self, outputOptions)

class Media(Base.Widget):
    """Media (file) viewing widget"""
    __attributes__ = ('content', 'base', 'types')
    content = None
    class Base(object): pass
    base = Base()
    base.type = 'text/html'
    base.file = StringIO.StringIO("""
<html>
 <head>
  %(content)s
 </head>
 <body>
  <p>
   <h1>Head1</h1>
   <p>Some text.</p>
   <p>
    <h2>Head1</h2>
    <p>Some text and <a href='http://google.com'>a link</a>.</p>
   </p>
  </p>
 </body>
</html>
""")

    types = {'default':{'width':None,  # All
                        'height':None,
                        'empty': '&lt;No file&gt;',
                        'inline':True,
                        'merge':False,
                        'invisible':False},
             'image/png':{'inline':True},
             'image/jpeg':{'inline':True},
             'image/gif':{'inline':True},
             'text/css':{'inline':True, 'merge':False, 'invisible':False},
             'text/html':{'inline':True, 'merge':False, 'invisible':False}}

    def getOption(self, option):
        mimeType = getattr(self.content, 'type', 'default')
        if mimeType in self.types and option in self.types[mimeType]:
            return self.types[mimeType][option]
        return self.types['default'][option]

    def getHtmlOption(self, option, htmlName = None):
        value = self.getOption(option)
        if value is None:
            return ''
        if htmlName is None: htmlName = option
        return '%s = "%s"' % (htmlName, value)

    def getRenderer(self, renderer):
        mimeType = getattr(self.content, 'type', None)
        resName = renderer + '_default'
        if mimeType is not None:
            name = renderer + "_" + mimeType.replace("/", "__").replace("-", "_")
            if hasattr(self, name):
                resName = name
        return getattr(self, resName)

    def calculateOutputUrl(self, part = 'content'):
        return self.calculateUrl({'widget': Webwidgets.Utils.pathToId(self.path), 'part':part})

    def output(self, outputOptions):
        content = ''
        mimeType = 'text/plain'
        if outputOptions['part'] == 'content':
            if self.content is not None:
                self.content.file.seek(0)
                content = self.content.file.read()
                mimeType = self.content.type
        elif outputOptions['part'] == 'base':
            if self.base is not None:
                self.base.file.seek(0)
                content = self.base.file.read() % self.getRenderer('base_include')(outputOptions)
                mimeType = self.base.type
        return {Webwidgets.Constants.OUTPUT: content,
                'Content-type': mimeType}

    def draw(self, outputOptions):
        if self.getOption('inline'):
            inlineRenderer = self.getRenderer('draw_inline')
        else:
            inlineRenderer = self.draw_inline_default
        inline = inlineRenderer(outputOptions)


        if self.getOption('invisible'):
            return ''

        if self.content is None:
            return self.getOption('empty')

        return """<a %(attr_htmlAttributes)s href="%(location)s">%(inline)s</a>""" % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'location': cgi.escape(self.calculateOutputUrl()),
            'inline': inline
            }

    def draw_inline_default(self, outputOptions):
        return getattr(self.content, 'filename', self.getOption('empty'))

    def base_include_default(self, outputOptions):
        return {'content': cgi.escape(self.calculateOutputUrl())}


    def draw_inline_image(self, outputOptions):
        return """<img src="%(location)s" alt="%(name)s" %(width)s %(height)s />""" % {
            'location': cgi.escape(self.calculateOutputUrl()),
            'name': self.draw_inline_default(outputOptions),
            'width': self.getHtmlOption('width'),
            'height': self.getHtmlOption('height')
            }
    
    draw_inline_image__png = draw_inline_image
    draw_inline_image__jpeg = draw_inline_image
    draw_inline_image__gif = draw_inline_image
    
    def draw_inline_text__css(self, outputOptions):
        if self.getOption('merge'):
            self.registerStyleLink(self.calculateOutputUrl())
            return self.draw_inline_default(outputOptions)
        else:
            return """<iframe src="%(location)s" title="%(name)s" %(width)s %(height)s></iframe>
                  %(name)s""" % {
            'location': cgi.escape(self.calculateOutputUrl('base')),
            'name': self.draw_inline_default(outputOptions),
            'width': self.getHtmlOption('width'),
            'height': self.getHtmlOption('height')
            }
    def base_include_text__css(self, outputOptions):
        return {'content':"<link href='%s' rel='stylesheet' type='text/css' />" % (cgi.escape(self.calculateOutputUrl()),)}

    def draw_inline_application__x_javascript(self, outputOptions):
        if self.getOption('merge'):
            self.registerScriptLink(self.calculateOutputUrl())
            return self.draw_inline_default(outputOptions)
        else:
            return """<iframe src="%(location)s" title="%(name)s" %(width)s %(height)s></iframe>
                  %(name)s""" % {
            'location': cgi.escape(self.calculateOutputUrl('base')),
            'name': self.draw_inline_default(outputOptions),
            'width': self.getHtmlOption('width'),
            'height': self.getHtmlOption('height')}
        
    def base_include_application__x_javascript(self, outputOptions):
        return {'content':"<script src='%s' type='text/javascript' ></script>" % (cgi.escape(self.calculateOutputUrl()),)}


    def draw_inline_text(self, outputOptions):
        return """<iframe src="%(location)s" title="%(name)s" %(width)s %(height)s></iframe>
                  %(name)s""" % {
            'location': cgi.escape(self.calculateOutputUrl()),
            'name': self.draw_inline_default(outputOptions),
            'width': self.getHtmlOption('width'),
            'height': self.getHtmlOption('height')
            }

    draw_inline_text__plain = draw_inline_text
    draw_inline_text__html = draw_inline_text
    draw_inline_text__xml = draw_inline_text

class Label(Base.StaticComposite):
    """Renders a label for an input field. The input field can be
    specified either as the widget itself, or a
    L{Webwidgets.Utils.RelativePath} to the widget"""
    
    __attributes__ = Base.StaticComposite.__attributes__ + ('target',)
    __children__ = ('label',)

    target = []
    """The widget this widget is a label for. This is either the
    actual widget, or a L{Webwidgets.Utils.RelativePath} referencing
    the widget.
    """

    def draw(self, outputOptions):
        if isinstance(self.target, Base.Widget):
            target = self.target
        else:
            target = self + self.target
        targetPath = target.path
        res = self.drawChildren(outputOptions, includeAttributes = True)
        res['error'] = ''
        if target.error is not None:
           res['error'] = """<span class="error">(%s)</span>""" % (target.error,)
        res['target'] = Webwidgets.Utils.pathToId(targetPath)
        return """<label %(attr_htmlAttributes)s for="%(target)s">
        %(label)s
        %(error)s
        </label>""" % res

class Field(Label):
    __wwml_html_override__ = False
    __children__ = Label.__children__ + ('field',)
    
    def draw(self, outputOptions):
        if isinstance(self.target, Base.Widget):
            target = self.target
        else:
            target = self + ['field'] + self.target
        targetPath = target.path
        res = self.drawChildren(outputOptions, includeAttributes = True)
        res['error'] = ''
        if target.error is not None:
           res['error'] = """<span class="error">(%s)</span>""" % (target.error,)
        res['target'] = Webwidgets.Utils.pathToId(targetPath)
        return """<div %(attr_htmlAttributes)s>
                   <label for="%(target)s">
                    %(label)s%(error)s:
                   </label>
                   <span class="field">
                    %(field)s
                   </span>
                  </div>
                  """ % res

class Fieldgroup(List):
    class pre(Base.Widget):
        def draw(self, outputOptions):
            return """<div %(attr_htmlAttributes)s>""" % {
                'attr_htmlAttributes': self.parent.drawHtmlAttributes(self.parent.path),
                }
    post = "</div>\n"

class Table(Base.StaticComposite, TableModel.Table):
    """Table that works similar to a GtkTable in Gtk - child widgets
    are attatched to cells by coordinates."""
    __attributes__ = Base.StaticComposite.__attributes__ + ('rowWidths', 'colWidths')

    class Cell(TableModel.Table.Cell):
        def name(self):
            return 'cell_' + str(self.x) + '_' + str(self.y) + '_' + str(self.w) + '_' + str(self.h)

    def __init__(self, session, winId, **attrs):
        Base.StaticComposite.__init__(self, session, winId, **attrs)
        TableModel.Table.__init__(self)
        for name, child in self.children.iteritems():
            if name.startswith('cell_'):
                x, y, w, h = self.childName2Coord(name)
                TableModel.Table.insert(self, child, x, y, w, h)
                
    def childName2Coord(self, name):
        dummy, x, y, w, h = name.split('_')
        return (int(x), int(y), int(w), int(h))
    
    def insert(self, content, x, y, w = 1, h = 1):
        cell = TableModel.Table.insert(self, content, x, y, w, h)
        self.children[cell.name()] = content
        
    def remove(self, x, y):
        cell = TableModel.Table.remove(self, x, y)
        if cell: del self.children[cell.name()]
    
    def draw(self, outputOptions):
        children = self.drawChildren(outputOptions)
        result = '<table border="1" %s>\n' % self.drawHtmlAttributes(self.path)
        for y in xrange(0, self.h):
            if y not in self.rowWidths or self.rowWidths[y] > 0:
                result += '<tr>\n'
                for x in xrange(0, self.w):
                    if x not in self.colWidths or self.colWidths[x] > 0:
                        left, right, top, bottom = self.isEdge(x, y)            
                        if left and top:
                            colspan, rowspan = self.visibleSize(x, y)
                            cell = self.cells[y][x]
                            result += '<td colspan="%(colspan)s" rowspan="%(rowspan)s">\n' % {'colspan':colspan, 'rowspan':rowspan}
                            if cell:
                                result += children[cell.name()]
                            result += '</td>\n'
                result += '</tr>\n'
        result += '</table>\n'
        return result
