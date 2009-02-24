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

import re, cgi, types
import Webwidgets.Constants, Webwidgets.Utils, Base, Formatting

class Window(Base.Widget):
    """Window is the main widget and should allways be the top-level
    widget of any application. It has an attribute for the HTTP
    headers and handles form submission values and URL arguments."""

    headers = {'Status': '404 Page not implemented'}
    languages = None

    root = True
    path = []

    def __init__(self, session, win_id, **attrs):
        super(Window, self).__init__(session, win_id, **attrs)
        self.fields = {}
        self.arguments = {}

    def output(self, output_options):
        result = {Webwidgets.Constants.OUTPUT: self.draw(output_options)}
        result.update(self.headers)
        return result

    def draw(self, output_options):
        self.fields = {}
        self.arguments = {}
        return ''

    def process_fields(self, fields):
        """Process fields (POST field values) and generate
        notifications for those that have changed."""

        if self.session.debug_fields:
            print "Fields:", fields
            print "Original:", dict([(name, value.field_output(Webwidgets.Utils.id_to_path(name)))
                                     for (name, value)
                                     in self.fields.iteritems()])
        if self.session.debug_field_registrations:
            print "Field registrations:"
            for (name, value) in self.fields.iteritems():
                print name, value

        sorted_fields = self.fields.items()
        sorted_fields.sort(lambda (name1, field1), (name2, field2):
                          field1.input_order(field2))

        changed_fields = []
        for fieldname, field in sorted_fields:
            path = Webwidgets.Utils.id_to_path(fieldname)

            # Check an extra time that the widget is active, just
            # for added paranoia :) The field should'nt ever be
            # there if it isn't but some sloppy widget hacker migt
            # have forgotten to not to add it...
            if field.get_active(path):
                value = fields.get(fieldname, '')
                if not isinstance(value, types.ListType):
                    value = [value]
                try:
                    old_value = field.field_output(path)
                except:
                    # If old value crashes, make sure we update
                    # the value no matter what, it might, just
                    # might, fix the problem :)
                    old_value = None
                    field.append_exception()
                if old_value != value:
                    changed_fields.append((field, path, value))

        return changed_fields

    def process_arguments(self, location, arguments):
        """Process arguments (query parameters) and location and
        generate notifications for those that have changed."""

        arguments = dict(arguments)
        extra = {}
        for argumentname in arguments.keys():
            if argumentname not in self.arguments and argumentname != '__extra__':
                extra[argumentname] = arguments[argumentname]
                del arguments[argumentname]

        if '__location__' in self.arguments:
            arguments['__location__'] = location
        else:
            extra['__location__'] = location
        if '__extra__' in self.arguments:
            arguments['__extra__'] = extra

        if self.session.debug_arguments: print "Arguments:", arguments

        sorted_arguments = self.arguments.items()
        sorted_arguments.sort(lambda (name1, argument1), (name2, argument2):
                             argument1['widget'].input_order(argument2['widget']))

        changed_arguments = []
        for argumentname, argument in sorted_arguments:
            path = argument['path']
            argument = argument['widget']
            # Check an extra time that the widget is active, just
            # for added paranoia :) The argument shouldn't ever be
            # there if it isn't but some sloppy widget hacker
            # might have forgotten to not to add it.
            if argument.get_active(path):
                value = arguments.get(argumentname, '')
                if not isinstance(value, types.ListType):
                    value = [value]
                if argument.field_output(path) != value or argument.allways_do_field_input:
                    changed_arguments.append((argument, path, value))

        return changed_arguments

    def input(self, fields, arguments, output_options):
        # Collect changed attributes in order, then run field_input
        changed = self.process_arguments(output_options['location'], arguments)
        if fields is not None:
            changed.extend(self.process_fields(fields))

        for field, path, value in changed:
            field.ignore_input_this_request = False

        for field, path, value in changed:
            try:
                if not field.ignore_input_this_request:
                    field.field_input(path, *value)
            except:
                field.append_exception()
        

class HtmlWindow(Window, Base.StaticComposite, Base.DirectoryServer):
    """HtmlWindow is the main widget for any normal application window
    displaying HTML. It has two children - head and body aswell as
    attributes for title, encoding and doctype"""

    headers = {'Status': '200 OK'}
    title = 'Page not available'
    Head = Base.Text.derive(html = '')
    Body = Base.Text.derive(html = 'Page not available')
    encoding = 'UTF-8'
    doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'

    findallvalues = re.compile(
        r"""(id=["']([^"'<>]*)["'][^<>]*value=["']([^"'<>]*)["'])|(value=["']([^"'<>]*)["'][^<>]*id=["']([^"'<>]*)["'])""",
        re.MULTILINE)

    def output(self, output_options):
        result = Window.output(self, output_options)
        result['Content-Type'] = 'text/html; charset=%(encoding)s' % {'encoding': self.encoding}
        return result

    def draw(self, output_options, body = None, title = None):
        Window.draw(self, output_options)
        self.headers = {}
        self.head_content = Webwidgets.Utils.OrderedDict()
        self.replaced_content = Webwidgets.Utils.OrderedDict()

        HtmlWindow.register_style_link(
            self,
            self.calculate_url_to_directory_server('Webwidgets.HtmlWindow',
                                                   ['Widgets.css'],
                                                   output_options))
        HtmlWindow.register_script_link(
            self,
            self.calculate_url_to_directory_server('Webwidgets.HtmlWindow',
                                                   ['prototype.js'],
                                                   output_options))
        HtmlWindow.register_script_link(
            self,
            self.calculate_url_to_directory_server('Webwidgets.HtmlWindow',
                                                   ['Widgets.js'],
                                                   output_options))
        #self.register_styles(output_options)

        result = self.draw_children(
            output_options,
            invisible_as_empty = True,
            include_attributes = True)

        result.update(self.headers)

        if body is not None:
            result['Body'] = body
        if title is None: title = self.get_title(self.path)
        result['title'] = '<title>' + title + '</title>'
        result['doctype'] = self.doctype
        result['ww_untranslated__uri'] = cgi.escape(output_options['transaction'].request()._environ['REQUEST_URI'])
        result['ww_untranslated__base'] = self.session.program.request_base(output_options['transaction'])

        for (all1, name1, value1, all2, value2, name2) in self.findallvalues.findall(result['Body']):
            HtmlWindow.register_value(self, 'field_value' + '_' + (name1 or name2), (value1 or value2))

        result['ww_untranslated__head_content'] = '\n'.join(self.head_content.values())
        result['ww_untranslated__replaced_content'] = '\n'.join(self.replaced_content.values())

        result['ww_untranslated__html_form_id'] = Webwidgets.Utils.path_to_id(self.path + ['_', 'body', 'form'])

        return ("""
%(doctype)s
<html xmlns="http://www.w3.org/1999/xhtml">
 <head>
  <base href='%(ww_untranslated__base)s' />
  %(ww_untranslated__head_content)s
  %(title)s
  %(Head)s
 </head>
 <body %(ww_untranslated__html_attributes)s>
  <form name="%(ww_untranslated__html_id)s" method='post' enctype='multipart/form-data' action='%(ww_untranslated__uri)s' id="%(ww_untranslated__html_form_id)s">
   %(ww_untranslated__replaced_content)s
   %(Body)s
  </form>
 </body>
</html>""" % result).encode(self.encoding)

    @classmethod
    def register_header(cls, widget, name, value):
        widget.session.windows[widget.win_id].headers[name] = value

    @classmethod
    def register_head_content(cls, widget, content, content_name):
        content_name = content_name or Webwidgets.Utils.path_to_id(widget.path)
        widget.session.windows[widget.win_id].head_content[content_name] = content

    @classmethod
    def register_replaced_content(cls, widget, content, content_name = None):
        content_name = content_name or Webwidgets.Utils.path_to_id(widget.path)
        widget.session.windows[widget.win_id].replaced_content[content_name] = content

    @classmethod
    def register_script_link(cls, widget, *uris):
        cls.register_head_content(
            widget,
            '\n'.join(["<script src='%s' type='text/javascript' ></script>" % (cgi.escape(uri),)
                       for uri in uris]),
            'script: ' + ' '.join(uris))

    @classmethod
    def register_style_link(cls, widget, *uris):
        cls.register_head_content(
            widget,
            '\n'.join(["<link href='%s' rel='stylesheet' type='text/css' />" % (cgi.escape(uri),)
                       for uri in uris]),
            'style: ' + ' '.join(uris))

    @classmethod
    def register_script(cls, widget, name, script):
        cls.register_head_content(
            widget,
            "<script language='javascript' type='text/javascript'>%s</script>" % (script,),
            name)

    @classmethod
    def register_style(cls, widget, name, style):
        cls.register_head_content(
            widget,
            "<style type='text/css'>%s</style>" % (style,),
            name)

    @classmethod
    def register_submit_action(cls, widget, path, event):
        info = {'id': Webwidgets.Utils.path_to_id(path),
                'event': event}
        cls.register_script(
            widget,
            'submit_action: %(id)s: %(event)s' % info,
            """
            webwidgets_add_event_handler_once_loaded(
             '%(id)s',
             '%(event)s',
             'webwidgets_submit_action',
             function () {
              webwidgets_submit_button_iefix();
              document.getElementById('root:_-body-form').submit();
             });
            """ % info)

    @classmethod
    def register_value(cls, widget, name, value):
        cls.register_head_content(
            widget,
            """<script language="javascript" type='text/javascript'>webwidgets_values['%(name)s'] = '%(value)s';</script>""" % {
                'name': name,
                'value': value},
            'value: ' + name)
