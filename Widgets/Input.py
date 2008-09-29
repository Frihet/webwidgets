#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moller@freecode.no>
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
        return '<input %(html_attributes)s type="hidden" name="%(name)s" value="%(value)s" %(disabled)s />' % {
            'html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'value': self.field_output(self.path)[0],
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}

class StringInput(Base.ValueInput):
    """Text input box"""
    rows = 1
    cols = None

    def draw(self, output_options):
        super(StringInput, self).draw(output_options)
	info = {'html_attributes': self.draw_html_attributes(self.path),
                'name': Webwidgets.Utils.path_to_id(self.path),
                'value': self.field_output(self.path)[0],
                'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)],
                'rows': self.rows,
                'cols': ['', 'cols="%s"' % self.cols][self.cols is not None],
                'size': ['', 'size="%s"' % self.cols][self.cols is not None]}

        if self.rows > 1:
            return '<textarea %(html_attributes)s rows="%(rows)s" %(cols)s name="%(name)s" %(disabled)s>%(value)s</textarea>' % info
        else:
            return '<input %(html_attributes)s %(size)s type="text" name="%(name)s" value="%(value)s" %(disabled)s />' % info

class IntegerInput(StringInput):
    error_string = "Integers must only contain the digits 0-9"
    original_value = None
    class WwModel(Base.ValueInput.WwModel):
        value = None
    def field_input(self, path, string_value):
        try:
            if string_value == '':
                self.value = None
            else:
                self.value = int(string_value)
        except ValueError, e:
            self.value = None
            self.error = self.error_string
                
    def field_output(self, path):
        if self.value is None:
            return ['']
        return [str(self.value)]

class FloatInput(StringInput):
    error_string = "Numbers must only contain the digits 0-9, period '.' and the exp. separator 'e'"
    original_value = None
    class WwModel(Base.ValueInput.WwModel):
        value = None
    def field_input(self, path, string_value):
        try:
            if string_value == '':
                self.ww_filter.value = None
            else:
                self.ww_filter.value = float(string_value)
        except ValueError, e:
            self.ww_filter.value = None
            self.ww_filter.error = self.error_string
                
    def field_output(self, path):
        if self.ww_filter.value is None:
            return ['']
        return [str(self.ww_filter.value)]

class PasswordInput(Base.ValueInput):
    """Like StringInput, but hides the user input"""
    def draw(self, output_options):
        super(PasswordInput, self).draw(output_options)

        return '<input %(html_attributes)s type="password" name="%(name)s" value="%(value)s" %(disabled)s />' % {
            'html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'value': self.field_output(self.path)[0],
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}

class NewPasswordInput(Formatting.Html, Base.ValueInput):
    """Used for entering new passwords - the password has to be
    repeated twice and the two values entered are compared. A
    value_changed is only propagated if the two values matches"""
    __wwml_html_override__ = False
    class WwModel(Base.ValueInput.WwModel):
        value = ''
    html = """
    <span %(html_attributes)s>
     %(input1)s
     %(input2)s
    </span>
    """

    msg_password_no_match = "Passwords don't match!"
    """Message displayed when passwords entered do not match."""

    def __init__(self, session, win_id, **attrs):
        Formatting.Html.__init__(
            self, session, win_id,
            **attrs)
        self.children['input1'] = self.Input(session, win_id, value=self.value)
        self.children['input2'] = self.Input(session, win_id, value=self.value)

    class Input(PasswordInput):
        ww_explicit_load = True
        html_autocomplete = "off"
        
        def value_changed(self, path, value):
            if self.parent['input1'].value == self.parent['input2'].value:
                self.parent.value = value
            else:
                self.parent.value = None
                self.parent.error = self._(msg_password_no_match)
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

class Button(Base.SingleActionInput):
    """Button widget - throws a "clicked" notification when clicked"""
    title = ''

    def draw(self, output_options):
        super(Button, self).draw(output_options)
        return '<input %(html_attributes)s type="submit" %(disabled)s name="%(name)s" value="%(title)s" />' % {
            'html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'title': self._(self.title, output_options),
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}

class UpdateButton(Base.SingleActionInput):
    """This is a special kind of button that only submits the form and
    causes other widgets to get their input. In addition, it
    dissapears if JavaScript is enabled. It is intended to be used in
    conjunction with register_submit_action() on other widgets."""

    def draw(self, output_options):
        Base.SingleActionInput.draw(self, output_options)
        info = {'html_attributes': self.draw_html_attributes(self.path),
                'id': Webwidgets.Utils.path_to_id(self.path),
                'title': self._("Update", output_options),
                'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}
        Base.HtmlWindow.register_script(self, 'update_button: %(id)s' % info,
                            """
                            webwidgets_add_event_handler(window, 'load',
                             'webwidgets_update_button: %(id)s',
                             function () {
                              document.getElementById('%(id)s').style.display = 'none';
                             });
                            """ % info)
        return '<input %(html_attributes)s type="submit" %(disabled)s name="%(id)s" value="%(title)s" />' % info

    def field_input(self, path, string_value):
        pass

class ButtonArray(Base.MultipleActionInput):
    """Button array widget - throws a "selected" notification when any one of the buttons is clicked"""

    pre = ''
    """HTML rendered before button array."""
    sep = ''
    """HTML rendered inbetween buttons."""
    post = ''
    """HTML rendered after button array."""
    buttons = {'Cancel': '0', 'Ok': '1'}
    "Mapping from button title to value."
    disabled_buttons = []
    "List of buttons that are disabled."

    def get_active_button(self, button):
        if button in self.disabled_buttons:
            return False
        else:
            return self.get_active(self.path + ['_', 'button', button])

    def draw(self, output_options):
        super(ButtonArray, self).draw(output_options)
        input_id = Webwidgets.Utils.path_to_id(self.path)
        buttons = ["""<button
                       type="submit"
                       %(disabled)s
                       name="%(name)s"
                       id="%(name)s-_-%(value)s"
                       value="%(value)s"
                       title="%(title)s"
                       >%(title)s</button>""" %
                   {'name': input_id,
                    'title': self._(title, output_options),
                    'value': value,
                    'disabled': ['', 'disabled="disabled"'][not self.get_active_button(value)]}
                   for title, value in self.ww_filter.buttons.iteritems()]
        return """<div %(html_attributes)s>%(pre)s%(buttons)s%(post)s</div>""" % {
            'html_attributes': self.draw_html_attributes(self.path),
            'buttons': self._(self.sep, output_options).join(buttons),
            'pre': self._(self.pre, output_options), 'post': self._(self.post, output_options)}

class RadioButtonGroup(Base.ValueInput):
    """Group of radio buttons must be joined together. This is
    performed by setting the 'group' attribute on each of the
    L{RadioInput} in the group to the same instance of this class."""

    #FIXME: What should original_value really be here? '' or None, or something else?
    
class RadioInput(Base.ValueInput, Base.StaticComposite):
    """A radio button (selection list item). You must create a
    L{RadioButtonGroup} instance and set the 'group' attribute to that
    instance so that all radio buttons in the group knows about each
    other."""

    def get_group(self):
        if isinstance(self.group, Base.Widget):
            return self.group
        return self + self.group

    def field_input(self, path, string_value):
        value = Webwidgets.Utils.id_to_path(string_value)
        if value == self.path:
            self.get_group().value = self.value

    def field_output(self, path):
        return [Webwidgets.Utils.path_to_id(self.path)]

    def draw(self, output_options):
        self.register_input(self.group.path, self.argument_name)
        result = self.draw_children(output_options, include_attributes = True)
        result['name'] = Webwidgets.Utils.path_to_id(self.group.path)
        result['value'] = result['id']
        result['checked'] = ['', 'checked'][self.value == self.get_group().value]
        result['disabled'] = ['', 'disabled="disabled"'][not self.get_active(self.path)],
        return """<input
                   %(ww_untranslated__html_attributes)s
                   type="radio"
                   name="%(name)s"
                   value="%(value)s"
                   %(checked)s
                   %(disabled)s
                  />""" % result

class Checkbox(Base.ValueInput):
    """Boolean input widget - it's value can either be true or false."""
    class WwModel(Base.ValueInput.WwModel):
        value = False
    def draw(self, output_options):
        super(Checkbox, self).draw(output_options)
        checked = ["", 'checked="checked"'][not not self.ww_filter.value]
        return '<input %(html_attributes)s type="checkbox" name="%(name)s" value="checked" %(checked)s %(disabled)s />' % {
            'html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'checked': checked,
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}

    def field_input(self, path, string_value):
        self.ww_filter.value = (string_value == "checked")

    def field_output(self, path):
        return [['', 'checked'][not not self.ww_filter.value]]

class ListInput(Base.ValueInput, Base.StaticComposite):
    """Scrollable list of selectable items. The list can optionally
    allow the user to select multiple items."""
    
    original_value = []

    class WwModel(Base.ValueInput.WwModel):
        value = []

        multiple = False
        """Allow the user to select multiple items."""

        size = 0
        """Size of the widget."""

    def draw(self, output_options):
        Base.ValueInput.draw(self, output_options)
        values = self.value
        if not isinstance(values, types.ListType):
            values = [values]
        options = '\n'.join([
            """<option %(selected)s value="%(value)s">
             %(description)s
            </option>""" % {'selected': child_name in values and 'selected="selected"' or '',
                           'value': child_name,
                           'description': child}
            for child_name, child
            in self.draw_children(output_options
                                  ).iteritems()])

        return """<select %(html_attributes)s %(multiple)s %(size)s name="%(name)s" %(disabled)s>
         %(options)s
         </select>""" % {
            'html_attributes': self.draw_html_attributes(self.path),
            'multiple': self.multiple and 'multiple' or '',
            'size': self.size != 0 and 'size="%s"' % self.size or '',
            'name': Webwidgets.Utils.path_to_id(self.path),
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)],
            'options': options
            }

class FileInput(Base.ValueInput, Base.StaticComposite):
    """File upload box"""
    original_value = None
    class WwModel(Base.ValueInput.WwModel):
        value = None
    
    def field_input(self, path, field_value):
        if path == self.path:
            if field_value != '':
                field_value.filename = field_value.filename.decode('utf-8')
                self.value = field_value
                
    def field_output(self, path):
        return [self.value]

    class Preview(Formatting.Media):
        class Content(object):
            def __get__(self, instance, owner):
                if instance is None or instance.parent is None:
                    return None
                return instance.parent.value
        content = Content()

    class Clear(Button):
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

        return """<span %(ww_untranslated__html_attributes)s>
                   %(Preview)s
                   <input type="file" name="%(ww_untranslated__html_id)s" %(disabled)s id="%(ww_untranslated__html_id)s-_-input" />
                   %(Clear)s
                  </span>""" % result

class ToggleButton(Base.ValueInput, Button):
    """
    A toggle button is very similar to a checkbox button, except it is
    rendered as a normal button, and instantly cause a page-load when
    clicked, just as a Button.
    """

    true_title = 'True'
    false_title = 'False'
    original_value = False
    class WwModel(Base.ValueInput.WwModel):
        value = False

    class HtmlClass(object):
        def __init__(self):
            self.value=""
        def __get__(self, instance, owner):
            if instance is None: return None
            return self.value + " " + ['toggle-false','toggle-true'][not not instance.value]
        def __set__(self, instance, value):
            self.value = value
    html_class = HtmlClass()

    class Title(object):
        def __get__(self, instance, owner):
            if instance is None: return None
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
    original_value = None
    class WwModel(Base.ValueInput.WwModel):
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

class NotificationError(Base.SingleActionInput):
    error = Exception("Example error")
    ww_bind_callback = "dont-require"
    

    def field_input(self, path, string_value):
        self.notify('raise_error')

    def field_output(self, path):
        return []

    def draw(self, output_options):
        super(NotificationError, self).draw(output_options)
        return '<input %(html_attributes)s type="hidden" name="%(name)s" value="cause-error" %(disabled)s />' % {
            'html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)]}

    def raise_error(self, path):
        raise self.error
