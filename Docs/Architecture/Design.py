# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework

# Copyright (C) 2009 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

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
User interfaces as widget trees
===============================

  In Webwidgets everything you see is a widget. Even an application is
  a widget. Each such widget might in its turn consist of several
  other widgets, either by incorporating them as child widgets or by
  subclassing them.

  The aim of this library is to encourage and ease code re-use - user
  interface functionality can easily be packaged and reused throughout
  a set of applications.



Statefull widgets
=================

  Each widget is implemented as a Python class. A web user session
  then consists of one or more instance of such classes.

  As these instances are part of the session, they survive between
  page-loads, and member variables of the widget, such as the one
  holding the value for a string input box or the label string for a
  button, stay the same until actively changed by the user (for input
  widgets) or by the application code.

  This removes the burden of re-creating the user interface at each
  page-load, re-reading values from the database at each page-load,
  and manually managing session content.


Notifications
=============

  As soon as an attribute of a widget is changed, either by user input
  or by some code, a notification is sent to the widget. This
  notification is named as the attribute, with C{Changed} appended,
  e.g. C{value_changed} for the C{value} attribute, and raised with
  the new value as sole parameter.

  A notification is implemented as a call to a method on the widget
  with a special first parameter C{path} that holds the path to the
  widget. Unless that method breaks out by raising a C{StopIteration}
  exception, the notification is propagated to the parent widget up to
  the top-level C{Window}. All the way through this propagation, the
  C{path} parameter stays the same, pointing to the originally
  notified widget.

  The propagation makes it possible to implement a complicated widget
  with many fields and just one single function to handle all of the
  state changes.


Input handling
==============

  Input handling is done using two special methods, C{field_input} and
  C{field_output}. The former method is called with a list of field
  values, and can update any attributes on the widget as it sees fit.
  This in turn raises notifications as usual. The latter method is
  used to query the widget for its current state and should return a
  list of the same format. This is used to inhibit calls to
  field_input when the user hasn't actually changed anything.


URL argument handling
=====================

  URL arguments (C{GET} parameters) are grafted onto the Webwidgets
  framework which is based on a global HTML form and C{POST} requests.
  Their main purpose is to allow the user to bookmark a page, and as
  an alternative way of user input and output.

  URL arguments always corresponds to widget attribute values. If not,
  the widget attributes are updated (and notifications sent as usual).

  However, all widget attributes need not be present in the URL,
  specifically attributes of hidden widgets are never present in the
  URL. If a previously hidden widget is made visible and has
  attributes that are supposed to be in the URL, the browser is sent a
  HTTP redirect to a new URL containing those new values.

  This provides the functionality the user expects while requiring the
  least amount of effort from the application programmer.


Output options
==============

  FIXME



Windows
=======

  A Webwidgets application can provide the user with several separate
  pages or windows each with its own widget tree and URL. These
  windows are created by the application after the user has navigated
  to the corresponding URL and must be destroyed by the application
  code manually (ultimately, they are destroyed as the session is
  destroyed when it times out).

  It is sometimes desirable to have separate pop-up-windows or frames
  with their own state. This functionality provides that.
"""
