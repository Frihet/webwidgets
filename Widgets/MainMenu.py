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
    def drawTabs(self, outputOptions):
        active = self.registerInput(self.path, self.argumentName)
        widgetId = Webwidgets.Utils.pathToId(self.path)

        def drawTabs(pages):
            tabs = []
            for name, (page, title, children) in pages.iteritems():
                info = {'childId': Webwidgets.Utils.pathToId(page),
                        'childName': '_'.join(['menuBar'] + page),
                        'parentName': '_'.join(['menuBar'] + page[:-1]),
                        'caption': title}
                if children is None:
                    tabs.append("""
var %(childName)s_item = new dhtmlXMenuItemObject("%(childId)s","%(caption)s","");
menuBar_menu.addItem(%(parentName)s_menu,%(childName)s_item);
""" % info)
                else:
                    tabs.append("""
var %(childName)s_item = new dhtmlXMenuItemObject("%(childId)s","%(caption)s","");
menuBar_menu.addItem(%(parentName)s_menu,%(childName)s_item);
var %(childName)s_menu = new dhtmlXMenuBarPanelObject(%(parentName)s_menu,%(childName)s_item,false,120,true);
""" % info)
                    tabs.extend(drawTabs(children))
            return tabs

        return """
                <div id="%(widgetId)s-_-menu" />
                <input type="hidden" id="%(widgetId)s-_-value" name="%(widgetId)s" value="" />
                <script language="javascript">
function onButtonClick(itemId, itemValue) {
 document.getElementById("%(widgetId)s-_-value").value = itemId;
 document.getElementById("root-_-body-form").submit();
}
menuBar_menu = new dhtmlXMenuBarObject('%(widgetId)s-_-menu','100%%',30,"%(title)s");
menuBar_menu.setOnClickHandler(onButtonClick);
%(tabs)s

                </script>
               """ % {'widgetId': widgetId,
                      'title': self._(self.title, outputOptions),
                      'tabs': '\n'.join(drawTabs(self.drawPageTitles(outputOptions)))}
 
    def draw(self, outputOptions):
        self.registerStyleLink(self.calculateUrl({'widgetClass': 'Webwidgets.MainMenu',
                                                  'location': ['css/dhtmlXMenu.css']},
                                                 {}))
        self.registerScriptLink(self.calculateUrl({'widgetClass': 'Webwidgets.MainMenu',
                                                   'location': ['js', 'dhtmlXProtobar.js']},
                                                  {}))
        self.registerScriptLink(self.calculateUrl({'widgetClass': 'Webwidgets.MainMenu',
                                                   'location': ['js', 'dhtmlXMenuBar.js']},
                                                  {}))
        self.registerScriptLink(self.calculateUrl({'widgetClass': 'Webwidgets.MainMenu',
                                                   'location': ['js', 'dhtmlXCommon.js']},
                                                  {}))
        return Composite.TabbedView.draw(self, outputOptions)
