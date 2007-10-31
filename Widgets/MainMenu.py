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

import Webwidgets.Utils, Webwidgets.Constants
import Composite, Base

class MainMenu(Base.DirectoryServer, Composite.TabbedView):
    def draw_tabs(self, output_options):
        active = self.register_input(self.path, self.argument_name)
        widget_id = Webwidgets.Utils.path_to_id(self.path)

        def draw_tabs(pages):
            tabs = []
            for name, (page, title, children) in pages.iteritems():
                info = {'child_id': Webwidgets.Utils.path_to_id(page),
                        'child_name': '_'.join(['menu_bar'] + page),
                        'parent_name': '_'.join(['menu_bar'] + page[:-1]),
                        'caption': title}
                if children is None:
                    tabs.append("""
var %(child_name)s_item = new dhtmlXMenuItemObject("%(child_id)s","%(caption)s","");
menu_bar_menu.addItem(%(parent_name)s_menu,%(child_name)s_item);
""" % info)
                else:
                    tabs.append("""
var %(child_name)s_item = new dhtmlXMenuItemObject("%(child_id)s","%(caption)s","");
menu_bar_menu.addItem(%(parent_name)s_menu,%(child_name)s_item);
var %(child_name)s_menu = new dhtmlXMenuBarPanelObject(%(parent_name)s_menu,%(child_name)s_item,false,120,true);
""" % info)
                    tabs.extend(draw_tabs(children))
            return tabs

        return """
                <div id="%(widget_id)s-_-menu" class="menu"></div>
                %(noscript_version)s
                <input type="hidden" id="%(widget_id)s-_-value" name="%(widget_id)s" value="" />
                <script language="javascript">
function onButtonClick(itemId, itemValue) {
 document.getElementById("%(widget_id)s-_-value").value = itemId;
 document.getElementById("root-_-body-form").submit();
}
menu_bar_menu = new dhtmlXMenuBarObject('%(widget_id)s-_-menu','100%%',30,"%(title)s");
menu_bar_menu.setOnClickHandler(onButtonClick);
%(tabs)s

                </script>
               """ % {'noscript_version': Composite.TabbedView.draw_tabs(self, output_options),
                      'widget_id': widget_id,
                      'title': self._(self.title, output_options),
                      'tabs': '\n'.join(draw_tabs(self.draw_page_titles(output_options)))}
 
    def draw(self, output_options):
        self.register_style_link(self.calculate_url({'widget_class': 'Webwidgets.MainMenu',
                                                  'location': ['css/dhtmlXMenu.css']},
                                                 {}))
        self.register_script_link(self.calculate_url({'widget_class': 'Webwidgets.MainMenu',
                                                   'location': ['js', 'dhtmlXProtobar.js']},
                                                  {}))
        self.register_script_link(self.calculate_url({'widget_class': 'Webwidgets.MainMenu',
                                                   'location': ['js', 'dhtmlXMenuBar.js']},
                                                  {}))
        self.register_script_link(self.calculate_url({'widget_class': 'Webwidgets.MainMenu',
                                                   'location': ['js', 'dhtmlXCommon.js']},
                                                  {}))
        return Composite.TabbedView.draw(self, output_options)
