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
Webwidgets.Program.Session.debug_send_notification = False

class MyWindow(object):
    class Body(object):
        class Submit(object):
            def clicked(self, path):
                print self.parent['Address'].ww_filter.co
                print self.parent['Address'].ww_filter.street
                print self.parent['Address'].ww_filter.zip
                print self.parent['Address'].ww_filter.city
                print self.parent['Address'].ww_filter.municipality
                print self.parent['Address'].ww_filter.county
                print self.parent['Address'].ww_filter.country


        class Address(object):
            WwFilters = [Webwidgets.RedirectRenameFilter.redirect(['AddressInput'], 1)]
