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
import Webwidgets.Widgets.BaseInput
import Webwidgets.Widgets.Formatting

class LanguageInput(Webwidgets.Widgets.BaseInput.ListInput):
    languages = {'en':u'English', 'sv':u'Svenska', 'no':u'Norsk'}
    
    def get_children(self):
        return self.languages.iteritems()

class LanguageSelector(LanguageInput):
    class Value(object):
        def __get__(self, instance, owner):
            if not hasattr(instance, 'session'):
                return None
            if instance.session.languages is None:
                return instance.get_languages({})[0]
            return instance.session.languages[0]
        def __set__(self, instance, value):
            instance.session.languages = (value,)
    value = Value()

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

    class Buttons(Webwidgets.Widgets.BaseInput.ButtonArray):
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
    class Head(Webwidgets.Widgets.Formatting.Html):
        html = """Really perform action?"""
    class Body(Webwidgets.Widgets.Formatting.Html):
        html = """Do you really want to perform this action?"""

class DisableConfirmationDialog(ConfirmationDialog):
    class Head(Webwidgets.Widgets.Formatting.Html):
        html = """Really disable this item?"""
    class Body(Webwidgets.Widgets.Formatting.Html):
        html = """Do you really want to disable this item?"""

class DeleteConfirmationDialog(ConfirmationDialog):
    class Head(Webwidgets.Widgets.Formatting.Html):
        html = """Really delete this item?"""
    class Body(Webwidgets.Widgets.Formatting.Html):
        html = """Do you really want to delete this item?"""

class DialogContainer(Webwidgets.Widgets.Formatting.Div):
    is_dialog_container = True

    __wwml_html_override__ = False
    html = "%(Dialogs)s%(Body)s"
    class Dialogs(Webwidgets.Widgets.Formatting.ReplacedList): pass
    class Body(Webwidgets.Widgets.Formatting.Html): pass

    def add_dialog(self, dialog, name = None):
        if name is None: name = str(len(self['Dialogs'].children))
        self['Dialogs'][name] = dialog
        dialog.remove_on_close = True

    def add_dialog_to_nearest(cls, widget, dialog, name = None):
        widget.get_ansestor_by_attribute(
            "is_dialog_container", True
            ).add_dialog(dialog, name)
    add_dialog_to_nearest = classmethod(add_dialog_to_nearest)

class Tabset(Webwidgets.Widgets.Base.StaticComposite):
    def get_pages(self, output_options):
        nr_of_descendants = 0
        tabs = Webwidgets.Utils.OrderedDict()
        for name, child in self.get_children():
            #### fixme ####
            # name = "Child must be widget"
            # description = """If child is not a widget
            # but a string, this fails..."""
            #### end ####
            if not child.get_visible(child.path): continue

            child_nr_of_descendants = 1
            child_pages = []

            if isinstance(child, Tabset):
                child_pages, child_nr_of_descendants = child.get_pages(output_options)
            
            tabs[name] = (child._(child.get_title(child.path), output_options),
                          child,
                          child_pages,
                          child_nr_of_descendants)            
            nr_of_descendants += child_nr_of_descendants
            
        return tabs, nr_of_descendants

class SwitchingView(Tabset):
    """Provides a set of overlapping 'pages', of which only one is
    shown to the user at any given time, each holding some other
    widget."""
    old_page = None
    page = None

    def __init__(self, session, win_id, *attrs):
        super(SwitchingView, self).__init__(session, win_id, *attrs)
        self.old_page = self.page

    def page_changed(self, path, page):
        """Notification that the user has changed page."""
        if path != self.path: return
        if self.old_page is not None:
            self.get_widget_by_path(self.old_page).notify('tab_blur')
        if self.page is not None:
            self.get_widget_by_path(self.page).notify('tab_focus')
        self.old_page = self.page

    def draw(self, output_options):
        return self.draw_child(self.get_widget_by_path(self.page).path,
                               self.get_widget_by_path(self.page),
                               output_options,
                               True)

class TabbedView(SwitchingView, Webwidgets.Widgets.Base.ActionInput):
    """Provides a set of overlapping 'pages' with tabs, each tab
    holding some other widget, through wich a user can browse using
    the tabs.

    It is possible to embed a widget in the menu itself by setting the
    attribute draw_inline=True on the child widget."""
    argument_name = None

    hide_single_tab = True
    """Hide the tab-header if there is only one tab (visible)."""

    def field_input(self, path, string_value):
        if string_value != '':
            page = Webwidgets.Utils.id_to_path(string_value)
            if self.get_active_page(page):
                self.page = page

    def field_output(self, path):
        return ['']

    def get_active_page(self, page):
        return getattr(self + page, 'active', True) and self.session.AccessManager(
            Webwidgets.Constants.RARR, self.win_id, self.path + page)
        
    def get_active_page_preview(self, page):
        return getattr(self + page, 'active', True) and self.session.AccessManager(
            Webwidgets.Constants.RARR, self.win_id, self.path + page)
        
    def get_active(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        return self.active and self.session.AccessManager(Webwidgets.Constants.RARR, self.win_id, path)

    def draw_tab_entry(self, child_widget, info, output_options):
        tabs = []
        # FIXME: Maybe put id= on the li, not the button would make more sense?
        if info['children'] is None:
            if getattr(child_widget, 'draw_inline', False):
                html = self.draw_child(child_widget.path, child_widget, output_options)
                if html is not None:
                    tabs.append("<li>%s</li>" % (html, ))
            else:
                tabs.append("""
                         <li><button
                              type="submit"
                              class="%(class)s"
                              %(disabled)s
                              id="%(html_id)s"
                              name="%(name)s"
                              title="%(caption)s"
                              value="%(page)s">%(caption)s</button></li>
                        """ % info)
        else:
            tabs.append("<li><span>%(caption)s</span>%(children)s</li>" % info)
        return tabs

    def draw_tabs_tablist(self, widget, tabs, output_options):
        return """
                <ul id="%(widget_id)s" class="tabs">
                 %(tabs)s
                </ul>
               """ % {'widget_id': Webwidgets.Utils.path_to_id(self.path + ['_', 'group'] + widget.path[len(self.path):]),
                      'tabs': '\n'.join(tabs)}

    def draw_tabs_recurse(self, active, widget_id, widget, pages, nr_of_descendants, output_options):
        tabs = []
        for name, (title, child_widget, child_pages, child_nr_of_descendants) in pages.iteritems():
            page = child_widget.path[len(self.path):]
            page_is_active = (   not active
                              or not self.get_active_page_preview(page))
               
            clss = []
            if page == self.page:
                clss.append('ww-selected')
            if page_is_active:
                clss.append('ww-disabled')
            info = {'class': ' '.join(clss),
                    'disabled': ['', 'disabled="disabled"'][    page_is_active
                                                            and not page == self.page],
                    'name': widget_id,
                    'child_id': Webwidgets.Utils.path_to_id(page),
                    'child_name': '_'.join(['menu_bar'] + page),
                    'parent_name': '_'.join(['menu_bar'] + page[:-1]),
                    'html_id': Webwidgets.Utils.path_to_id(self.path + ['_', 'page'] + page),
                    'page': Webwidgets.Utils.path_to_id(page),
                    'caption': title,
                    'children': None}

            if child_pages:
                info['children'] = self.draw_tabs_recurse(active, widget_id, child_widget, child_pages, child_nr_of_descendants, output_options)
                
            tabs.extend(self.draw_tab_entry(child_widget, info, output_options))

        return self.draw_tabs_tablist(widget, tabs, output_options)

    def draw_tabs_container(self, widget_id, tabs, output_options):
        return tabs

    def draw_tabs(self, output_options):
        active = self.register_input(self.path, self.argument_name)
        widget_id = Webwidgets.Utils.path_to_id(self.path)
        pages, nr_of_descendants = self.get_pages(output_options)

        if nr_of_descendants < 2 and self.hide_single_tab:
            return ''

        return self.draw_tabs_container(
            widget_id,
            self.draw_tabs_recurse(active, widget_id, self, pages, nr_of_descendants, output_options),
            output_options)

    def draw(self, output_options):
        return """
               <div %(html_attributes)s>
                %(tabs)s
                <div class="%(html_classes_for_page)s">
                 %(page)s
                </div>
               </div>
               """ % {'html_attributes': self.draw_html_attributes(self.path),
                      'page': super(TabbedView, self).draw(output_options),
                      'tabs': self.draw_tabs(output_options),
                      'html_classes_for_page': Webwidgets.Utils.classes_to_css_classes(
                          Webwidgets.Utils.classes_remove_bases(self.ww_classes, TabbedView), ['page'])
                      }

class Hide(Webwidgets.Widgets.Base.StaticComposite):
    """
    A hide/show widget

    Change the value of the title variable to change the text in the button.

    TODO:
    Implement an alternative javascript implementation for faster
    update at the expense of longer reloads
    """

    class HideButton(Webwidgets.Widgets.BaseInput.ToggleButton):
        true_title = "Hide"
        false_title = "Show"

    def draw(self, path):
        self['Child'].visible = self['HideButton'].value
        children = self.draw_children(path, invisible_as_empty=True, include_attributes=True)
        return """<div %(html_attributes)s>%(HideButton)s %(Child)s</div>""" % children
 
