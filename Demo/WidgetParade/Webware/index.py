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

"""Main Webware page connecting the root URL for this application to
its L{Webwidgets.Demo.WidgetParade.UI.Window} widget, global debugging
options are also set from within this module.

Most applications will only have one Webware page.

The webware page module must contain a class named the same as the
module, in this case L{index}.
"""

import Webwidgets

Webwidgets.Program.Session.debug_fields = False
Webwidgets.Program.Session.debug_field_input = False
Webwidgets.Program.Session.debug_receive_notification = False
Webwidgets.Program.Session.debug_arguments = False
Webwidgets.Wwml.debug_import = True

import Webwidgets.Demo.WidgetParade.UI

class index(Webwidgets.Program):
    """The Webware page class must be named the same as the webware
    page module, inherit from L{Webwidgets.Program} and overide the
    C{Session} class member."""
    
    class Session(Webwidgets.Program.Session):
        """Every user session (wether logged in or not) will be
        represented by an instance of this class. It must inherit from
        L{Webwidgets.Program.Session} and provide a method
        L{new_window}."""

        def new_window(self, win_id):
            """This method is where the boilerplate ends and your
            application really begins.

            It loads the top-level widget of your user interface, a
            L{Webwidgets.HtmlWindow} subclass, and instanciates it. In
            this case, this widget is called
            L{MyWindow<Webwidgets.Demo.WidgetParade.UI.MyWindow>}.

            It is called whenever the user accesses a new base URL
            under your application. The returned window widget
            together with its child widgets will then serve that URL
            (and any subdirectory URLs that the window or its child
            widgets supports).

            The L{Webwidgets.HtmlWindow} subclass is usually created
            in the L{UI module<Webwidgets.Demo.WidgetParade.UI>} using
            the L{WWML<Webwidgets.Wwml>} language language.

            It is possible to write the user interface definition in
            pure Python which allows for greate flexibility, but is
            also quite verbose and requires lots and lots of
            boilerplate code.

            WWML is a simple XML-based language for defining the UI
            layout (but not the actual look - that's the job of CSS!).

            Not only does Wwml simplify the work to create widgets, it
            also helps separating the layout from the application
            code, which is stored in a separate python module file. In
            this example, that's the L{UICallbacks
            module<Webwidgets.Demo.WidgetParade.UICallbacks>}.
            """
            
            return Webwidgets.Demo.WidgetParade.UI.MyWindow(self, win_id)
