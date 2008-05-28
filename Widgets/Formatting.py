#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

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
import Base, GridLayoutModel

class List(Base.StaticComposite):
    """Concatenates all children in name order, drawing the "sep"
    string inbetween each and the "pre" and "post" strings before and
    after the whole list, respectively."""
    ww_class_data__no_classes_name = True
    pre = sep = post = ''
    frame = '%(child)s'
    
    def draw(self, output_options):
        children = self.draw_children(output_options)
        attributes = self.draw_attributes(output_options)

        pre = attributes['pre'] % attributes
        sep = attributes['sep'] % attributes
        post = attributes['post'] % attributes

        return pre + sep.join([attributes['frame'] % Webwidgets.Utils.subclass_dict(attributes, {'child': child})
                               for name, child in children.iteritems()]) + post

class ReplacedList(List):
    def draw(self, output_options):
        Base.HtmlWindow.register_replaced_content(
            self,
            List.draw(self, output_options))
        return ''

class BulletList(List):
    pre = "<ul %(html_attributes)s>"
    sep = "\n"
    frame= "<li>%(child)s</li>"
    post = "</ul>"

class Html(Base.Text, Base.StaticComposite):
    """This widget is the base widget for most output widgets and the
    main method of concatenating and grouping widgets. It provides a
    way to "format" together other widgets with some custom HTML
    around them.

    @cvar html: The 'html' attribute should contain HTML code with
    python format strings like %(name)s embedded. These should
    correspond to children of the html widget or to attributes. In
    addition the special name 'id' will insert the widget id (path) of
    the current widget, which is usefull for CSS styling).
    """
    
    ww_class_data__no_classes_name = True
    """Don't include the classname of this class in L{ww_classes}."""

    top_level = None

    def draw(self, output_options):
        children = self.draw_children(
            output_options,
            invisible_as_empty = True,
            include_attributes = True)
        html = self._(self.ww_filter.html, output_options)
        if self.top_level is not None:
            html = "<%(top_level)s %(html_attributes)s>" + html + "</%(top_level)s>"
        try:
            return html % children
        except (KeyError, TypeError), e:
            e.args = (self, self.path) + e.args + (self.ww_filter.html,)
            raise e

class Div(Html):
    """Adds a single div with the widget id as id around the single
    child "child"
    """
    top_level="div"
    ww_class_data__no_classes_name = True

class Span(Html):
    """Adds a single span with the widget id as id around the single
    child "child"
    """
    top_level="span"
    ww_class_data__no_classes_name = True

class Style(Html):
    """Includes the css style from the child "style"
    """
    __wwml_html_override__ = False
    class style(Base.Text): html = ''
    html = """<style %(html_attributes)s type='text/css'>%(style)s</style>"""
    
class StyleLink(Html):
    """Includes the css style from the URL specified with the
    attribute "style"
    """
    __wwml_html_override__ = False
    style = ''
    """URI to the stylesheet to include."""
    title = ''
    html = """<link %(html_attributes)s href="%(style)s" title="%(title)s" rel="stylesheet" type="text/css" />"""

class Message(Html):
    """Informative message display. If no message is set, this widget
    is invisible."""
    __wwml_html_override__ = False
    class message(Base.Text): html = ''
    def draw(self, output_options):
        if self.children['message']:
            self.html = '<div %(html_attributes)s>%(message)s</div>'
        else:
            self.html = ''
        return Html.draw(self, output_options)

class Media(Base.Widget):
    """Media (file) viewing widget"""
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
                        'invisible':False,
                        'include_label':False},
             'image/png':{'inline':True},
             'image/jpeg':{'inline':True},
             'image/gif':{'inline':True},
             'text/css':{'inline':True, 'merge':False, 'invisible':False},
             'text/html':{'inline':True, 'merge':False, 'invisible':False}}

    def get_option(self, option):
        mime_type = getattr(self.content, 'type', 'default')
        if mime_type in self.types and option in self.types[mime_type]:
            return self.types[mime_type][option]
        return self.types['default'][option]

    def get_html_option(self, option, html_name = None):
        value = self.get_option(option)
        if value is None:
            return ''
        if html_name is None: html_name = option
        return '%s = "%s"' % (html_name, value)

    def get_renderer(self, renderer):
        mime_type = getattr(self.content, 'type', None)
        res_name = renderer + '_default'
        if mime_type is not None:
            name = renderer + "_" + mime_type.replace("/", "__").replace("-", "_")
            if hasattr(self, name):
                res_name = name
        return getattr(self, res_name)

    def calculate_output_url(self, output_options, part = 'content'):
        return self.calculate_url({'transaction': output_options['transaction'],
                                   'widget': Webwidgets.Utils.path_to_id(self.path),
                                   'part':part})

    def output(self, output_options):
        content = ''
        mime_type = 'text/plain'
        if output_options['part'] == 'content':
            if self.content is not None:
                self.content.file.seek(0)
                content = self.content.file.read()
                mime_type = self.content.type
        elif output_options['part'] == 'base':
            if self.base is not None:
                self.base.file.seek(0)
                content = (self.base.file.read().decode('utf-8') % self.get_renderer('base_include')(output_options)
                           ).encode('utf-8')
                mime_type = self.base.type
        return {Webwidgets.Constants.OUTPUT: content,
                'Content-type': mime_type}

    def draw(self, output_options):
        if self.get_option('inline'):
            inline_renderer = self.get_renderer('draw_inline')
        else:
            inline_renderer = self.draw_inline_default
        is_default = inline_renderer is self.draw_inline_default
        inline = inline_renderer(output_options)


        if self.get_option('invisible'):
            return ''

        if self.content is None:
            return self.get_option('empty')

        title = ''
        if not is_default and self.get_option('include_label'):
            title = self.draw_inline_default(output_options)

        return """<a %(html_attributes)s href="%(location)s">%(inline)s</a>""" % {
            'html_attributes': self.draw_html_attributes(self.path),
            'location': cgi.escape(self.calculate_output_url(output_options)),
            'inline': inline,
            'title': title
            }

    def draw_inline_default(self, output_options):
        return getattr(self.content, 'filename', self.get_option('empty'))

    def base_include_default(self, output_options):
        return {'content': cgi.escape(self.calculate_output_url(output_options))}


    def draw_inline_image(self, output_options):
        return """<img src="%(location)s" alt="%(name)s" %(width)s %(height)s />""" % {
            'location': cgi.escape(self.calculate_output_url(output_options)),
            'name': self.draw_inline_default(output_options),
            'width': self.get_html_option('width'),
            'height': self.get_html_option('height')
            }
    
    draw_inline_image__png = draw_inline_image
    draw_inline_image__jpeg = draw_inline_image
    draw_inline_image__gif = draw_inline_image
    
    def draw_inline_text__css(self, output_options):
        if self.get_option('merge'):
            self.register_style_link(self.calculate_output_url(output_options))
            return self.draw_inline_default(output_options)
        else:
            return """<iframe src="%(location)s" title="%(name)s" %(width)s %(height)s></iframe>""" % {
            'location': cgi.escape(self.calculate_output_url(output_options, 'base')),
            'name': self.draw_inline_default(output_options),
            'width': self.get_html_option('width'),
            'height': self.get_html_option('height')
            }
    def base_include_text__css(self, output_options):
        return {'content':"<link href='%s' rel='stylesheet' type='text/css' />" % (cgi.escape(self.calculate_output_url(output_options)),)}

    def draw_inline_application__x_javascript(self, output_options):
        if self.get_option('merge'):
            self.register_script_link(self.calculate_output_url(output_options))
            return self.draw_inline_default(output_options)
        else:
            return """<iframe src="%(location)s" title="%(name)s" %(width)s %(height)s></iframe>""" % {
            'location': cgi.escape(self.calculate_output_url(output_options, 'base')),
            'name': self.draw_inline_default(output_options),
            'width': self.get_html_option('width'),
            'height': self.get_html_option('height')}
        
    def base_include_application__x_javascript(self, output_options):
        return {'content':"<script src='%s' type='text/javascript' ></script>" % (cgi.escape(self.calculate_output_url(output_options)),)}


    def draw_inline_text(self, output_options):
        return """<iframe src="%(location)s" title="%(name)s" %(width)s %(height)s></iframe>""" % {
            'location': cgi.escape(self.calculate_output_url(output_options)),
            'name': self.draw_inline_default(output_options),
            'width': self.get_html_option('width'),
            'height': self.get_html_option('height')
            }

    draw_inline_text__plain = draw_inline_text
    draw_inline_text__html = draw_inline_text
    draw_inline_text__xml = draw_inline_text

class DownloadLink(Media):
    types = {'default': Webwidgets.Utils.subclass_dict(Media.types['default'],
                                                      {'inline':False})}

class Label(Base.StaticComposite):
    """Renders a label for an input field. The input field can be
    specified either as the widget itself, or a
    L{Webwidgets.Utils.RelativePath} to the widget"""
    

    target = []
    """The widget this widget is a label for. This is either the
    actual widget, or a L{Webwidgets.Utils.RelativePath} referencing
    the widget.
    """

    target_prefix = []

    separator = ''

    def draw_label_parts(self, output_options):
        if isinstance(self.target, Base.Widget):
            target = self.target
        else:
            target = self + self.target_prefix + self.target
        target_path = target.path
        res = self.draw_children(output_options, include_attributes = True)
        if 'Label' in res:
            res['label'] = res['Label']
        else:
            res['label'] = target.get_title()
        if getattr(target, 'error', None) is not None:
            error_arg = (target._(target.error, output_options),)
            if res['label'] == '':
                res['label'] = """<span class="error">%s</span>""" % error_arg
            else:
                res['label'] += """ <span class="error">(%s)</span>""" % error_arg
        if res['label']:
            res['label'] += self.separator
        res['target'] = Webwidgets.Utils.path_to_id(target_path)
 	return res

    def draw(self, output_options):
        res = self.draw_label_parts(output_options)
        try:
            return """<label %(html_attributes)s for="%(target)s">%(Label)s</label>""" % res
        except KeyError, e:
            e.args = (self, self.path) + e.args
            raise e

class Field(Label):
    __wwml_html_override__ = False
    target_prefix = ['Field']
    separator = ':'
    def draw(self, output_options):
        res = self.draw_label_parts(output_options)
        try:
            return """<div %(html_attributes)s>
                       <label for="%(target)s">
                        %(label)s
                       </label>
                       <div class="field">
                        %(Field)s
                       </div>
                      </div>
                      """ % res
        except KeyError, e:
            e.args = (self, self.path) + e.args
            raise e

class AbstractFieldgroup(List):
    pre = "<div %(html_attributes)s>"
    post = "</div>\n"

class VerticalFieldgroup(AbstractFieldgroup): pass
class HorizontalFieldgroup(AbstractFieldgroup): pass

# Compatibility and convienence
class Fieldgroup(VerticalFieldgroup): pass

class GridLayout(Base.StaticComposite, GridLayoutModel.GridLayout):
    """GridLayout that works similar to a GtkTable in Gtk - child widgets
    are attatched to cells by coordinates."""

    class Cell(GridLayoutModel.GridLayout.Cell):
        def name(self):
            return 'cell_' + str(self.x) + '_' + str(self.y) + '_' + str(self.w) + '_' + str(self.h)

    def __init__(self, session, win_id, **attrs):
        Base.StaticComposite.__init__(self, session, win_id, **attrs)
        GridLayoutModel.GridLayout.__init__(self)
        for name, child in self.children.iteritems():
            if name.startswith('cell_'):
                x, y, w, h = self.child_name_to_coord(name)
                GridLayoutModel.GridLayout.insert(self, child, x, y, w, h)
                
    def child_name_to_coord(self, name):
        dummy, x, y, w, h = name.split('_')
        return (int(x), int(y), int(w), int(h))
    
    def insert(self, content, x, y, w = 1, h = 1):
        cell = GridLayoutModel.GridLayout.insert(self, content, x, y, w, h)
        self.children[cell.name()] = content
        
    def remove(self, x, y):
        cell = GridLayoutModel.GridLayout.remove(self, x, y)
        if cell: del self.children[cell.name()]
    
    def draw(self, output_options):
        children = self.draw_children(output_options)
        result = '<table border="1" %s>\n' % self.draw_html_attributes(self.path)
        for y in xrange(0, self.h):
            if y not in self.row_widths or self.row_widths[y] > 0:
                result += '<tr>\n'
                for x in xrange(0, self.w):
                    if x not in self.col_widths or self.col_widths[x] > 0:
                        left, right, top, bottom = self.is_edge(x, y)            
                        if left and top:
                            colspan, rowspan = self.visible_size(x, y)
                            cell = self.cells[y][x]
                            result += '<td colspan="%(colspan)s" rowspan="%(rowspan)s">\n' % {'colspan':colspan, 'rowspan':rowspan}
                            if cell:
                                result += children[cell.name()]
                            result += '</td>\n'
                result += '</tr>\n'
        result += '</table>\n'
        return result


class DrawError(Base.Widget):
    error = Exception("Example error")

    def draw(self, output_options):
	raise self.error
