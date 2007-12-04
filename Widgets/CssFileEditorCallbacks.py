# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
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

import Base, Formatting, cgi

class CssFileEditor(Base.ValueInput):
    original_value = value = None

    class input(object):
        class Value(object):
            def __get__(self, instance, owner):
                if instance is None or instance.parent is None:
                    return None
                return instance.parent.value
            def __set__(self, instance, value):
                instance.parent.value = value
        value = Value()

    class preview(object):
        types = dict(Formatting.Media.types)
        types['default'] = dict(types['default'])
        types['default']['width'] = None
        types['default']['height'] = None

        class Content(object):
            def __get__(self, instance, owner):
                if instance is None or instance.parent is None:
                    return None
                return instance.parent.value
        content = Content()
