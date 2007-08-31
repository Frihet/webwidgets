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

import types
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
    __attributes__ = Base.StaticComposite.__attributes__ + ('html',)
    html = ''
    def draw(self, outputOptions):
        children = self.drawChildren(
            outputOptions,
            invisibleAsEmpty = True,
            includeAttributes = True)
        try:
            return self.html % children
        except KeyError, e:
            e.args = (self, self.path()) + e.args + (self.html,)
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
    __attributes__ = ('content', 'empty', 'width', 'height')
    content = None
    empty = '&lt;No file&gt;'
    width = 100
    height = 100

    def getContent(self, path):
        return self.content
    
    def output(self, outputOptions):
        content = self.getContent(self.path())
        res = {Webwidgets.Constants.OUTPUT: content.file.read(),
               'Content-type': content.type
               }
        content.file.seek(0)
        return res

    def draw(self, outputOptions):
        content = self.getContent(self.path())

        if content is None:
            return self.empty

        location = self.calculateUrl({'widget': Webwidgets.Utils.pathToId(self.path())})
        if content.type in ('image/png', 'image/jpeg', 'image/gif'):
            preview = """<img src="%(location)s" alt="%(name)s" width="%(width)s" height="%(height)s" />""" % {
                'location': location,
                'name': content.filename,
                'width': self.width,
                'height': self.height
                }
        else:
            preview = content.filename
        return """<a %(attr_htmlAttributes)s href="%(location)s">%(preview)s</a>""" % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path()),
            'location': location,
            'preview': preview
            }

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
        targetPath = target.path()
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
    __no_classes_name__ = True
    __wwml_html_override__ = False
    __children__ = Label.__children__ + ('field',)
    
    def draw(self, outputOptions):
        if isinstance(self.target, Base.Widget):
            target = self.target
        else:
            target = self + ['field'] + self.target
        targetPath = target.path()
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
                'attr_htmlAttributes': self.parent.drawHtmlAttributes(self.parent.path()),
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
        TableModel.Table.__init__(self)
        Base.StaticComposite.__init__(self, session, winId, **attrs)
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
        result = '<table border="1" %s>\n' % self.drawHtmlAttributes(self.path())
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
