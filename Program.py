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

import time
import WebKit.Page
import cgi, urllib, types, os, sys, threading
import Utils, Utils.Cache, Widgets, AccessManager, Constants
import hotshot, pdb, traceback
import Utils.Performance, os, datetime

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
    profile_directory = "/tmp"
    performance_report = True
    performance_report_directory = "/tmp"
    performance_report_min_time = 1.0
    debug = False

    _transaction_store = threading.local()

    #FIXME: Use this instead of passing around lots of stuff in output_options
    @classmethod
    def transaction(cls):
        if not hasattr(cls._transaction_store, 'transaction'):
            raise AttributeError('There is no current transaction running')
        return cls._transaction_store.transaction

    request_nr = 0

#     def sleep(self, transaction):
#         import traceback
#         print "============SLEEP============"
#         traceback.print_stack()
#         super(Program, self).sleep(transaction)

    def _respond(self, transaction):
        """Main processing method, called by WebWare."""
        Program._transaction_store.transaction = transaction
        return self.handle_request(transaction)

    def handle_request(self, transaction):
        type(self).request_nr += 1
        try:
            request = transaction.request()
            request.timings = Utils.Timings()
            request.timings['total'].start()
            
            session = transaction.session()
            servlet = request.servletURI()
            if not session.hasValue(servlet):
                session[servlet] = self.Session(type(self))
            session[servlet].program = self
            fn = lambda: session[servlet].handle_request(transaction)

            if self.profile:
                non_profiled_fn = fn
                def profile_fn():
                    profiler = hotshot.Profile(os.path.join(self.profile_directory, "webwidgets.profile.request.%s" % type(self).request_nr))
                    profiler.addinfo('url', self.request_base(transaction) + request.extraURLPath() + '?' + request.queryString())
                    try:
                        return profiler.runcall(non_profiled_fn)
                    finally:
                        profiler.close()
                fn = profile_fn

            if self.performance_report:
                non_reporting_fn = fn
                def reporting_fn():
                    Utils.Performance.start_report()
                    t1 = time.time()
                    try:
                        return non_reporting_fn()
                    finally:
                        report = Utils.Performance.get_report()
                        t2 = time.time()
                        dt = t2-t1
                        if report and dt > self.performance_report_min_time:
                            filename=os.path.join(self.performance_report_directory, "greencycle.performance.%s.%s.html" % (datetime.datetime.now().strftime("%Y-%m-%d"),
                                                                                                                 type(self).request_nr))
                            linkname=os.path.join(self.performance_report_directory, "greencycle.performance.html")
                            
                            try:
                                os.remove(filename)
                            except:
                                pass
                            with open(filename,'w') as f:
                                f.write(report)
                            try:
                                os.remove(linkname)
                            except:
                                pass

                            os.symlink(filename, linkname)
                fn = reporting_fn

            if self.debug:
                non_debugged_fn = fn
                def debug_fn():
                    return pdb.runcall(non_debugged_fn)
                fn = debug_fn

            return fn()
        
        finally:
            Utils.Cache.clear_cache(time="request_part")
            Utils.Cache.clear_cache(time="request")

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


        def replace_timings(self, req, output, output_item):
            if output.get('Content-Type', '').startswith('text/'):
                for key, value in req.timings.iteritems():
                    replace_string = '<ww:timing part="%s" />' % (key,)
                    if replace_string in output_item:
                        value = float(value.total.seconds) + (0.000001 * float(value.total.microseconds))
                        output_item = output_item.replace(replace_string, '%.1f' % (value,))
            return output_item
            
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

            with req.timings['input_decode']:
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

            with req.timings['class_output']:
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

            req.timings['total'].stop()
            if isinstance(content, types.UnicodeType):
                content = content.encode('utf-8')
            if isinstance(content, types.StringType):
                response.write(self.replace_timings(req, output, content))
            elif content is not None:
                for item in content:
                    response.write(self.replace_timings(req, output, item))

        def class_output(cls, session, arguments, output_options):
            req = output_options['transaction'].request()
            response = output_options['transaction'].response()

            window = session.get_window(output_options['win_id'], output_options)
            if window:
                with req.timings['input_process']:
                    fields = None
                    if req.method() == 'POST':
                        fields = decode_fields(normalize_fields(req.fields()))
                    
                    window.input(fields, arguments, output_options)

                    def find_fn(obj, fn_name, output_options):
                        if 'widget' in output_options:
                            for name in Utils.id_to_path(output_options['widget']):
                                obj = obj[name]
                        if 'aspect' in output_options:
                            fn_name += '_' + output_options['aspect']
                        return getattr(obj, fn_name, None)

                    args = (output_options,)
                    output_fn = find_fn(window, 'output', output_options)

                Utils.Cache.clear_cache(time="request_part")
            
                with req.timings['output']:
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
