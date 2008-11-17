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

"""This module is used to define a new Webwidgets application

This module contains the foundations for implementing a Webwidgets
application.
"""

from __future__ import with_statement

import WebKit.Page
import cgi, urllib, types, os, sys
import Utils, Utils.Cache, Widgets, AccessManager, Constants
import hotshot, pdb, traceback
import Webwidgets.Utils.Performance

debug_exceptions = True

def decode_field(value):
    if isinstance(value, types.StringType):
        return value.decode('utf-8')
    return value

def normalize_fields(fields):
    fields = dict(fields)
    for fieldname in fields.keys():
        if isinstance(fields[fieldname], list):
            fields[fieldname] = [field for field in fields[fieldname]
                                 if field != '']
            if len(fields[fieldname]) == 1:
                fields[fieldname] = fields[fieldname][0]
            elif len(fields[fieldname]) == 0:
                del fields[fieldname]
        elif fields[fieldname] == '':
            del fields[fieldname]
    return fields

def decode_fields(fields):
    fields = dict(fields)
    for fieldname in fields.keys():
        if isinstance(fields[fieldname], list):
            fields[fieldname] = [decode_field(item)
                                 for item in fields[fieldname]]
        else:
            fields[fieldname] = decode_field(fields[fieldname])
    return fields

def filter_arguments(arguments):
    res_args = dict([(key, value)
                    for (key, value)
                    in arguments.iteritems()
                    if not key.startswith('_')])
    output_options = dict([(key[1:], value)
                          for (key, value)
                          in arguments.iteritems()
                          if key.startswith('_')])
    return res_args, output_options

class Program(WebKit.Page.Page):
    """This class is the foundation of a Webwidgets application. An
    application consists of a Program instance, and any number of
    Session instances, which in turn consists of any number of Window
    instances (one for each page).

    The application programmer should subclass this class,
    subclass/override L{Webwidgets.Program.Program.Session} and
    implement the L{Webwidgets.Program.Program.Session.new_window}
    method.
    """

    profile = False
    debug = False

    request_nr = 0

#     def sleep(self, transaction):
#         import traceback
#         print "============SLEEP============"
#         traceback.print_stack()
#         super(Program, self).sleep(transaction)

    def _respond(self, transaction):
        """Main processing method, called by WebWare."""

        try:
            if self.profile:
                Webwidgets.Utils.Performance.start_report()
            return self.handle_request(transaction)
        except:
            sys.last_traceback = sys.exc_info()[2]
            pdb.pm()
            raise
        finally:
            if self.profile:
                report = Webwidgets.Utils.Performance.get_report()
                if report:
                    with open("/tmp/greencycle-performance.html",'w') as f:
                        f.write(report)

    def handle_request(self, transaction):
        type(self).request_nr += 1
        try:
            session = transaction.session()
            request = transaction.request()
            servlet = request.servletURI()
            if not session.hasValue(servlet):
                session[servlet] = self.Session(type(self))
            session[servlet].program = self
            fn = lambda: session[servlet].handle_request(transaction)

            if self.profile:
                non_profiled_fn = fn
                def profile_fn():
                    profiler = hotshot.Profile("webwidgets.profile.request.%s" % type(self).request_nr)
                    profiler.addinfo('url', self.request_base(transaction) + request.extraURLPath() + '?' + request.queryString())
                    try:
                        return profiler.runcall(non_profiled_fn)
                    finally:
                        profiler.close()
                fn = profile_fn

            if self.debug:
                non_debugged_fn = fn
                def debug_fn():
                    return pdb.runcall(non_debugged_fn)
                fn = debug_fn

            return fn()
        
        finally:
            Utils.Cache.clear_per_request_cache()

    def webware_base(self, transaction):
        """@return: A URL to where the Webware installation is serving
        documents from."""

        req = transaction.request()

        # FIXME: Work-around empty adapter name
        adapter = req.adapterName()

        port = ''
        if req._environ.get('HTTPS', 'off') == 'on':
            protocol = "https"
            if req._environ['SERVER_PORT'] != '443':
                port = ':' + req._environ['SERVER_PORT']
        else:
            protocol = "http"
            if req._environ['SERVER_PORT'] != '80':
                port = ':' + req._environ['SERVER_PORT']

        # This is due to difference between running with apache+mod_webkit and only webware appserver
        if 'HTTP_HOST' in req._environ:
            host = req._environ['HTTP_HOST']
        else:
            import socket
            host = socket.getfqdn()
        
        if ':' in host:
            port = ''

        return protocol + '://' + host + port + adapter

    def request_base(self, transaction):
        """@return: A URL to this Webwidgets application."""
        return self.webware_base(transaction) + transaction.request().servletURI()

    class Session(object):
        """The application programmer should subclass this class and
        implement the L{Webwidgets.Program.Program.Session.new_window}
        method.
        """

        debug_arguments = False
        debug_fields = False
        debug_field_input = False
        debug_receive_notification = False
        debug_field_registrations = False

        root = True
        parent = None
        name = None

        def __init__(self, Program):
            self.windows = Widgets.Base.ChildNodeDict(self)
            self.notifications = []
            self.output = None
            self.Program = Program
            self.program = None
            self.AccessManager = self.AccessManager(self)
            self.session = self
            self.languages = None

        AccessManager = AccessManager.AccessManager

        class Notification(object):
            def __init__(self, widget, message, args = (), kw = {}, path = None):
                self.widget = widget
                self._path = path
                self.message = message
                self.args = args
                self.kw = kw

            class Path(object):
                def __get__(self, instance, owner):
                    if instance is None: return None
                    path = instance._path
                    if isinstance(path, list):
                        return path
                    widget_path = instance.widget.path
                    if path is None:
                        return widget_path
                    if widget_path is None:
                        return None
                    return list(widget_path + path)

                def __set__(self, instance, value):
                    instance._path = value
            path = Path()

            def parent(self):
                if self.widget.parent is None:
                    raise StopIteration()
                return type(self)(self.widget.parent, self.message, self.args, self.kw, self.path)

            def process(self):
                if hasattr(self.widget, self.message):
                    if self.widget.session.debug_receive_notification:
                        print "Notifying %s (received)" % self
                        print "Method: %s" % (getattr(self.widget, self.message),)
                    try:
                        getattr(self.widget, self.message
                                )(self.path, *self.args, **self.kw)
                    except StopIteration:
                        return
                    except:
                        self.widget.append_exception()
                else:
                    if self.widget.session.debug_receive_notification:
                        print "Notifying %s (ignored)" % self
                if self.widget.session.debug_receive_notification:
                    print "Notifying parent %s" % self.widget.parent
                try:
                    parent = self.parent()
                except StopIteration:
                    return
                return parent.process()

            def __repr__(self):
                return "Notification(%s)" % (unicode(self),)

            def __unicode__(self):
                return "%s/%s <- %s(%s, %s)" % (
                    self.widget, self.path, self.message, self.args, self.kw)

            def __str__(self):
                return str(unicode(self))

        def get_window(self, win_id, output_options):
            """Retrieves a window by its ID; either an existing window
            is returned, or a window created for the requested id."""
            if win_id in self.windows:
                return self.windows[win_id]
            else:
                window = self.new_window(win_id)
                if window is not None:
                    self.windows[win_id] = window
                    # Redraw the window once, so that all input fields
                    # have generated their window.fields and
                    # window.arguments entries so that we can do
                    # proper input handling directly and don't
                    # have to wait for the next reload. This is
                    # especially important for arguments as they can
                    # be bookmarked.
                    #### fixme ####
                    # name = """Transaction should probably be
                    # some kind of dummy object, not out current
                    # real one..."""
                    #### end ####
                    try:
                        window.draw({'transaction': output_options['transaction']})
                    except Constants.OutputGiven:
                        return None
                return window

        def process_arguments(self, window, location, arguments):
            """Process arguments (query parameters) and location and
            generate notifications for those that have changed."""

            arguments = dict(arguments)
            extra = {}
            for argumentname in arguments.keys():
                if argumentname not in window.arguments and argumentname != '__extra__':
                    extra[argumentname] = arguments[argumentname]
                    del arguments[argumentname]

            if '__location__' in window.arguments:
                arguments['__location__'] = location
            else:
                extra['__location__'] = location
            if '__extra__' in window.arguments:
                arguments['__extra__'] = extra

            if self.debug_arguments: print "Arguments:", arguments

            sorted_arguments = window.arguments.items()
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
                    if argument.field_output(path) != value:
                        changed_arguments.append((field, path, value))

            return changed_arguments

        def generate_arguments(self, window):
            """Return a tuple of the location and arguments (query
            parameters) that the user should be at given the state of
            the widgets (this is used to trigger a redirect, would
            they not match the current URL)."""

            new_location = []
            new_arguments = {}
            for argumentname, argument in window.arguments.iteritems():
                value = argument['widget'].field_output(argument['path'])
                if argumentname == '__extra__':
                    new_arguments.update(value)
                elif argumentname == '__location__':
                    new_location = value
                else:
                    new_arguments[argumentname] = value
            return new_location, new_arguments

        def process_fields(self, window, fields):
            """Process fields (POST field values) and generate
            notifications for those that have changed."""

            if self.debug_fields:
                print "Fields:", fields
                print "Original:", dict([(name, value.field_output(Utils.id_to_path(name)))
                                         for (name, value)
                                         in window.fields.iteritems()])
            if self.debug_field_registrations:
                print "Field registrations:"
                for (name, value) in window.fields.iteritems():
                    print name, value

            sorted_fields = window.fields.items()
            sorted_fields.sort(lambda (name1, field1), (name2, field2):
                              field1.input_order(field2))

            changed_fields = []
            for fieldname, field in sorted_fields:
                path = Utils.id_to_path(fieldname)

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

        def handle_request(self, transaction):
            """Main processing method, called by WebWare. This method will
            notify widgets of changed input values, process any pending
            notifications and then redraw all widgets (unless output has
            already been set by a notification, e.g. with
            L{redirect}, in which case that output is sent to the
            client instaed)."""
            req = transaction.request()
            response = transaction.response()

            self.output = None

            # extraURLPath begins with a /, so remove the first empty item in location
            location = req.extraURLPath().split('/')[1:]

            base_options = {'widget_class': Constants.DEFAULT_WIDGET_CLASS,
                           'win_id': Constants.DEFAULT_WINDOW,
                           'widget': Constants.DEFAULT_WIDGET}
            if location and location[0].startswith('_'):
                base_options['widget_class'] = location[0][1:]
                location = location[1:]
            if location and location[0].startswith('_'):
                base_options['win_id'] = location[0][1:]
                location = location[1:]
            if location and location[0].startswith('_'):
                base_options['widget'] = location[0][1:]
                location = location[1:]
            base_options['location'] = location
            base_options['transaction'] = transaction

            arguments = decode_fields(normalize_fields(cgi.parse_qs(req.queryString())))
            arguments, output_options = filter_arguments(arguments)
            output_options.update(base_options)

            obj = Utils.load_class(output_options['widget_class'])
            if not (isinstance(obj, type)
                    and (   issubclass(obj, Program.Session)
                         or issubclass(obj, Widgets.Base.Widget))):
                raise Exception("Expected session or widget. Got", obj)
            fn_name = 'class_output'
            if 'aspect' in output_options:
                fn_name += '_' + output_options['aspect']
            output_fn = getattr(obj, fn_name)

            try:
                output = output_fn(self, arguments, output_options)
            except Constants.OutputGiven, e:
                output = e.output

            if output is None:
                output = {'Status': '404 No such window',
                          'Content-Type': 'text/plain',
                          Constants.OUTPUT: '404 No such window'}

            if 'Status' not in output:
                output['Status'] = '200 OK'

            for key, value in output.iteritems():
                if key not in (Constants.OUTPUT, Constants.FINAL_OUTPUT):
                    response.setHeader(key.encode('utf-8'), value.encode('utf-8'))
            content = None
            if Constants.OUTPUT in output:
                content = output[Constants.OUTPUT]
            if Constants.FINAL_OUTPUT in output:
                content = output[Constants.FINAL_OUTPUT]
            if isinstance(content, types.StringType):
                response.write(content)
            elif content is not None:
                for item in content:
                    response.write(item)

        def class_output(cls, session, arguments, output_options):
            req = output_options['transaction'].request()
            response = output_options['transaction'].response()

            window = session.get_window(output_options['win_id'], output_options)
            if window:
                # Collect changed attributes in order, then run field_input
                changed = session.process_arguments(window, output_options['location'], arguments)
                if req.method() == 'POST':
                    changed.extend(session.process_fields(window,
                                                          decode_fields(normalize_fields(req.fields()))))

                for field, path, value in changed:
                    try:
                        if not field.ignore_input_this_request:
                            field.field_input(path, *value)
                    except:
                        field.append_exception()

                for field in window.fields.itervalues():
                    field.ignore_input_this_request = False

                obj = window
                fn_name = 'output'
                args = (output_options,)
                if 'widget' in output_options:
                    for name in Utils.id_to_path(output_options['widget']):
                        obj = obj[name]
                if 'aspect' in output_options:
                    fn_name += '_' + output_options['aspect']
                output_fn = getattr(obj, fn_name)

                if not changed and output_fn is window.output:
                    #### fixme ####
                    # name = """changed will nearly allways be true due
                    # to buttons"""
                    # description = """If you clicked a button and
                    # then you do a reload, you'd have the same POST
                    # (non-empty-string) variable, but your
                    # field_output would still output an empty
                    # string."""
                    #### end ####

                    # Don't fire reload events except for reloads of
                    # the page itself. Caching policies might result
                    # in other items being reloaded now and then w/o
                    # user interaction...
                    window.notify("reload")


                res = output_fn(*args)
                if (not res
                    or (    'Location' not in res
                        and Constants.FINAL_OUTPUT not in res)):
                    (new_location, new_arguments) = session.generate_arguments(window)
                    new_arguments = normalize_fields(new_arguments)
                    if (   new_location != output_options['location']
                        or new_arguments != arguments):
                        if session.debug_arguments:
                            print "Old: %s: %s" % (output_options['location'], arguments)
                            print "New: %s: %s" % (new_location, new_arguments)
                        session.redirect(
                            Utils.subclass_dict(output_options,
                                               {'location': new_location}),

                            new_arguments)
                return res
        class_output = classmethod(class_output)

        def notify(self, *arg, **kw):
            """Enques a message (method name and arguments) for a
            widget. Notifications can be sent to any widget and
            escalates throughout the widget hierarchy up to the root,
            or until a widget decides to 'eat' it.

            Notifications are processed in first-come-first-serve
            order, so that notifications registered as a result of
            previous notifications are handled after all those
            previous ones are processed. In practice, this means that
            all direct value-changing notifications have been
            processed before any secondary notifications sent out by
            widgets as a result of their values being changed, gets
            processed.
            """
            self.Notification(*arg, **kw).process()

        def calculate_url(self, output_options, arguments):
            path = [self.program.request_base(output_options['transaction'])]

            if (   (    'widget_class' in output_options
                    and output_options['widget_class'] != Constants.DEFAULT_WIDGET_CLASS)
                or (    'win_id' in output_options
                    and output_options['win_id'] != Constants.DEFAULT_WINDOW)
                or (    'widget' in output_options
                    and output_options['widget'] != Constants.DEFAULT_WIDGET)):
                path.append('_' + output_options.get('widget_class', Constants.DEFAULT_WIDGET_CLASS))
                if (   (    'win_id' in output_options
                        and output_options['win_id'] != Constants.DEFAULT_WINDOW)
                    or (    'widget' in output_options
                        and output_options['widget'] != Constants.DEFAULT_WIDGET)):
                    path.append('_' + output_options.get('win_id', Constants.DEFAULT_WINDOW))
                    if (    'widget' in output_options
                        and output_options['widget'] != Constants.DEFAULT_WIDGET):
                        path.append('_' + output_options['widget'])

            if 'location' in output_options and output_options['location']:
                path.extend(output_options['location'])

            url_arg_list = []
            for key, value in arguments.iteritems():
                if not isinstance(value, list): value = [value]
                for value_part in value:
                    url_arg_list.append((key, value_part))
            for key, value in output_options.iteritems():
                if key not in ('transaction', 'widget_class', 'win_id', 'widget', 'location', 'internal'):
                    if not isinstance(value, list): value = [value]
                    for value_part in value:
                        url_arg_list.append(('_' + key, value_part))

            args = ''
            if url_arg_list:
                args = '?' + urllib.urlencode(url_arg_list)

            return '/'.join(path) + args

        def redirect(self, output_options, arguments):
            raise Constants.OutputGiven({'Status': '303 See Other',
                                         'Location': self.calculate_url(output_options,
                                                                        arguments)})

        def new_window(self, win_id):
            """You should override this to return a Window instance in
            your own application."""
            raise Constants.OutputGiven()
