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

class StringInput(Base.ValueInput):
    """Text input box"""
    def draw(self, outputOptions):
        super(StringInput, self).draw(outputOptions)
        return '<input %(attr_htmlAttributes)s type="text" name="%(name)s" value="%(value)s" %(disabled)s />' % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'name': Webwidgets.Utils.pathToId(self.path),
            'value': self.fieldOutput(self.path)[0],
            'disabled': ['', 'disabled="true"'][not self.getActive(self.path)]}

class PasswordInput(Base.ValueInput):
    """Like StringInput, but hides the user input"""
    def draw(self, outputOptions):
        super(PasswordInput, self).draw(outputOptions)
        return '<input %(attr_htmlAttributes)s type="password" name="%(name)s" value="%(value)s" %(disabled)s />' % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'name': Webwidgets.Utils.pathToId(self.path),
            'value': self.fieldOutput(self.path)[0],
            'disabled': ['', 'disabled="true"'][not self.getActive(self.path)]}

class NewPasswordInput(Formatting.Html, Base.Input):
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
                self.parent.value = value
            else:
                self.parent.error = "Passwords don't match!"
            return True

        def getActive(self, path):
            return self.parent.getActive(path[:-1])

    def valueChanged(self, path, value):
        if path != self.path: return
        # If we get this from anywhere else that input1 and input2, we
        # must set their values too...
        self['input1'].value = self['input2'].value = self.value
        self.error = None

class Button(Base.Input):
    """Button widget - throws a "clicked" notification when clicked"""
    __attributes__ = Base.Input.__attributes__ + ('title',)
    title = ''

    def draw(self, outputOptions):
        super(Button, self).draw(outputOptions)
        return '<input %(attr_htmlAttributes)s type="submit" %(disabled)s name="%(name)s" value="%(title)s" />' % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'name': Webwidgets.Utils.pathToId(self.path),
            'title': self.title,
            'disabled': ['', 'disabled="true"'][not self.getActive(self.path)]}

    def fieldInput(self, path, stringValue):
        if stringValue != '':
            self.notify('clicked')

    def fieldOutput(self, path):
        return []

    def clicked(self, path):
        if path != self.path: return
        return

class RadioButtonGroup(Base.ValueInput):
    """Group of radio buttons must be joined together. This is
    performed by setting the 'group' attribute on each of the
    L{RadioInput} in the group to the same instance of this class."""
    
    def __init__(self, session, winId, *arg, **kw):
        Base.ValueInput.__init__(self, session, winId, *arg, **kw)
        self.members = {}

class RadioInput(Base.Input, Base.StaticComposite):
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
        result['disabled'] = ['', 'disabled="true"'][not self.getActive(self.path)],
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
        checked = ["", "checked='true'"][not not self.value]
        return '<input %(attr_htmlAttributes)s type="checkbox" name="%(name)s" value="checked" %(checked)s %(disabled)s />' % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'name': Webwidgets.Utils.pathToId(self.path),
            'checked': checked,
            'disabled': ['', 'disabled="true"'][not self.getActive(self.path)]}

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
            </option>""" % {'selected': childname in values and 'selected' or '',
                           'value': childname,
                           'description': children[childname]}
            for childname
            in childnames])

        return """<select %(attr_htmlAttributes)s %(multiple)s %(size)s name="%(name)s" %(disabled)s">
         %(options)s
         </select>""" % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'multiple': self.multiple and 'multiple' or '',
            'size': self.size != 0 and 'size="%s"' % self.size or '',
            'name': Webwidgets.Utils.pathToId(self.path),
            'disabled': ['', 'disabled="true"'][not self.getActive(self.path)],
            'options': options
            }


class FileInput(Base.ValueInput, Base.StaticComposite):
    """File upload box"""
    value = None
    
    def fieldInput(self, path, fieldValue):
        if path == self.path:
            if fieldValue != '':
                self.value = fieldValue
        elif path == self.path + ['_', 'clear']:
            if fieldValue != '':
                self.value = None
                
    def fieldOutput(self, path):
        return [self.value]

    class preview(Formatting.Media):
        def getContent(self, path):
            return self.parent.value
        
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
        return """<span %(attr_htmlAttributes)s>
                   %(current)s
                   <input type="file" name="%(attr_html_id)s" %(disabled)s id="%(attr_html_id)s" />
                   <input type='submit' name="%(clearId)s" %(clearable)s id="%(clearId)s" value="Clear" />
                  </span>""" % {
                       'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
                       'current': self.drawChild(self.path + ['preview'], self['preview'], outputOptions, True),
                       'disabled': ['', 'disabled="true"'][not self.getActive(self.path)],
                       'clearable': ['', 'disabled="true"'][not self.getActive(self.path) or self.value is None],
                       'attr_html_id': Webwidgets.Utils.pathToId(self.path),
                       'clearId': Webwidgets.Utils.pathToId(self.path + ['_', 'clear'])}
