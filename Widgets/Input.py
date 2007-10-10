#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Axel Liljencrantz <axel.liljencrantz@freecode.no>

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

"""Widgets for user input.
"""

import types, cgi
import Webwidgets.Utils, Webwidgets.Constants
import Base, Formatting

class ArgumentInput(Base.ValueInput):
    """This input widget does not actually renders into any HTML but
    instead represents a parameter in the URL. L{argument_name} is
    mandatory for this widget to be usefull.

    Special note: The two special URL argument names '__location__'
    and '__extra__' represents any extra path in URL and any argments
    not named by any other input field, respectively.

    As those two fields have to be defined, L{Window} defines two
    children that are subww_classes of this class for this purpose. If
    you need to implement these two widgets somwhere else in the
    widget tree, you must replace those two widgets with something
    else, e.g. the empty string.
    """
    
    def draw(self, output_options):
        self.register_input(self.path, self.argument_name, False)
        return ''

class HiddenInput(Base.ValueInput):
    """Hidden input box. Note that this is only usefull to communicate
    with some JavaScript."""
    def draw(self, output_options):
        super(HiddenInput, self).draw(output_options)
        return '<input %(attr_html_attributes)s type="hidden" name="%(name)s" value="%(value)s" %(disabled)s />' % {
            'attr_html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'value': self.field_output(self.path)[0],
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}

class StringInput(Base.ValueInput):
    """Text input box"""
    rows = 1
    cols = None

    def draw(self, output_options):
        super(StringInput, self).draw(output_options)
	info = {'attr_html_attributes': self.draw_html_attributes(self.path),
                'name': Webwidgets.Utils.path_to_id(self.path),
                'value': self.field_output(self.path)[0],
                'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)],
                'rows': self.rows,
                'cols': ['', 'cols="%s"' % self.cols][self.cols is not None],
                'size': ['', 'size="%s"' % self.cols][self.cols is not None]}

        if self.rows > 1:
            return '<textarea %(attr_html_attributes)s rows="%(rows)s" %(cols)s name="%(name)s" %(disabled)s>%(value)s</textarea>' % info
        else:
            return '<input %(attr_html_attributes)s %(size)s type="text" name="%(name)s" value="%(value)s" %(disabled)s />' % info

class PasswordInput(Base.ValueInput):
    """Like StringInput, but hides the user input"""
    def draw(self, output_options):
        super(PasswordInput, self).draw(output_options)
        return '<input %(attr_html_attributes)s type="password" name="%(name)s" value="%(value)s" %(disabled)s />' % {
            'attr_html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'value': self.field_output(self.path)[0],
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}

class NewPasswordInput(Formatting.Html, Base.ValueInput):
    """Used for entering new passwords - the password has to be
    repeated twice and the two values entered are compared. A
    value_changed is only propagated if the two values matches"""
    __wwml_html_override__ = False
    value = ''
    html = """
    <span %(attr_html_attributes)s>
     %(input1)s
     %(input2)s
    </span>
    """
    def __init__(self, session, win_id, **attrs):
        Formatting.Html.__init__(
            self, session, win_id,
            **attrs)
        self.children['input1'] = self.Input(session, win_id, value=self.value)
        self.children['input2'] = self.Input(session, win_id, value=self.value)

    class Input(PasswordInput):
        __explicit_load__ = True
        
        def value_changed(self, path, value):
            if self.parent['input1'].value == self.parent['input2'].value:
                print "Passwords matches", self.parent['input1'].value, self.parent['input2'].value
                self.parent.value = value
            else:
                self.parent.value = None
                self.parent.error = "Passwords don't match!"
            return True

        def get_active(self, path):
            return self.parent.get_active(path[:-1])

    def value_changed(self, path, value):
        if path != self.path: return
        if value is None: return
        # If we get this from anywhere else than input1 and input2, we
        # must set their values too...
        self['input1'].value = self['input2'].value = self.value
        self.error = None

class Button(Base.ActionInput):
    """Button widget - throws a "clicked" notification when clicked"""
    title = ''

    def draw(self, output_options):
        super(Button, self).draw(output_options)
        return '<input %(attr_html_attributes)s type="submit" %(disabled)s name="%(name)s" value="%(title)s" />' % {
            'attr_html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'title': self._(self.title, output_options),
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}

class UpdateButton(Base.ActionInput):
    """This is a special kind of button that only submits the form and
    causes other widgets to get their input. In addition, it
    dissapears if JavaScript is enabled. It is intended to be used in
    conjunction with register_submit_action() on other widgets."""

    def draw(self, output_options):
        Base.ActionInput.draw(self, output_options)
        info = {'attr_html_attributes': self.draw_html_attributes(self.path),
                'id': Webwidgets.Utils.path_to_id(self.path),
                'title': self._("Update", output_options),
                'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}
        self.register_script('update_button: %(id)s' % info,
                            """
                            webwidgets_add_event_handler(window, 'load',
                             'webwidgets_update_button: %(id)s',
                             function () {
                              document.getElementById('%(id)s').style.display = 'none';
                             });
                            """ % info)
        return '<input %(attr_html_attributes)s type="submit" %(disabled)s name="%(id)s" value="%(title)s" />' % info

    def field_input(self, path, string_value):
        pass

class RadioButtonGroup(Base.ValueInput):
    """Group of radio buttons must be joined together. This is
    performed by setting the 'group' attribute on each of the
    L{RadioInput} in the group to the same instance of this class."""
    
    def __init__(self, session, win_id, *arg, **kw):
        Base.ValueInput.__init__(self, session, win_id, *arg, **kw)
        self.members = {}

class RadioInput(Base.ValueInput, Base.StaticComposite):
    """A radio button (selection list item). You must create a
    L{RadioButtonGroup} instance and set the 'group' attribute to that
    instance so that all radio buttons in the group knows about each
    other."""
    def __init__(self, session, win_id, **attrs):
        Base.StaticComposite.__init__(self, session, win_id, **attrs)
        self.group.members[self.value] = self
        if self.default:
            self.group.value = self.value

    def field_input(self, path, string_value):
        value = Utils.id_to_path(string_value)
        if value == path:
            self.group.value = self.value

    def field_output(self, path):
        return [Utils.path_to_id(self.group.members[self.group.value].path)]

    def draw(self, output_options):
        self.register_input(self.group.path, self.argument_name)
        result = self.draw_children(output_options, include_attributes = True)
        result['name'] = Webwidgets.Utils.path_to_id(self.group.path)
        result['value'] = result['id']
        result['checked'] = ['', 'checked'][self.value == self.group.value]
        result['disabled'] = ['', 'disabled="disabled"'][not self.get_active(self.path)],
        return """<input
                   %(attr_html_attributes)s
                   type="radio"
                   name="%(name)s"
                   value="%(value)s"
                   %(checked)s
                   %(disabled)s
                  >%(title)s</input>""" % result

class Checkbox(Base.ValueInput):
    """Boolean input widget - it's value can either be true or false."""
    value = False
    def draw(self, output_options):
        super(Checkbox, self).draw(output_options)
        checked = ["", 'checked="checked"'][not not self.value]
        return '<input %(attr_html_attributes)s type="checkbox" name="%(name)s" value="checked" %(checked)s %(disabled)s />' % {
            'attr_html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'checked': checked,
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}

    def field_input(self, path, string_value):
        self.value = (string_value == "checked")

    def field_output(self, path):
        return [['', 'checked'][not not self.value]]

class ListInput(Base.ValueInput, Base.StaticComposite):
    """Scrollable list of selectable items. The list can optionally
    allow the user to select multiple items."""
    
    multiple = False
    """Allow the user to select multiple items."""
    
    size = 0
    """Size of the widget."""
    
    value = []

    def draw(self, output_options):
        Base.ValueInput.draw(self, output_options)
        children = self.draw_children(output_options)
        child_names = children.keys()
        child_names.sort()
        values = self.value
        if not isinstance(values, types.ListType):
            values = [values]
        options = '\n'.join([
            """<option %(selected)s value="%(value)s">
             %(description)s
            </option>""" % {'selected': child_name in values and 'selected="selected"' or '',
                           'value': child_name,
                           'description': children[child_name]}
            for child_name
            in child_names])

        return """<select %(attr_html_attributes)s %(multiple)s %(size)s name="%(name)s" %(disabled)s>
         %(options)s
         </select>""" % {
            'attr_html_attributes': self.draw_html_attributes(self.path),
            'multiple': self.multiple and 'multiple' or '',
            'size': self.size != 0 and 'size="%s"' % self.size or '',
            'name': Webwidgets.Utils.path_to_id(self.path),
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)],
            'options': options
            }


class FileInput(Base.ValueInput, Base.StaticComposite):
    """File upload box"""
    value = None
    
    def field_input(self, path, field_value):
        if path == self.path:
            if field_value != '':
                self.value = field_value
                
    def field_output(self, path):
        return [self.value]

    class preview(Formatting.Media):
        class Content(object):
            def __get__(self, instance, owner):
                if instance.parent is None:
                    return None
                return instance.parent.value
        content = Content()

    class clear(Button):
        title = 'Clear'
        def clicked(self, path):
            self.parent.value = None
        def get_active(self, path):
            return self.parent.get_active(path[:-1]) and self.parent.value != None
        
    def output(self, output_options):
        res = {Webwidgets.Constants.OUTPUT: self.value.file.read(),
               'Content-type': value.type
               }
        value.file.seek(0)
        return res

    def draw(self, output_options):
        super(FileInput, self).draw(output_options)
        if self.get_active(self.path):
            self.register_input(self.path, self.argument_name)
            if self.value is not None:
                argument_name = self.argument_name
                if argument_name: argument_name = argument_name + '_clear'
                self.register_input(self.path + ['_', 'clear'], argument_name)

        result = self.draw_children(output_options, include_attributes = True)
        result['disabled'] = ['', 'disabled="disabled"'][not self.get_active(self.path)]

        return """<span %(attr_html_attributes)s>
                   %(preview)s
                   <input type="file" name="%(attr_html_id)s" %(disabled)s id="%(attr_html_id)s-_-input" />
                   %(clear)s
                  </span>""" % result

class ToggleButton(Base.ValueInput, Button):
    """
    A toggle button is very similar to a checkbox button, except it is
    rendered as a normal button, and instantly cause a page-load when
    clicked, just as a Button.
    """

    true_title = 'True'
    false_title = 'False'
    value=False

    class HtmlClass(object):
        def __init__(self):
            self.value=""
        def __get__(self, instance, owner):
            return self.value + " " + ['toggle-false','toggle-true'][not not instance.value]
        def __set__(self, instance, value):
            self.value = value
    html_class = HtmlClass()

    class Title(object):
        def __get__(self, instance, owner):
            if instance.value:
                return instance.true_title
            return instance.false_title
    title = Title()

    def __init__(self,session,win_id,**attrs):
        setattr(type(self), 'html_class', self.HtmlClass())
        super(ToggleButton, self).__init__(session,win_id,**attrs)

    def field_input(self, path, string_value):
        if string_value != '':
            self.value = not self.value

    def field_output(self, path):
        return []

class FieldStorageInput(Base.ValueInput):
    value = None

    def field_input(self, path, string_value):
        if self.value is None:
            self.value = cgi.FieldStorage()
            self.value.filename = '%s file' % (self.mime_type,)
        if hasattr(self.value, 'original'):
            del self.value.original
        self.value.type = self.mime_type
        if self.value.file is None:
            self.value.file = self.value.make_file()
        self.value.file.seek(0)
        self.value.file.write(string_value.encode('utf-8'))
        self.value.file.truncate()
        self.value.file.seek(0)

    def field_output(self, path):
        res = ''
        if self.value is not None:
            self.value.file.seek(0)
            res = self.value.file.read().decode('utf-8')
        return [res]

