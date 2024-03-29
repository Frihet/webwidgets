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
        class Autoexpand(object):
#            default_expand = False
            def __init__(self, session, win_id, **attrs):
                Webwidgets.Table.__init__(self, session, win_id, **attrs)
                self.pre_sort = [('country', 'asc'),
                                 ]
                self.sort = [('provider', 'asc'),
                             ('technology', 'asc'),
                             ('price', 'asc')]
                self.rows = []
                for country in ('SE', 'NO', 'FI', 'DK'):
                    for provider  in ('Comm2', 'BandCorp', 'Fieacomm', 'OFelia'):
                        for technology in ('modem', 'DSL1', 'DSL2', 'cable'):
                            for price in ('100-200', '200-300', '300-400', '400-'):
                                self.rows.append({'country':country, 'provider':provider, 'technology':technology, 'price':price})

        class DebugNow(object):
            def clicked(self, path):
                import pdb
                pdb.set_trace()
