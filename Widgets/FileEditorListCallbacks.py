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

import Webwidgets

class Value(object):
    empty = ''
    def __get__(self, instance, owner):
        if not instance or instance.file_editor is None:
            return None
        if instance.file_editor.value is None:
            return self.empty
        if not hasattr(instance.file_editor.value, self.attribute):
            setattr(instance.file_editor.value, self.attribute, '')
        return getattr(instance.file_editor.value, self.attribute)
    def __set__(self, instance, value):
        if instance.file_editor.value is not None :
            setattr(instance.file_editor.value, self.attribute, value)

class FileEditorList(object):
    def __init__(self, session, win_id, **attrs):
        self.__dict__['rows'] = []
        Webwidgets.Table.__init__(self, session, win_id, **attrs)
        
    class NameInput(Webwidgets.StringInput):
        ww_explicit_load = True
        file_editor = None
        
        class NameValue(Value):
            attribute = 'filename'
            empty = '&lt;No file&gt'
        value = NameValue()

    class DescriptionInput(Webwidgets.StringInput):
        ww_explicit_load = True
        file_editor = None
        cols = 40
        rows_expanded = 10
        rows_collapsed = 1

        class Rows(object):
            def __get__(self, instance, owner):
                if not instance or instance.file_editor is None:
                    return None
                return [instance.rows_collapsed, instance.rows_expanded][instance.file_editor.expanded]
        rows = Rows()
        
        class DescriptionValue(Value):
            attribute = 'description'
        value = DescriptionValue()

    def add_row(self, file = None):
        file_editor = self.FileEditor(self.session, self.win_id, value = file)
        self.rows.append({
            'name': self.NameInput(self.session, self.win_id, file_editor = file_editor),
            'description': self.DescriptionInput(self.session, self.win_id, file_editor = file_editor),
            'file': file_editor
            })

    def group_function(self, path, function):
        if path != self.path: return
        if function == 'add':
            self.add_row()
            self.rows[-1]['file'].expanded = True

    def function(self, path, function, row):
        if path != self.path: return
        if function == 'delete':
            del self.rows[row]
        if function == 'edit':
            self.rows[row]['file'].expanded = not self.rows[row]['file'].expanded

    class FileListValue(object):
        def __get__(self, instance, owner):
            if not instance or instance.rows is None:
                return None
            return [row['file'].value
                    for row in instance.rows
                    if row['file'].value is not None]
        def __set__(self, instance, value):
            if instance.rows is not None:
                del instance.rows[:]
                for file in value:
                    if file is not None:
                        instance.add_row(file)
    value = FileListValue()

    def reset(self):
        self.rows = []
