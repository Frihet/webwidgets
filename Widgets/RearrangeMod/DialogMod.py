#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 Egil Moeller <redhog@redhog.org>
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

import types
import Webwidgets.Utils
import Webwidgets.Constants
import Webwidgets.Widgets.Base
import Webwidgets.Widgets.WindowMod
import Webwidgets.Widgets.InputMod.BaseInput
import Webwidgets.Widgets.FormattingMod.BaseFormatting

class InfoFrame(Webwidgets.Widgets.Base.StaticComposite):
    def draw_head(self, children, output_options):
        if 'Head' not in children:
            children['Head'] = children['Body'].title
        return """<div class="%(html_head_classes)s" id="%(ww_untranslated__html_id)s-head">
                   %(Head)s
                  </div>""" % children

    def draw_body(self, children, output_options):
        return """<div class="%(html_body_classes)s" id="%(ww_untranslated__html_id)s-body">
                   %(Body)s
                  </div>""" % children

    def draw_foot(self, children, output_options):
        return ""

    def draw(self, output_options):
        children = self.draw_children(
            output_options,
            invisible_as_empty = True,
            include_attributes = True)
        children['html_head_classes'] = Webwidgets.Utils.classes_to_css_classes(self.ww_classes, ['head'])
        children['html_body_classes'] = Webwidgets.Utils.classes_to_css_classes(self.ww_classes, ['body'])
        children['html_foot_classes'] = Webwidgets.Utils.classes_to_css_classes(self.ww_classes, ['foot'])
        children['head'] = self.draw_head(children, output_options)
        children['body'] = self.draw_body(children, output_options)
        children['foot'] = self.draw_foot(children, output_options)

        return """
    <div %(html_attributes)s>
     %(head)s
     %(body)s
     %(foot)s
    </div>
    """ % children

class StaticDialog(InfoFrame):
    """Dialogs provides an easy way to let the user select one of a
    few different options, while providing the user with some longer
    explanation/description of the options. Options are described
    using a dictionary of description-value pairs."""
    __wwml_html_override__ = False
    buttons = {'Cancel': '0', 'Ok': '1'}

    def draw_foot(self, children, output_options):
        return """<div class="%(html_foot_classes)s" id="%(ww_untranslated__html_id)s-foot">
                   %(Buttons)s
                  </div>""" % children

    class Buttons(Webwidgets.Widgets.InputMod.BaseInput.ButtonArray):
        def selected(self, path, value):
            self.parent.notify('selected', value)
            raise StopIteration
        class Buttons(object):
            def __get__(self, instance, owner):
                if not instance.parent: return None
                return instance.parent.buttons

        buttons = Buttons()

class AbstractDialog(StaticDialog, Webwidgets.Widgets.Base.DirectoryServer):
    remove_on_close = False

    def draw(self, output_options):
        Webwidgets.Widgets.WindowMod.HtmlWindow.register_script_link(
            self, 
            self.calculate_url_to_directory_server(
                'Webwidgets.Dialog',
                ['Dialog','dialog_iefix.js'],
                output_options))
        return StaticDialog.draw(self, output_options)

    def close(self):
        if self.remove_on_close:
            del self.parent[self.name]
        else:
            self.visible = False

    def selected(self, path, value):
        if path != self.path: return
        self.close()

class Dialog(AbstractDialog):
    pass

class AbstractInfoDialog(AbstractDialog):
    pass

class InfoDialog(AbstractInfoDialog):
    buttons = {'Ok': '1'}

class ConfirmationDialog(AbstractInfoDialog):
    class Head(Webwidgets.Widgets.FormattingMod.BaseFormatting.Html):
        html = """Really perform action?"""
    class Body(Webwidgets.Widgets.FormattingMod.BaseFormatting.Html):
        html = """Do you really want to perform this action?"""

class DisableConfirmationDialog(ConfirmationDialog):
    class Head(Webwidgets.Widgets.FormattingMod.BaseFormatting.Html):
        html = """Really disable this item?"""
    class Body(Webwidgets.Widgets.FormattingMod.BaseFormatting.Html):
        html = """Do you really want to disable this item?"""

class DeleteConfirmationDialog(ConfirmationDialog):
    class Head(Webwidgets.Widgets.FormattingMod.BaseFormatting.Html):
        html = """Really delete this item?"""
    class Body(Webwidgets.Widgets.FormattingMod.BaseFormatting.Html):
        html = """Do you really want to delete this item?"""

class DialogContainer(Webwidgets.Widgets.FormattingMod.BaseFormatting.Div):
    is_dialog_container = True

    __wwml_html_override__ = False
    html = "%(Dialogs)s%(Body)s"
    class Dialogs(Webwidgets.Widgets.FormattingMod.BaseFormatting.ReplacedList): pass
    class Body(Webwidgets.Widgets.FormattingMod.BaseFormatting.Html): pass

    def add_dialog(self, dialog, name = None):
        if name is None: name = str(len(self['Dialogs'].children))
        self['Dialogs'][name] = dialog
        dialog.remove_on_close = True

    def add_dialog_to_nearest(cls, widget, dialog, name = None):
        widget.get_ansestor_by_attribute(
            "is_dialog_container", True
            ).add_dialog(dialog, name)
    add_dialog_to_nearest = classmethod(add_dialog_to_nearest)

class Hide(Webwidgets.Widgets.Base.StaticComposite):
    """
    A hide/show widget

    Change the value of the title variable to change the text in the button.

    TODO:
    Implement an alternative javascript implementation for faster
    update at the expense of longer reloads
    """

    class HideButton(Webwidgets.Widgets.InputMod.BaseInput.ToggleButton):
        true_title = "Hide"
        false_title = "Show"

    def draw(self, path):
        self['Child'].visible = self['HideButton'].value
        children = self.draw_children(path, invisible_as_empty=True, include_attributes=True)
        return """<div %(html_attributes)s>%(HideButton)s %(Child)s</div>""" % children
 
