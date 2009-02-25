#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

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

import types, StringIO, cgi, sys, os, re
import Webwidgets.Utils
import Webwidgets.Constants
import Webwidgets.Widgets.Base
import Webwidgets.Widgets.ApplicationMod.WindowMod
import Webwidgets.Widgets.FormattingMod.GridLayoutModel

class List(Webwidgets.Widgets.Base.StaticComposite):
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
        Webwidgets.Widgets.ApplicationMod.WindowMod.HtmlWindow.register_replaced_content(
            self,
            List.draw(self, output_options))
        return ''

class BulletList(List):
    pre = "<ul %(html_attributes)s>"
    sep = "\n"
    frame= "<li>%(child)s</li>"
    post = "</ul>"

class Html(Webwidgets.Widgets.Base.Text, Webwidgets.Widgets.Base.StaticComposite):
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
    class style(Webwidgets.Widgets.Base.Text): html = ''
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
    class message(Webwidgets.Widgets.Base.Text): html = ''
    def draw(self, output_options):
        if self.children['message']:
            self.html = '<div %(html_attributes)s>%(message)s</div>'
        else:
            self.html = ''
        return Html.draw(self, output_options)

class Media(Webwidgets.Widgets.Base.Widget):
    """Media (file) viewing widget"""
    content = None
    "Object with file (file object), type (mimetype) and filename attributes, i.e. cgi.FieldStorage"
    _content = None
    "Cache for path based content."
    inline_only = False
    "If True, do not link to media object only render inline version. Default False."

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

    def get_content(self):
        # FIXME: This needs to be cleaned up with regards to resource usage.

        if isinstance(self.content, (str, unicode)):
            if not self._content or self._content.path != self.content:
                class Content(object):
                    path = self.content
                    file = open(os.path.join(Webwidgets.Utils.module_file_path(self.__module__), path))
                    filename = os.path.basename(self.content)
                    type = Webwidgets.Utils.FileHandling.extension_to_mime_type.get(
                        os.path.splitext(filename)[1][1:], 'application/octet-stream')

                self._content = Content()
            return self._content

        else:
            return self.content


    def get_option(self, option):
        r_content = self.get_content()
        mime_type = getattr(r_content, 'type', 'default')
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
        r_content = self.get_content()
        mime_type = getattr(r_content, 'type', None)
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
        r_content = self.get_content()
        mime_type = 'text/plain'
        if output_options['part'] == 'content':
            if r_content is not None:
                r_content.file.seek(0)
                content = r_content.file.read()
                mime_type = r_content.type
        elif output_options['part'] == 'base':
            if self.base is not None:
                self.base.file.seek(0)
                content = (self.base.file.read().decode('utf-8') % self.get_renderer('base_include')(output_options)
                           ).encode('utf-8')
                mime_type = self.base.type
        return {Webwidgets.Constants.OUTPUT: content,
                'Content-type': mime_type,
                'Cache-Control': 'public; max-age=3600'}

    def draw(self, output_options):
        if self.get_option('inline'):
            inline_renderer = self.get_renderer('draw_inline')
        else:
            inline_renderer = self.draw_inline_default
        is_default = inline_renderer is self.draw_inline_default
        inline = inline_renderer(output_options)


        if self.get_option('invisible'):
            return ''

        if self.get_content() is None:
            return self.get_option('empty')

        if self.inline_only:
            return inline

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
        r_content = self.get_content()
        return getattr(r_content, 'filename', self.get_option('empty'))

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
            Webwidgets.Widgets.ApplicationMod.WindowMod.HtmlWindow.register_style_link(self, self.calculate_output_url(output_options))
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
            Webwidgets.Widgets.ApplicationMod.WindowMod.HtmlWindow.register_script_link(self, self.calculate_output_url(output_options))
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

class ImageButton(Webwidgets.Widgets.Base.SingleActionInput, Media):
    """ImageButton, combination of SingleActionInput and Media with
    inline_only set. Used to get clickable images."""

    inline_only = True
    
    def get_renderer(self, renderer):
        return self.draw_inline_image_button

    def draw(self, output_options):
        Webwidgets.Widgets.Base.SingleActionInput.draw(self, output_options)
        return Media.draw(self, output_options)

    def draw_inline_image_button(self, output_options):
        return """<input %(html_attributes)s type="image" %(disabled)s name="%(name)s" value="1" src="%(src)s" %(width)s %(height)s />""" % {
            'src': cgi.escape(self.calculate_output_url(output_options)),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'width': self.get_html_option('width'),
            'height': self.get_html_option('height'),
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)],
            'html_attributes': self.draw_html_attributes(self.path)
            }

class DownloadLink(Media):
    types = {'default': Webwidgets.Utils.subclass_dict(Media.types['default'],
                                                      {'inline':False})}

class Label(Webwidgets.Widgets.Base.StaticComposite):
    """Renders a label for an input field. The input field can be
    specified either as the widget itself, or a
    L{Webwidgets.Utils.WidgetPath} to the widget"""
    

    target = []
    """The widget this widget is a label for. This is either the
    actual widget, or a L{Webwidgets.Utils.WidgetPath} referencing
    the widget.
    """

    target_prefix = []

    separator = ''

    def draw_label_parts(self, output_options):
        if isinstance(self.target, Webwidgets.Widgets.Base.Widget):
            target = self.target
        else:
            target = self + self.target_prefix + self.target
        target_path = target.path
        res = self.draw_children(output_options, include_attributes = True, invisible_as_empty=True)
        if 'Label' in res:
            res['label'] = res['Label']
        else:
            res['label'] = target.get_title(target.path)
        if getattr(target, 'error', None) is not None:
            error_arg = (target._(target.error, output_options),)
            if res['label'] == '':
                res['label'] = """<span class="ww-error">%s</span>""" % error_arg
            else:
                res['label'] += """ <span class="ww-error">(%s)</span>""" % error_arg
        if getattr(target, 'input_required', False):
            res['label'] += ' <span class="ww-input-required">*</span>'
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

class GridLayout(Webwidgets.Widgets.Base.StaticComposite, Webwidgets.Widgets.FormattingMod.GridLayoutModel.GridLayout):
    """GridLayout that works similar to a GtkTable in Gtk - child widgets
    are attatched to cells by coordinates."""

    class Cell(Webwidgets.Widgets.FormattingMod.GridLayoutModel.GridLayout.Cell):
        def name(self):
            return 'cell_' + str(self.x) + '_' + str(self.y) + '_' + str(self.w) + '_' + str(self.h)

    def __init__(self, session, win_id, **attrs):
        Webwidgets.Widgets.Base.StaticComposite.__init__(self, session, win_id, **attrs)
        Webwidgets.Widgets.FormattingMod.GridLayoutModel.GridLayout.__init__(self)
        for name, child in self.children.iteritems():
            if name.startswith('cell_'):
                x, y, w, h = self.child_name_to_coord(name)
                Webwidgets.Widgets.FormattingMod.GridLayoutModel.GridLayout.insert(self, child, x, y, w, h)
                
    def child_name_to_coord(self, name):
        dummy, x, y, w, h = name.split('_')
        return (int(x), int(y), int(w), int(h))
    
    def insert(self, content, x, y, w = 1, h = 1):
        cell = Webwidgets.Widgets.FormattingMod.GridLayoutModel.GridLayout.insert(self, content, x, y, w, h)
        self.children[cell.name()] = content
        
    def remove(self, x, y):
        cell = Webwidgets.Widgets.FormattingMod.GridLayoutModel.GridLayout.remove(self, x, y)
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


class DrawError(Webwidgets.Widgets.Base.Widget):
    error = Exception("Example error")

    def draw(self, output_options):
	raise self.error

class ProgressMeter(Webwidgets.Widgets.Base.Widget):
    progress_position = 0.0
    scale_start = 0.0
    scale_end = 100.0
    scale_units = "%"
    width = 100.0
    width_unit = "px"

    def draw(self, output_options):
        progress_position = (self.progress_position - self.scale_start) / (self.scale_end - self.scale_start)
        return """
%(scale_start)s%(scale_units)s
<span class="%(progress_box_class)s">
<span style="width: %(width)s%(width_unit)s" class="%(progress_label_class)s">
  %(progress)s%(scale_units)s
 </span>
 <span
  style="padding-right: %(progress_done)s%(width_unit)s;
         margin-right: %(progress_left)s%(width_unit)s"
  class="%(progress_position_class)s">&nbsp;</span>
</span>
%(scale_end)s%(scale_units)s
""" % {'width': self.width,
       'width_unit': self.width_unit,
       'scale_start': self.scale_start,
       'scale_end': self.scale_end,
       'scale_units': self.scale_units,
       'progress': self.progress_position,
       'progress_done': self.width * progress_position,
       'progress_left': self.width * (1 - progress_position),
       'progress_box_class': Webwidgets.Utils.classes_to_css_classes(self.ww_classes, ['progress_box']),
       'progress_label_class': Webwidgets.Utils.classes_to_css_classes(self.ww_classes, ['progress_label']),
       'progress_position_class': Webwidgets.Utils.classes_to_css_classes(self.ww_classes, ['progress_position'])
       }

class BrowserWarning(Webwidgets.Widgets.Base.StaticComposite):
    def draw(self, output_options):
        agent = output_options['transaction'].request()._environ['HTTP_USER_AGENT']
        for name, child in self.get_children():
            if not hasattr(child, 'match_agent_compiled'):
                child.match_agent_compiled = re.compile(child.match_agent)
            if child.match_agent_compiled.match(agent):
                return self.draw_child(child.path, child, output_options, True)
        return ''

class Timing(Webwidgets.Widgets.Base.Widget):
    part = 'total'
    """Any of

    total - total server time
    input_decode - time to decode input fields
    input_process - time to process input (e.g. notifcation handling)
    class_output - total time application specific time 
    output - time to run draw()
    """

    def draw(self, output_options):
        return '<ww:timing part="%s" />' % (self.part,)
