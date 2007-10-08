#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moeller@freecode.no>

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

import Webwidgets
import datetime

Webwidgets.Program.Session.debug_fields = False
Webwidgets.Program.Session.debugSendNotification = False

class MyWindow(object):
    class body(object):

        class GreencycleList(object):
            nextId = 0

            def getPages(self):
                return 1
            
            def getRows(self):
                return self.rows

            def valueChanged(self, path, value):
                #print "Change %s: %s" % (path, repr(value))
                self.changed = True
                Webwidgets.GBOList.valueChanged(self, path, value)
            
        class Add(object):
            def clicked(self, path):
                kg=Webwidgets.Html(self.session, self.win_id, html="kg")
                count=Webwidgets.Html(self.session, self.win_id, html="count")

                self.parent['GreencycleList'].nextId += 1
                newRow = {"idd": self.parent['GreencycleList'].nextId,
                          "currency" : Webwidgets.StringInput(self.session, self.win_id, value=""),
                          "name": Webwidgets.StringInput(self.session, self.win_id, value="")}
                self.parent['GreencycleList'].rows.append(newRow)
