#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

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
import Webwidgets.Utils, Webwidgets.Constants
import Base, Input, Formatting

class LanguageInput(Input.ListInput):
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

class InfoFrame(Base.StaticComposite):
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

    class Buttons(Input.ButtonArray):
        def selected(self, path, value):
            self.parent.notify('selected', value)
            raise StopIteration
        class Buttons(object):
            def __get__(self, instance, owner):
                if not instance.parent: return None
                return instance.parent.buttons

        buttons = Buttons()

class Dialog(StaticDialog):
    remove_on_close = False
    
    def close(self):
        if self.remove_on_close:
            del self.parent[self.name]
        else:
            self.visible = False

    def selected(self, path, value):
        if path != self.path: return
        self.close()

class Tabset(Base.StaticComposite):
    def get_pages(self, path = []):
        tabs = Webwidgets.Utils.OrderedDict()
        for name, child in self.get_children():
            #### fixme ####
            # name = "Child must be widget"
            # description = """If child is not a widget
            # but a string, this fails..."""
            #### end ####
            if not child.get_visible(child.path): continue

            page = path + [name]

            if isinstance(child, Tabset):
                tabs[name] = (page, child, child.get_pages(page))
            else:
                tabs[name] = (page, child, None)
        return tabs

    def draw_page_titles(self, output_options):
        def draw_page_titles(pages):
            if pages is None: return None
            res = Webwidgets.Utils.OrderedDict()
            for name, (page, widget, children) in pages.iteritems():
                res[name] = (page,
                             widget._(widget.get_title(widget.path), output_options),
                             draw_page_titles(children))
            return res
        return draw_page_titles(self.get_pages())

class SwitchingView(Tabset):
    """Provides a set of overlapping 'pages', of which only one is
    shown to the user at any given time, each holding some other
    widget."""
    old_page = None
    page = None

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

class TabbedView(SwitchingView, Base.ActionInput):
    """Provides a set of overlapping 'pages' with tabs, each tab
    holding some other widget, through wich a user can browse using
    the tabs."""
    argument_name = None

    def field_input(self, path, string_value):
        if string_value != '':
            self.page = Webwidgets.Utils.id_to_path(string_value, True)

    def field_output(self, path):
        return [unicode(Webwidgets.Utils.path_to_id(self.page, True))]

    def get_active(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        return self.active and self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, path)

    def draw_tabs(self, output_options):
        active = self.register_input(self.path, self.argument_name)
        widget_id = Webwidgets.Utils.path_to_id(self.path)

        def draw_tabs(pages, path = []):
            tabs = []
            for name, (page, title, children) in pages.iteritems():
                info = {'disabled': ['', 'disabled="disabled"'][page == self.page or not active],
                        'name': widget_id,
                        'html_id': Webwidgets.Utils.path_to_id(self.path + ['_', 'page'] + page),
                        'page': Webwidgets.Utils.path_to_id(page),
                        'caption': title}
                if children is None:
                    tabs.append("""
                                 <li><button
                                      type="submit"
                                      %(disabled)s
                                      id="%(html_id)s"
                                      name="%(name)s"
                                      value="%(page)s">%(caption)s</button></li>
                                """ % info)
                else:
                    info['children'] = draw_tabs(children, path + [name])
                    tabs.append("<li><span>%(caption)s</span>%(children)s</li>" % info)
            return """
                    <ul id="%(widget_id)s" class="tabs">
                     %(tabs)s
                    </ul>
                   """ % {'widget_id': Webwidgets.Utils.path_to_id(self.path + ['_', 'group'] + path),
                          'tabs': '\n'.join(tabs)}
        return draw_tabs(self.draw_page_titles(output_options))

    def draw(self, output_options):
        return """
               <div %(html_attributes)s>
                %(tabs)s
                <div class="page">
                 %(page)s
                </div>
               </div>
               """ % {'html_attributes': self.draw_html_attributes(self.path),
                      'page': super(TabbedView, self).draw(output_options),
                      'tabs': self.draw_tabs(output_options),
                      }

class Hide(Base.StaticComposite):
    """
    A hide/show widget

    Change the value of the title variable to change the text in the button.

    TODO:
    Implement an alternative javascript implementation for faster
    update at the expense of longer reloads
    """

    class HideButton(Input.ToggleButton):
        true_title = "Hide"
        false_title = "Show"

    def draw(self, path):
        self['Child'].visible = self['HideButton'].value
        children = self.draw_children(path, invisible_as_empty=True, include_attributes=True)
        return """<div %(html_attributes)s>%(HideButton)s %(Child)s</div>""" % children
 
