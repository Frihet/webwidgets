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

class Singleton(object):
    class __metaclass__(type):
        def __repr__(self):
            return "%s.%s" % (self.__module__, self.__name__)
        def __str__(self):
            return self.__name__

DEFAULT_WINDOW = 'default'

class OUTPUT(Singleton): pass

class OutputGiven(Exception): pass        

class NotASubwidgetException(Exception): pass

class EDIT(Singleton): pass
class REARRANGE(Singleton): pass
class VIEW(Singleton): pass
class SUBTREE(Singleton): pass
class ONE(Singleton): pass
