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

class Dialog(Formatting.Html):
    """Dialogs provides an easy way to let the user select one of a
    few different options, while providing the user with some longer
    explanation/description of the options. Options are described
    using a dictionary of description-value pairs."""
    __wwml_html_override__ = False
    buttons = {'Cancel': '0', 'Ok': '1'}
    html = """
    <div %(html_attributes)s>
     <div class="dialog-head" id="%(html_id)s-head">
      %(Head)s
     </div>
     <div class="dialog-body" id="%(html_id)s-body">
      %(Body)s
     </div>
     <div class="dialog-buttons" id="%(html_id)s-buttons">
      %(Buttons)s
     </div>
    </div>
    """

    class Buttons(Formatting.List):
        ww_explicit_load = True

        class Button(Input.Button):
            ww_explicit_load = True
            def clicked(self, path):
                self.parent.parent.notify('selected', self.value)
                raise StopIteration
            
        def __init__(self, session, win_id, buttons):
            super(Dialog.Buttons, self).__init__(
                session, win_id,
                children = Webwidgets.Utils.OrderedDict(
                    [(str(value),
                      Dialog.Buttons.Button(session, win_id,
                                            title=title, value=value))
                     for title, value in buttons.iteritems()]))
        
    def __init__(self, session, win_id, **attrs):
        super(Formatting.Html, self).__init__(
            session, win_id,
            children = {'Buttons': self.Buttons(session, win_id, self.buttons)},
            **attrs)

    def selected(self, path, value):
        if path != self.path: return
        self.visible = False

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

class TabbedView(Base.ActionInput, Tabset):
    """Provides a set of overlapping 'pages' with tabs, each tab
    holding some other widget, through wich a user can browse using
    the tabs."""
    argument_name = None
    old_page = None
    page = None

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

    def page_changed(self, path, page):
        """Notification that the user has changed page."""
        if path != self.path: return
        if self.old_page is not None:
            self.get_widget_by_path(self.old_page).notify('tab_blur')
        if self.page is not None:
            self.get_widget_by_path(self.page).notify('tab_focus')
        self.old_page = self.page

    def draw_tabs(self, output_options):
        active = self.register_input(self.path, self.argument_name)
        widget_id = Webwidgets.Utils.path_to_id(self.path)

        def draw_tabs(pages):
            tabs = []
            for name, (page, title, children) in pages.iteritems():
                info = {'disabled': ['', 'disabled="disabled"'][page == self.page or not active],
                        'html_id': widget_id,
                        'page': Webwidgets.Utils.path_to_id(page),
                        'caption': title}
                if children is None:
                    tabs.append("""
                                 <li><button
                                      type="submit"
                                      %(disabled)s
                                      id="%(html_id)s-_-%(page)s"
                                      name="%(html_id)s"
                                      value="%(page)s">%(caption)s</button></li>
                                """ % info)
                else:
                    info['children'] = draw_tabs(children)
                    tabs.append("<li><span>%(caption)s</span>%(children)s</li>" % info)
            return """
                    <ul id="%(widget_id)s" class="tabs">
                     %(tabs)s
                    </ul>
                   """ % {'widget_id': widget_id,
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
                      'page': self.draw_child(self.get_widget_by_path(self.page).path, self.get_widget_by_path(self.page), output_options, True),
                      'tabs': self.draw_tabs(output_options)}

class Hide(Base.StaticComposite):
    """
    A hide/show widget

    Change the value of the title variable to change the text in the button.

    TODO:
    Implement an alternative javascript implementation for faster update at the expense of longer reloads
    """

    class hideButton(Input.ToggleButton):
        true_title = "Hide"
        false_title = "Show"

    def draw(self, path):
        self['child'].visible = self['hideButton'].value
        children = self.draw_children(path, invisible_as_empty=True, include_attributes=True)
        return """<div %(html_attributes)s>%(hideButton)s %(child)s</div>""" % children
 
