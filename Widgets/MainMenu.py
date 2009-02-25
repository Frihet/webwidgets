#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 Egil Moeller <redhog@redhog.org>

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

"""Application menu
"""

import Webwidgets.Utils
import Webwidgets.Constants
import Webwidgets.Widgets.Composite
import Webwidgets.Widgets.Base
import Webwidgets.Widgets.WindowMod

class MainMenu(Webwidgets.Widgets.Base.DirectoryServer, Webwidgets.Widgets.Composite.TabbedView):
    def draw_tab_entry(self, child_widget, info, output_options):
        if output_options.get('MainMenu.noscript_version', False):
            return Webwidgets.Widgets.Composite.TabbedView.draw_tab_entry(self, child_widget, info, output_options)
        if info['children'] is None:
            return ["""
var %(child_name)s_item = new dhtmlXMenuItemObject("%(child_id)s","%(caption)s","");
menu_bar_menu.addItem(%(parent_name)s_menu,%(child_name)s_item);
""" % info]
        else:
            return ["""
var %(child_name)s_item = new dhtmlXMenuItemObject("%(child_id)s","%(caption)s","");
menu_bar_menu.addItem(%(parent_name)s_menu,%(child_name)s_item);
var %(child_name)s_menu = new dhtmlXMenuBarPanelObject(%(parent_name)s_menu,%(child_name)s_item,false,120,true);
%(children)s
""" % info]
            
    def draw_tabs_tablist(self, widget, tabs, output_options):
        if output_options.get('MainMenu.noscript_version', False):
            return Webwidgets.Widgets.Composite.TabbedView.draw_tabs_tablist(self, widget, tabs, output_options)
        return '\n'.join(tabs)

    def draw_tabs_container(self, widget_id, tabs, output_options):
        if output_options.get('MainMenu.noscript_version', False):
            return Webwidgets.Widgets.Composite.TabbedView.draw_tabs_container(self, widget_id, tabs, output_options)
        return """
                <div id="%(widget_id)s-_-menu" class="menu"></div>
                %(noscript_version)s
                <input type="hidden" id="%(widget_id)s-_-value" name="%(widget_id)s" value="" />
                <script language="javascript">
function onButtonClick(itemId, itemValue) {
 document.getElementById("%(widget_id)s-_-value").value = itemId;
 document.getElementById("root:_-body-form").submit();
}
menu_bar_menu = new dhtmlXMenuBarObject('%(widget_id)s-_-menu','100%%',30,"%(title)s");
menu_bar_menu.setOnClickHandler(onButtonClick);
%(tabs)s

                </script>
               """ % {'noscript_version': Webwidgets.Widgets.Composite.TabbedView.draw_tabs(self, Webwidgets.Utils.subclass_dict(output_options, {'MainMenu.noscript_version': True})),
                      'widget_id': widget_id,
                      'title': self._(self.title, output_options),
                      'tabs': tabs}

    def draw(self, output_options):
        def calculate_url(location):
            return self.calculate_url_to_directory_server('Webwidgets.MainMenu', location, output_options)
        Webwidgets.Widgets.WindowMod.HtmlWindow.register_style_link(self, calculate_url(['css', 'dhtmlXMenu.css']))
        Webwidgets.Widgets.WindowMod.HtmlWindow.register_script_link(self, calculate_url(['js', 'dhtmlXProtobar.js']))
        Webwidgets.Widgets.WindowMod.HtmlWindow.register_script_link(self, calculate_url(['js', 'dhtmlXMenuBar.js']))
        Webwidgets.Widgets.WindowMod.HtmlWindow.register_script_link(self, calculate_url(['js', 'dhtmlXCommon.js']))
        return Webwidgets.Widgets.Composite.TabbedView.draw(self, Webwidgets.Utils.subclass_dict(output_options, {'MainMenu.noscript_version': False}))
