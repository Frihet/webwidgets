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

"""This module is used to define a new Webwidgets application

This module contains the foundations for implementing a Webwidgets
application.
"""

import WebKit.Page
import cgi, urllib, types
import Utils, Widgets, AccessManager, Constants

def decodeField(value):
    if isinstance(value, types.StringType):
        return value.decode('utf-8')
    return value

def normalizeFields(fields):
    fields = dict(fields)
    for fieldname in fields.keys():
        if isinstance(fields[fieldname], list):
            if len(fields[fieldname]) == 1:
                fields[fieldname] = fields[fieldname][0]
        if fields[fieldname] == '':
            del fields[fieldname]
    return fields

def decodeFields(fields):
    fields = dict(fields)
    for fieldname in fields.keys():
        if isinstance(fields[fieldname], list):            
            fields[fieldname] = [decodeField(item)
                                 for item in fields[fieldname]]
        else:
            fields[fieldname] = decodeField(fields[fieldname])
    return fields

def filterArguments(arguments):
    resArgs = dict([(key, value)
                    for (key, value)
                    in arguments.iteritems()
                    if not key.startswith('_')])
    outputOptions = dict([(key[1:], value)
                          for (key, value)
                          in arguments.iteritems()
                          if key.startswith('_')])
    return resArgs, outputOptions

class Program(WebKit.Page.Page):
    """This class is the foundation of a Webwidgets application. An
    application consists of a Program instance, and any number of
    Session instances, which in turn consists of any number of Window
    instances (one for each page).

    The application programmer should subclass this class,
    subclass/override L{Webwidgets.Program.Program.Session} and
    implement the L{Webwidgets.Program.Program.Session.newWindow}
    method.
    """

    def writeHTML(self):
        """Main processing method, called by WebWare."""
        session = self.session()
        servlet = self.request().servletURI()
        if not session.hasValue(servlet):
            session[servlet] = self.Session()
        session[servlet].program = self
        return session[servlet].writeHTML()

    def webwareBase(self):
        """@return: A URL to where the Webware installation is serving
        documents from."""
        #### fixme ####
        # name = "https not supported"
        # description = """Yes, we should check for https, but WebWare
        # is braindead and doesn't provide that info _at_all_!"""
        #### end ####
        req = self.request()
        return 'http://' + req._environ['SERVER_NAME'] + req.adapterName() + '/'

    def requestBase(self):
        """@return: A URL to this Webwidgets application."""
        req = self.request()
        return self.webwareBase() + req.servletURI() + '/'

    class Session(object):
        """The application programmer should subclass this class and
        implement the L{Webwidgets.Program.Program.Session.newWindow}
        method.
        """
        
        debugArguments = False
        debugFields = False
        debugSendNotification = False
        debugReceiveNotification = False

        def __init__(self):
            self.windows = Widgets.Base.ChildNodes(self)
            self.notifications = []
            self.output = None
            self.program = None
            self.AccessManager = self.AccessManager(self)
            self.session = self

        AccessManager = AccessManager.AccessManager

        class Notification(object):
            def __init__(self, widget, message, args = (), kw = {}, path = None):
                self.widget = widget
                self._path = path
                self.message = message
                self.args = args
                self.kw = kw

            class path(object):
                def __get__(self, instance, owner):
                    path = instance._path
                    if path is None:
                        path = instance.widget.path()
                    elif isinstance(path, Utils.RelativePath):
                        path = list(instance.widget.path() + path)
                    return path
                def __set__(self, instance, value):
                    instance._path = value
            path = path()

            def parent(self):
                return type(self)(self.widget.parent, self.message, self.args, self.kw, self.path)

            def process(self):
                if self.widget.session.debugReceiveNotification:
                    print "Notifying %s" % self
                if hasattr(self.widget, self.message):
                    # Run the notification handler!
                    if getattr(self.widget, self.message
                               )(self.path, *self.args, **self.kw):
                        # Notification consumed
                        return
                if hasattr(self.widget, 'parent'):
                    self.widget.session.addNotification(self.parent())

            def __str__(self):
                return "%s/%s <- %s(%s, %s)" % (
                    self.widget, self.path, self.message, self.args, self.kw)

        def getWindow(self, winId):
            """Retrieves a window by its ID; either an existing window
            is returned, or a window created for the requested id."""
            if winId in self.windows:
                return self.windows[winId]
            else:
                try:
                    window = self.newWindow(winId)
                    if window is not None:
                        self.windows[winId] = window
                        # Redraw the window once, so that all input fields
                        # have generated their window.fields and
                        # window.arguments entries so that we can do
                        # proper input handling directly and don't
                        # have to wait for the next reload. This is
                        # especially important for arguments as they can
                        # be bookmarked.
                        window.draw([])
                    return window
                except Constants.OutputGiven:
                    return None

        def processArguments(self, window, location, arguments):
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

            if self.debugArguments: print "Arguments:", arguments
            for argumentname, argument in arguments.iteritems():
                oldArgument = window.arguments[argumentname]
                # Check an extra time that the widget is
                # active, just for added paranoia :) The field
                # should'nt ever be there if it isn't but some
                # sloppy widget hacker migt have forgotten to
                # not to add it...
                if oldArgument['widget'].getActive(oldArgument['path']):
                    if not isinstance(argument, types.ListType):
                        argument = [argument]
                    if oldArgument['widget'].fieldOutput(oldArgument['path']) != argument:
                        oldArgument['widget'].fieldInput(oldArgument['path'], *argument)

        def generateArguments(self, window):
            """Return a tuple of the location and arguments (query
            parameters) that the user should be at given the state of
            the widgets (this is used to trigger a redirect, would
            they not match the current URL)."""

            newLocation = []
            newArguments = {}
            for argumentname, argument in window.arguments.iteritems():
                value = argument['widget'].fieldOutput(argument['path'])
                if argumentname == '__extra__':
                    newArguments.update(value)
                elif argumentname == '__location__':
                    newLocation = value
                else:
                    newArguments[argumentname] = value
            return newLocation, newArguments

        def processFields(self, window, fields):
            """Process fields (POST field values) and generate
            notifications for those that have changed."""
            
            if self.debugFields:
                print "Fields:", fields
                print "Original:", dict([(name, value.fieldOutput(Utils.idToPath(name)))
                                         for (name, value)
                                         in window.fields.iteritems()])
            
            for fieldname, field in window.fields.iteritems():
                path = Utils.idToPath(fieldname)
                # Check an extra time that the widget is
                # active, just for added paranoia :) The field
                # should'nt ever be there if it isn't but some
                # sloppy widget hacker migt have forgotten to
                # not to add it...
                if field.getActive(path):
                    value = fields.get(fieldname, '')
                    if not isinstance(value, types.ListType):
                        value = [value]
                    if field.fieldOutput(path) != value:
                        field.fieldInput(path, *value)

        def writeHTML(self):
            """Main processing method, called by WebWare. This method will
            notify widgets of changed input values, process any pending
            notifications and then redraw all widgets (unless output has
            already been set by a notification, e.g. with
            L{redirect}, in which case that output is sent to the
            client instaed)."""
            req = self.program.request()
            response = self.program.response()

            self.output = None

            # extraURLPath begins with a /, so remove the first empty item in location
            location = req.extraURLPath().split('/')[1:]            
            winId = Constants.DEFAULT_WINDOW
            if location and location[0].startswith('_'):
                winId = location[0][1:]
                location = location[1:]

            window = self.getWindow(winId)
            if window:
                arguments = decodeFields(normalizeFields(cgi.parse_qs(req.queryString())))
                arguments, outputOptions = filterArguments(arguments)
                self.processArguments(window, location, arguments)
                if req.method() == 'POST':
                    self.processFields(window,
                                       decodeFields(normalizeFields(req.fields())))

                self.processNotifications()

                if self.output is None:
                    if 'widgetClass' in outputOptions:
                        cls = Utils.loadClass(outputOptions['widgetClass'])
                        assert issubclass(cls, Widgets.Base.Widget)
                        outputFn = lambda: cls.classOutput(window, outputOptions)
                    elif 'widget' in outputOptions:
                        widget = window
                        for name in Utils.idToPath(outputOptions['widget']):
                            widget = widget[name]
                        outputFn = lambda: widget.output(outputOptions)
                    else:
                        outputFn = lambda: window.output(outputOptions)
                        
                    try:
                        self.output = outputFn()
                    except Constants.OutputGiven:
                        pass
                    else:
                        if not self.output or 'Location' not in self.output:
                            (newLocation, newArguments) = self.generateArguments(window)
                            newArguments = normalizeFields(newArguments)
                            if newLocation != location or newArguments != arguments:
                                if self.debugArguments:
                                    print "Old: %s: %s" %(location, arguments)
                                    print "New: %s: %s" % (newLocation, newArguments)
                                self.redirect(winId, newLocation, newArguments, outputOptions)
            else:
                self.processNotifications()

            if self.output is not None:
                for key, value in self.output.iteritems():
                    if key is not Constants.OUTPUT:
                        response.setHeader(key.encode('utf-8'), value.encode('utf-8'))
                if Constants.OUTPUT in self.output:
                    content = self.output[Constants.OUTPUT]
                    if isinstance(content, types.StringType):
                        self.program.write(content)
                    else:
                        for item in content:
                            self.program.write(item)
            else:
                response.setHeader('Status', '404 No such window')
                response.setHeader('Content-Type', 'text/plain')
                self.program.writeln('404 No such window')

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
            self.addNotification(self.Notification(*arg, **kw))

        def addNotification(self, notification):
            if self.debugSendNotification: print "Add notification:", notification
            self.notifications.append(notification)

        def processNotifications(self):
            """Processes any pending notifications. Mainly used internally by writeHTML."""
            while self.notifications:
                notification = self.notifications[0]
                del self.notifications[0]
                notification.process()

        def calculateUrl(self, winId, location, arguments, outputOptions):
            windowPath = self.program.request().servletURI()
            if winId != Constants.DEFAULT_WINDOW:
                windowPath += '/_' + winId
            path = self.program.webwareBase() + windowPath
            if location:
                path += '/' + '/'.join(location)
            return path + '?' + urllib.urlencode(arguments.items() +
                                                 [('_' + key, value)
                                                  for (key, value)
                                                  in outputOptions.items()])

        def redirect(self, winId, location, arguments, outputOptions):
            self.output = {'Status': '303 See Other',
                           'Location': self.calculateUrl(winId, location, arguments, outputOptions)}

        def newWindow(self, winId):
            """You should override this to return a Window instance in
            your own application."""
            raise Constants.OutputGiven

