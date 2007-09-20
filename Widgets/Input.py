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

import types
import Webwidgets.Utils, Webwidgets.Constants
import Base, Formatting

class ArgumentInput(Base.ValueInput):
    """This input widget does not actually renders into any HTML but
    instead represents a parameter in the URL. L{argumentName} is
    mandatory for this widget to be usefull.

    Special note: The two special URL argument names '__location__'
    and '__extra__' represents any extra path in URL and any argments
    not named by any other input field, respectively.

    As those two fields have to be defined, L{Window} defines two
    children that are subclasses of this class for this purpose. If
    you need to implement these two widgets somwhere else in the
    widget tree, you must replace those two widgets with something
    else, e.g. the empty string.
    """
    
    def draw(self, outputOptions):
        self.registerInput(self.path, self.argumentName, False)
        return ''

class HiddenInput(Base.ValueInput):
    """Hidden input box. Note that this is only usefull to communicate
    with some JavaScript."""
    def draw(self, outputOptions):
        super(HiddenInput, self).draw(outputOptions)
        return '<input %(attr_htmlAttributes)s type="hidden" name="%(name)s" value="%(value)s" %(disabled)s />' % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'name': Webwidgets.Utils.pathToId(self.path),
            'value': self.fieldOutput(self.path)[0],
            'disabled': ['', 'disabled="disabled"'][not self.getActive(self.path)]}

class StringInput(Base.ValueInput):
    """Text input box"""
    __attributes__ = Base.ValueInput.__attributes__ + ('rows', 'cols')
    rows = 1
    cols = None

    def draw(self, outputOptions):
        super(StringInput, self).draw(outputOptions)
	info = {'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
                'name': Webwidgets.Utils.pathToId(self.path),
                'value': self.fieldOutput(self.path)[0],
                'disabled': ['', 'disabled="disabled"'][not self.getActive(self.path)],
                'rows': self.rows,
                'cols': ['', 'cols="%s"' % self.cols][self.cols is not None],
                'size': ['', 'size="%s"' % self.cols][self.cols is not None]}

        if self.rows > 1:
            return '<textarea %(attr_htmlAttributes)s rows="%(rows)s" %(cols)s name="%(name)s" %(disabled)s>%(value)s</textarea>' % info
        else:
            return '<input %(attr_htmlAttributes)s %(size)s type="text" name="%(name)s" value="%(value)s" %(disabled)s />' % info

class PasswordInput(Base.ValueInput):
    """Like StringInput, but hides the user input"""
    def draw(self, outputOptions):
        super(PasswordInput, self).draw(outputOptions)
        return '<input %(attr_htmlAttributes)s type="password" name="%(name)s" value="%(value)s" %(disabled)s />' % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'name': Webwidgets.Utils.pathToId(self.path),
            'value': self.fieldOutput(self.path)[0],
            'disabled': ['', 'disabled="disabled"'][not self.getActive(self.path)]}

class NewPasswordInput(Formatting.Html, Base.ValueInput):
    """Used for entering new passwords - the password has to be
    repeated twice and the two values entered are compared. A
    valueChanged is only propagated if the two values matches"""
    __wwml_html_override__ = False
    __attributes__ = Formatting.Html.__attributes__ + ('value',)
    value = ''
    html = """
    <span %(attr_htmlAttributes)s>
     %(input1)s
     %(input2)s
    </span>
    """
    def __init__(self, session, winId, **attrs):
        Formatting.Html.__init__(
            self, session, winId,
            **attrs)
        self.children['input1'] = self.Input(session, winId, value=self.value)
        self.children['input2'] = self.Input(session, winId, value=self.value)

    class Input(PasswordInput):
        __explicit_load__ = True
        
        def valueChanged(self, path, value):
            if self.parent['input1'].value == self.parent['input2'].value:
                print "Passwords matches", self.parent['input1'].value, self.parent['input2'].value
                self.parent.value = value
            else:
                self.parent.value = None
                self.parent.error = "Passwords don't match!"
            return True

        def getActive(self, path):
            return self.parent.getActive(path[:-1])

    def valueChanged(self, path, value):
        if path != self.path: return
        if value is None: return
        # If we get this from anywhere else than input1 and input2, we
        # must set their values too...
        self['input1'].value = self['input2'].value = self.value
        self.error = None

class Button(Base.ActionInput):
    """Button widget - throws a "clicked" notification when clicked"""
    __attributes__ = Base.ActionInput.__attributes__ + ('title',)
    title = ''

    def draw(self, outputOptions):
        super(Button, self).draw(outputOptions)
        return '<input %(attr_htmlAttributes)s type="submit" %(disabled)s name="%(name)s" value="%(title)s" />' % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'name': Webwidgets.Utils.pathToId(self.path),
            'title': self.title,
            'disabled': ['', 'disabled="disabled"'][not self.getActive(self.path)]}

class UpdateButton(Base.ActionInput):
    """This is a special kind of button that only submits the form and
    causes other widgets to get their input. In addition, it
    dissapears if JavaScript is enabled. It is intended to be used in
    conjunction with registerSubmitAction() on other widgets."""

    def draw(self, outputOptions):
        Base.ActionInput.draw(self, outputOptions)
        info = {'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
                'id': Webwidgets.Utils.pathToId(self.path),
                'title': self.title,
                'disabled': ['', 'disabled="disabled"'][not self.getActive(self.path)]}
        self.registerScript('updateButton: %(id)s' % info,
                            """
                            webwidgets_add_event_handler(window, 'load',
                             'webwidgets_update_button: %(id)s',
                             function () {
                              document.getElementById('%(id)s').style.display = 'none';
                             });
                            """ % info)
        return '<input %(attr_htmlAttributes)s type="submit" %(disabled)s name="%(id)s" value="Update" />' % info

    def fieldInput(self, path, stringValue):
        pass

class RadioButtonGroup(Base.ValueInput):
    """Group of radio buttons must be joined together. This is
    performed by setting the 'group' attribute on each of the
    L{RadioInput} in the group to the same instance of this class."""
    
    def __init__(self, session, winId, *arg, **kw):
        Base.ValueInput.__init__(self, session, winId, *arg, **kw)
        self.members = {}

class RadioInput(Base.ValueInput, Base.StaticComposite):
    """A radio button (selection list item). You must create a
    L{RadioButtonGroup} instance and set the 'group' attribute to that
    instance so that all radio buttons in the group knows about each
    other."""
    __attributes__ = Base.StaticComposite.__attributes__ + ('group', 'title', 'value', 'default')
    def __init__(self, session, winId, **attrs):
        Base.StaticComposite.__init__(self, session, winId, **attrs)
        self.group.members[self.value] = self
        if self.default:
            self.group.value = self.value

    def fieldInput(self, path, stringValue):
        value = Utils.idToPath(stringValue)
        if value == path:
            self.group.value = self.value

    def fieldOutput(self, path):
        return [Utils.pathToId(self.group.members[self.group.value].path)]

    def draw(self, outputOptions):
        self.registerInput(self.group.path, self.argumentName)
        result = self.drawChildren(outputOptions, includeAttributes = True)
        result['name'] = Webwidgets.Utils.pathToId(self.group.path)
        result['value'] = result['id']
        result['checked'] = ['', 'checked'][self.value == self.group.value]
        result['disabled'] = ['', 'disabled="disabled"'][not self.getActive(self.path)],
        return """<input
                   %(attr_htmlAttributes)s
                   type="radio"
                   name="%(name)s"
                   value="%(value)s"
                   %(checked)s
                   %(disabled)s
                  >%(title)s</input>""" % result

class Checkbox(Base.ValueInput):
    """Boolean input widget - it's value can either be true or false."""
    value = False
    def draw(self, outputOptions):
        super(Checkbox, self).draw(outputOptions)
        checked = ["", 'checked="checked"'][not not self.value]
        return '<input %(attr_htmlAttributes)s type="checkbox" name="%(name)s" value="checked" %(checked)s %(disabled)s />' % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'name': Webwidgets.Utils.pathToId(self.path),
            'checked': checked,
            'disabled': ['', 'disabled="disabled"'][not self.getActive(self.path)]}

    def fieldInput(self, path, stringValue):
        self.value = (stringValue == "checked")

    def fieldOutput(self, path):
        return [['', 'checked'][not not self.value]]

class ListInput(Base.ValueInput, Base.StaticComposite):
    """Scrollable list of selectable items. The list can optionally
    allow the user to select multiple items."""
    
    __attributes__ = Base.ValueInput.__attributes__ + ('multiple', 'size')
    multiple = False
    """Allow the user to select multiple items."""
    
    size = 0
    """Size of the widget."""
    
    value = []

    def draw(self, outputOptions):
        Base.ValueInput.draw(self, outputOptions)
        children = self.drawChildren(outputOptions)
        childnames = children.keys()
        childnames.sort()
        values = self.value
        if not isinstance(values, types.ListType):
            values = [values]
        options = '\n'.join([
            """<option %(selected)s value="%(value)s">
             %(description)s
            </option>""" % {'selected': childname in values and 'selected="selected"' or '',
                           'value': childname,
                           'description': children[childname]}
            for childname
            in childnames])

        return """<select %(attr_htmlAttributes)s %(multiple)s %(size)s name="%(name)s" %(disabled)s>
         %(options)s
         </select>""" % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'multiple': self.multiple and 'multiple' or '',
            'size': self.size != 0 and 'size="%s"' % self.size or '',
            'name': Webwidgets.Utils.pathToId(self.path),
            'disabled': ['', 'disabled="disabled"'][not self.getActive(self.path)],
            'options': options
            }


class FileInput(Base.ValueInput, Base.StaticComposite):
    """File upload box"""
    value = None
    
    def fieldInput(self, path, fieldValue):
        if path == self.path:
            if fieldValue != '':
                self.value = fieldValue
                
    def fieldOutput(self, path):
        return [self.value]

    class preview(Formatting.Media):
        class Content(object):
            def __get__(self, instance, owner):
                if not hasattr(instance, 'parent'):
                    return None
                return instance.parent.value
        content = Content()

    class clear(Button):
        title = 'Clear'
        def clicked(self, path):
            self.parent.value = None
        def getActive(self, path):
            return self.parent.getActive(path[:-1]) and self.parent.value != None
        
    def output(self, outputOptions):
        res = {Webwidgets.Constants.OUTPUT: self.value.file.read(),
               'Content-type': value.type
               }
        value.file.seek(0)
        return res

    def draw(self, outputOptions):
        super(FileInput, self).draw(outputOptions)
        if self.getActive(self.path):
            self.registerInput(self.path, self.argumentName)
            if self.value is not None:
                argumentName = self.argumentName
                if argumentName: argumentName = argumentName + '_clear'
                self.registerInput(self.path + ['_', 'clear'], argumentName)

        result = self.drawChildren(outputOptions, includeAttributes = True)
        result['disabled'] = ['', 'disabled="disabled"'][not self.getActive(self.path)],
        result['clearable'] = ['', 'disabled="disabled"'][not self.getActive(self.path) or self.value is None],

        return """<span %(attr_htmlAttributes)s>
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

    value=False

    class HtmlClass(object):
        def __init__(self):
            self.value=""
        def __get__(self, instance, owner):
            return self.value + " " + ['toggle-invisible','toggle-visible'][instance.value]
        def __set__(self, instance, value):
            self.value = value
    html_class = HtmlClass()

    def __init__(self,session,winId,**attrs):
        setattr(type(self), 'html_class', self.HtmlClass())
        super(ToggleButton, self).__init__(session,winId,**attrs)

    def fieldInput(self, path, stringValue):
        if stringValue != '':
            self.value = not self.value

    def fieldOutput(self, path):
        return []
