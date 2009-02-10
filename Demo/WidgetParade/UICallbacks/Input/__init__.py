# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

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

"""
Shows off user interaction widgets.

This screen shows you how you can use input widgets to interact with
the user using buttons, text-fields etc.

The callbacks defines what actually happens when the user does
something, e.g. clicks on the 'go' button. When this happen, a
callback function is called in this file. This callback can modify the
user interface 'live' - there is no explicit session handling as in
e.g. PHP or JavaBeans, but it works much the same as Gtk - the UI
stays the same until explicitly modified, and changes are seen by the
user more or less directly (as soon as the webpage finishes loading
:).

The layout of the classes defined inside each other in the callbacks
file exactly mirrors the widget tags in the Wwml file. Compare the
class-structure (see below) to the following exerpt::

 <w:Tabset id="Input" title="Input">
  <w:Html id="PageLoad" title="Page load callback">
   ...
  </w:Html>

  <w:Fieldgroup id="Data" title="Data input">
   ...
   <w:Field id="LastPwd" Label=":Html:Last password">
    <w:Html id="Field" error=":none" />
   </w:Field>
   <w:Field id='NewPwd' Label=':Text:New password'>
    <w:NewPasswordInput id="Field" value="foo" bind="dont-require" />
   </w:Field>
   <w:Field id="UpdatePwd" Label=":Html:Update passwords">
    <w:Html id="Field" error=":none">
     <w:Button id="PwdClear" title="Clear new password" />
     <w:Button id="PwdSet" title="Set new password" /><br />
    </w:Html>
   </w:Field>
   ...
  </w:Fieldgroup>

  </w:Tabset>
 </w:Tabset>

"""

class Input(object):
    class PageLoad(object):
        class PageLoad(object):
            count = 0
            def page_load(self, path, mode):
                """This callback is called onece every page load. We
                use it to display a page-load counter, C{Count}."""
                self.count += 1
                self.parent['Count'].html = str(self.count)

    class Data(object):
        class UpdatePwd(object):
            class Field(object):
                class PwdClear(object):
                    def clicked(self, path):
                        """Clear (reset) the content of the C{NewPwd}
                        input field (accessed using a relative path
                        from this button widget)."""
                        self.parent.parent.parent['NewPwd']['Field'].value = ''

                class PwdSet(object):
                    def clicked(self, path):
                        """If the NewPwd new password input fields
                        match, make the C{LastPwd} C{Html}-widget display
                        the text entered there."""
                        newpwd = self.parent.parent.parent['NewPwd']['Field']
                        lastpwd = self.parent.parent.parent['LastPwd']['Field']
                        if newpwd.value is not None:
                            lastpwd.html = newpwd.value
