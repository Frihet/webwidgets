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

class Singleton(object):
    class __metaclass__(type):
        def __repr__(self):
            return "%s.%s" % (self.__module__, self.__name__)
        def __str__(self):
            return self.__name__

DEFAULT_WIDGET_CLASS = 'Webwidgets.Program.Session'
DEFAULT_WINDOW = 'default'
DEFAULT_WIDGET = 'root'

class OUTPUT(Singleton): pass
class FINAL_OUTPUT(OUTPUT): pass

class OutputGiven(Exception):
    """This exception can be thrown anywhere from within get_window(),
    class_output(), output() or draw() (of any widget), and will
    immediately abort the current page and replace it with whatever
    content is supplied to the init function of this exception (same
    format as what can be returned by output())."""
    def __init__(self, output = None):
        self.output = output

class NotASubwidgetException(Exception): pass

class EDIT(Singleton): pass
class RARR(Singleton): pass
class VIEW(Singleton): pass
class SUB(Singleton): pass
class ONE(Singleton): pass
