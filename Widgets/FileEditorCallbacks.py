#! /bin/env python
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

import Webwidgets, cgi, traceback

def mime_type_to_method(mime_type):
    return mime_type.replace("/", "__").replace("-", "_")

def method_to_mime_type(mime_type):
    return mime_type.replace("__", "/").replace("_", "-")

class Value(object):
    def __get__(self, instance, owner):
        if instance is None or instance.parent is None:
            return None
        return instance.parent.parent.value
    def __set__(self, instance, value):
        instance.parent.parent.value = value
        
class FileEditor(Webwidgets.ValueInput):
    def __init__(self, session, win_id, **attr):
        Webwidgets.Html.__init__(self, session, win_id, **attr)
        self.value_changed(self.path, self.value)
        self.expanded_changed(self.path, self.expanded)

    original_value = value = None
    error = None
    expanded = False

    def mime_type_to_method(self, mime_type):
        return mime_type_to_method(mime_type)
    
    def method_to_mime_type(self, mime_type):
        return method_to_mime_type(mime_type)

    class DownloadLink(object):
        class Content(object):
            def __get__(self, instance, owner):
                if instance is None or instance.parent is None:
                    return None
                return instance.parent.value
        content = Content()

    class Hide(object):
        class Value(object):
            def __get__(self, instance, owner):
                if instance is None or instance.parent is None:
                    return None
                return instance.parent.expanded
            def __set__(self, instance, value):
                instance.parent.expanded = value
        value = Value()

    def expanded_changed(self, path, value):
        self['InfoGroup'].visible = self['Editors'].visible = self['Upload'].visible = value

    class InfoGroup(object):
        class Name(object):
            class Field(object):
                class Value(object):
                    def __get__(self, instance, owner):
                        if instance is None or instance.parent is None:
                            return None
                        return getattr(instance.parent.parent.parent.value, 'filename', '&lt;No file&gt;')
                    def __set__(self, instance, value):
                        if instance.parent.parent.parent.value is not None:
                            instance.parent.parent.parent.value.filename = value
                value = Value()

    class Editors(object):
        class text__css(object):
            value = Value()
        class text__plain(object):
            value = Value()
        class text__html(object):
            value = Value()
        class default(object):
            content = Value()
        def page_changed(self, path, page):
            Webwidgets.TabbedView.page_changed(self, path, page)
            if page not in (None, ['default']):
                if page == ['none']:
                    self.parent.value = None
                else:
                    mime_type = method_to_mime_type(page[0])
                    value = self.parent.value
                    if value is None or mime_type != value.type:
                        if value is None:
                            value = cgi.FieldStorage()
                        value.type = mime_type
                        if value.file is None:
                            value.file = value.make_file()
                        value.file.seek(0)
                        value.file.truncate()
                        value.filename = "new %s file" % mime_type
                        self.parent.value = value
            
    class Upload(object):
        class Action(object):
            def clicked(self, path):
                value = self.parent['File'].value
                editors = self.parent.parent['Editors']
                if value is not None:
                    editor = mime_type_to_method(value.type)
                    if editor not in editors.children:
                        if editors['default'].visible:
                            editor = 'default'
                        else:
                            self.parent['File'].error = 'Unrecognized file-type: %s' % value.type
                            return
                    elif not editors[editor].visible:
                        self.parent['File'].error = 'Unallowed file-type: %s' % value.type
                        return
                self.parent.parent.value = value

    def value_changed(self, path, value):
        if path != self.path: return
        editor = mime_type_to_method(getattr(value, 'type', 'none'))
        if editor not in self['Editors'].children:
            editor = 'default'
        self['Editors'].page = [editor]
        
