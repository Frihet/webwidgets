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

import cgi, os.path

class Home(object):
    class logo(object):
        content = cgi.FieldStorage()
        content.filename = "Logo.png"
        content.type = "image/png"
        content.file = open(os.path.join(os.path.split(__file__)[0],
                                         "../../../Docs/Logo.png"))
        content.file.seek(0)


#     class SubclassWithNoWidget(object):
#         ww_bind_widget = "require"
