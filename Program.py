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
import cgi, urllib, types, os
import Utils, Widgets, AccessManager, Constants
import hotshot, pdb

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

    profile = True
    debug = False
    
    requestNr = 0

    def writeHTML(self):
        """Main processing method, called by WebWare."""

        type(self).requestNr += 1
        
        session = self.session()
        servlet = self.request().servletURI()
        if not session.hasValue(servlet):
            session[servlet] = self.Session()
        session[servlet].program = self
        fn = session[servlet].handleRequest

        if self.profile:
            nonProfiledFn = fn
            def profileFn():
                profiler = hotshot.Profile("webwidgets.profile.request.%s" % type(self).requestNr)
                profiler.addinfo('url', self.requestBase() + self.request().extraURLPath() + '?' + self.request().queryString())
                try:
                    return profiler.runcall(nonProfiledFn)
                finally:
                    profiler.close()
            fn = profileFn

        if self.debug:
            nondebuggedFn = fn
            def debugFn():
                return pdb.runcall(nondebuggedFn)
            fn = debugFn

        return fn()

    def webwareBase(self):
        """@return: A URL to where the Webware installation is serving
        documents from."""
        #### fixme ####
        # name = "https not supported"
        # description = """Yes, we should check for https, but WebWare
        # is braindead and doesn't provide that info _at_all_!"""
        #### end ####
        req = self.request()

        # Work-around empty adapter name
        adapter = req.adapterName()
        
        return 'http://' + req._environ['HTTP_HOST'] + adapter

    def requestBase(self):
        """@return: A URL to this Webwidgets application."""
        return self.webwareBase() + self.request().servletURI()

    class Session(object):
        """The application programmer should subclass this class and
        implement the L{Webwidgets.Program.Program.Session.newWindow}
        method.
        """
        
        debugArguments = False
        debugFields = False
        debugFieldInput = False
        debugReceiveNotification = False

        root = True
        parent = None
        name = None

        def __init__(self):
            self.windows = Widgets.Base.ChildNodes(self)
            self.notifications = []
            self.output = None
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
                    path = instance._path
                    if isinstance(path, list):
                        return path
                    widgetPath = instance.widget.path
                    if path is None:
                        return widgetPath
                    if widgetPath is None:
                        return None
                    return list(widgetPath + path)

                def __set__(self, instance, value):
                    instance._path = value
            path = Path()

            def parent(self):
                if self.widget.parent is None:
                    raise StopIteration()
                return type(self)(self.widget.parent, self.message, self.args, self.kw, self.path)

            def process(self):
                if self.widget.session.debugReceiveNotification:
                    print "Notifying %s" % self
                try:
                    if hasattr(self.widget, self.message):
                        # Run the notification handler!
                        if getattr(self.widget, self.message
                                   )(self.path, *self.args, **self.kw):
                            # FIXME: Workaround to support the old API!
                            raise StopIteration()
                    return self.parent().process()
                except StopIteration:
                    # Notification consumed
                    pass

            def __repr__(self):
                return "Notification(%s)" % (unicode(self),)
            
            def __unicode__(self):
                return "%s/%s <- %s(%s, %s)" % (
                    self.widget, self.path, self.message, self.args, self.kw)

            def __str__(self):
                return str(unicode(self))

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
                        window.draw({})
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

            sortedArguments = window.arguments.items()
            sortedArguments.sort(lambda (name1, argument1), (name2, argument2):
                                 argument1['widget'].inputOrder(argument2['widget']))

            for argumentname, argument in sortedArguments:
                path = argument['path']
                argument = argument['widget']
                # Check an extra time that the widget is
                # active, just for added paranoia :) The argument
                # should'nt ever be there if it isn't but some
                # sloppy widget hacker migt have forgotten to
                # not to add it...
                if argument.getActive(path):
                    value = arguments.get(argumentname, '')
                    if not isinstance(value, types.ListType):
                        value = [value]
                    if argument.fieldOutput(path) != value:
                        argument.fieldInput(path, *value)

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

            sortedFields = window.fields.items()
            sortedFields.sort(lambda (name1, field1), (name2, field2):
                              field1.inputOrder(field2))
                
            for fieldname, field in sortedFields:
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
                        if self.debugFieldInput:
                            print "Field input:", path, fieldname, field.fieldOutput(path), value
                        field.fieldInput(path, *value)

        def handleRequest(self):
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

            baseOptions = {'widgetClass': Constants.DEFAULT_WIDGET_CLASS,
                           'winId': Constants.DEFAULT_WINDOW,
                           'widget': Constants.DEFAULT_WIDGET}
            if location and location[0].startswith('_'):
                baseOptions['widgetClass'] = location[0][1:]
                location = location[1:]
            if location and location[0].startswith('_'):
                baseOptions['winId'] = location[0][1:]
                location = location[1:]
            if location and location[0].startswith('_'):
                baseOptions['widget'] = location[0][1:]
                location = location[1:]
            baseOptions['location'] = location

            arguments = decodeFields(normalizeFields(cgi.parse_qs(req.queryString())))
            arguments, outputOptions = filterArguments(arguments)
            outputOptions.update(baseOptions)

            obj = Utils.loadClass(outputOptions['widgetClass'])
            assert issubclass(obj, Program.Session) or issubclass(obj, Widgets.Base.Widget)
            fnName = 'classOutput'
            if 'aspect' in outputOptions:
                fnName += '_' + outputOptions['aspect']
            outputFn = getattr(obj, fnName)

            try:
                self.output = outputFn(self, arguments, outputOptions)
            except Constants.OutputGiven:
                pass

            if self.output is None:
                self.output = {'Status': '404 No such window',
                               'Content-Type': 'text/plain',
                               Constants.OUTPUT: '404 No such window'}

            for key, value in self.output.iteritems():
                if key not in (Constants.OUTPUT, Constants.FINAL_OUTPUT):
                    response.setHeader(key.encode('utf-8'), value.encode('utf-8'))
            content = None
            if Constants.OUTPUT in self.output:
                content = self.output[Constants.OUTPUT]
            if Constants.FINAL_OUTPUT in self.output:
                content = self.output[Constants.FINAL_OUTPUT]
            if isinstance(content, types.StringType):
                self.program.write(content)
            elif content is not None:
                for item in content:
                    self.program.write(item)

        def classOutput(cls, session, arguments, outputOptions):
            req = session.program.request()
            response = session.program.response()

            window = session.getWindow(outputOptions['winId'])
            if window:
                session.processArguments(window, outputOptions['location'], arguments)
                if req.method() == 'POST':
                    session.processFields(window,
                                          decodeFields(normalizeFields(req.fields())))

                obj = window
                fnName = 'output'
                args = (outputOptions,)
                if 'widget' in outputOptions:
                    for name in Utils.idToPath(outputOptions['widget']):
                        obj = obj[name]
                if 'aspect' in outputOptions:
                    fnName += '_' + outputOptions['aspect']
                outputFn = getattr(obj, fnName)

                res = outputFn(*args)
                if (not res
                    or (    'Location' not in res
                        and Constants.FINAL_OUTPUT not in res)):
                    (newLocation, newArguments) = session.generateArguments(window)
                    newArguments = normalizeFields(newArguments)
                    if (   newLocation != outputOptions['location']
                        or newArguments != arguments):
                        if session.debugArguments:
                            print "Old: %s: %s" % (outputOptions['location'], arguments)
                            print "New: %s: %s" % (newLocation, newArguments)
                        session.redirect(
                            Utils.subclassDict(outputOptions,
                                               {'location': newLocation}),

                            newArguments)
                return res
        classOutput = classmethod(classOutput)

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

        def calculateUrl(self, outputOptions, arguments):
            path = [self.program.requestBase()]

            if (   (    'widgetClass' in outputOptions
                    and outputOptions['widgetClass'] != Constants.DEFAULT_WIDGET_CLASS)
                or (    'winId' in outputOptions
                    and outputOptions['winId'] != Constants.DEFAULT_WINDOW)
                or (    'widget' in outputOptions
                    and outputOptions['widget'] != Constants.DEFAULT_WIDGET)):
                path.append('_' + outputOptions.get('widgetClass', Constants.DEFAULT_WIDGET_CLASS))
                if (   (    'winId' in outputOptions
                        and outputOptions['winId'] != Constants.DEFAULT_WINDOW)
                    or (    'widget' in outputOptions
                        and outputOptions['widget'] != Constants.DEFAULT_WIDGET)):
                    path.append('_' + outputOptions.get('winId', Constants.DEFAULT_WINDOW))
                    if (    'widget' in outputOptions
                        and outputOptions['widget'] != Constants.DEFAULT_WIDGET):
                        path.append('_' + outputOptions['widget'])
                
            if 'location' in outputOptions and outputOptions['location']:
                path.extend(outputOptions['location'])

            urlArgList = []
            for key, value in arguments.iteritems():
                if not isinstance(value, list): value = [value]
                for valuePart in value:
                    urlArgList.append((key, valuePart))
            for key, value in outputOptions.iteritems():
                if key not in ('widgetClass', 'winId', 'widget', 'location'):
                    if not isinstance(value, list): value = [value]
                    for valuePart in value:
                        urlArgList.append(('_' + key, valuePart))

            return '/'.join(path) + '?' + urllib.urlencode(urlArgList)

        def redirect(self, outputOptions, arguments):
            self.output = {'Status': '303 See Other',
                           'Location': self.calculateUrl(outputOptions,
                                                         arguments)}
            raise Constants.OutputGiven
        
        def newWindow(self, winId):
            """You should override this to return a Window instance in
            your own application."""
            raise Constants.OutputGiven
