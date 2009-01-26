#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moeller@freecode.no>

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

"""
L{Wwml<Webwidgets.Wwml>} is used to define the user interface in terms
of widgets inside each others. Some of these widgets are then bound to
classes with callback methods that define the behaviour of the
application (application logic).

This module contains callbacks for the application L{main
window<Webwidgets.Demo.WidgetParade.UI.MyWindow>}. Submodules contains
callbacks for subwidgets (the different screens).

The following is the Wwml file using this module::

  <w:wwml
   xmlns="http://www.w3.org/TR/REC-html40"
   xmlns:w="http://freecode.no/xml/namespaces/wwml-1.0"
   xmlns:html="http://www.w3.org/TR/REC-html40"
   using="Webwidgets.Demo.WidgetParade.UI"
   bind="Webwidgets.Demo.WidgetParade.UICallbacks"
   >
   <w:ApplicationWindow
    id="MyWindow"
    title="RedBack Webwidgets demo application">
    <w:ApplicationWindow.Body.LogIn.Application classid="Body.LogIn.Application" page=":path:Home">
     <w:pre>
      <w:Home.Home id="Home" />
      <w:Input.Input id="Input" />
      <w:Formatting.Formatting id="Formatting" />
      <w:Composite.Composite id="Composite" />
      <w:Dynamic.Dynamic id="Dynamic" />
      <w:Errors.Errors id="Errors" />
      <w:Config.Config id="Config" />
     </w:pre>
    </w:ApplicationWindow.Body.LogIn.Application>
   </w:ApplicationWindow>
  </w:wwml>

Hey, that was a load of XML in that Wwml-file. Actually, quite a lot
of it was just boilerplate that needs to be there for it to be correct
XML and thus Wwml. We'll go though the code line-by line now. The
first few lines is boilerplate for setting up namespaces for Wwml tags
and HTML tags, so that they can be freely mixed::

  <w:wwml
   xmlns="http://www.w3.org/TR/REC-html40"
   xmlns:w="http://freecode.no/xml/namespaces/wwml-1.0"
   xmlns:html="http://www.w3.org/TR/REC-html40"

The Wwml parser needs to be told in which Python modules to look for
widgets that are used in this Wwml file. More than one module can be
specified, separated by a space. The special module C{Webwidgets} is
allways searched last, and doesn't need to be included explicitly. The
following line tells the parser to look in the
C{Webwidgets.Demo.WidgetParade.UI} in addition to C{Webwidgets}::
   
  using="Webwidgets.Demo.WidgetParade.UI"

The next line binds the python module
C{Webwidgets.Demo.WidgetParade.UICallbacks} to the widgets in the
interface definition, so that the callback functions defined in there
will be called when the user interacts with the UI::

  bind="Webwidgets.Demo.WidgetParade.UICallbacks"
  >

Bindings are inherited by widgets and their subwidgets, so the above
line will cuase e.g. the widget C{MyWindow.Body.LogIn} to bind to
L{Webwidgets.Demo.WidgetParade.UICallbacks.MyWindow.Body.LogIn} (this
binding provides the widget with an authentication method used to
authenticate logins to the application).

After this boilerplate follows the definition of the user interface
itself. At the top-level is our main window widget. In this case implemented
using a "standard application" template widget - L{Webwidgets.ApplicationWindow}. This template
provides a log-in dialog and a main menu as one widget.

The tag name is the name of an existing widget, either defined in some
other Wwml-file in the aplication, or one of the predefined ones from
the Webwidgets package. The id tag is required, and gives the name of
the widget to creat. More information on the tag syntax can be found
at Basic tag structure::

  <w:ApplicationWindow
   id="MyWindow"
   title="RedBack Webwidgets demo application">


We need to override the main menu contents of the template widget.

We override specific subwidgets far down in the widget tree by using
their dotted paths (relative to the surrounding widget, that is,
C{MyWindow} in this case) as C{id}::

  <w:ApplicationWindow.Body.LogIn.Application

C{classid} is used instead of C{id} to signify that a widget, in this
case the screen shown to logged in users, is not instantiated
automatically, but by some callback, in this case the
C{authenticate()} method of the log-in widget::

  classid="Body.LogIn.Application"

Set the default page (the page shown when the user has just logged in)::

  page=":path:Home">

Add some pages to the (beginning og the) menu. These ones are defined
in separate sub-modules::

  <w:pre>
   <w:Home.Home id="Home" />
   <w:Input.Input id="Input" />
   <w:Formatting.Formatting id="Formatting" />
   <w:Composite.Composite id="Composite" />
   <w:Dynamic.Dynamic id="Dynamic" />
   <w:Errors.Errors id="Errors" />
   <w:Config.Config id="Config" />
  </w:pre>

There are several callbacks that can be defined, and the available
callbacks varies from widget to widget. Every callback takes a
different set of parameters, but they all share the first parameter -
path, which is the path through the widget tree to the widget who's
callback is called.

See the L{Input
screen<Webwidgets.Demo.WidgetParade.UICallbacks.Input>} for more
examples of how the callback system works.
"""

class MyWindow(object):
    class Body(object):
        class LogIn(object):
            def authenticate(self, username, password):
                """This method is used to authenticate log-ins to the
                application. For this demo, the correct password is
                the same as the username!"""
                if username != password:
                    raise Exception("For this demo, the correct password is the same as the username!")
                return True
