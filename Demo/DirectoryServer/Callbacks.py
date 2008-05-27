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
import datetime, StringIO

class File(object):
    def __init__(self, content, type="text/plain"):
        self.file = StringIO.StringIO(content)
        self.type = type


class MyWindow(object):
    class Body(object):
        class Media0(object):
            content = File("Media 0 content")
        class Media1(object):
            content = File("Media 1 content")
        class Media2(object):
            content = File("Media 2 content")
        class Media3(object):
            content = File("Media 3 content")
        class Media4(object):
            content = File("Media 4 content")
        class Media5(object):
            content = File("Media 5 content")
        class Media6(object):
            content = File("Media 6 content")
        class Media7(object):
            content = File("Media 7 content")
        class Media8(object):
            content = File("Media 8 content")
        class Media9(object):
            content = File("Media 9 content")

        class Media10(object):
            content = File("Media 10 content")
        class Media11(object):
            content = File("Media 11 content")
        class Media12(object):
            content = File("Media 12 content")
        class Media13(object):
            content = File("Media 13 content")
        class Media14(object):
            content = File("Media 14 content")
        class Media15(object):
            content = File("Media 15 content")
        class Media16(object):
            content = File("Media 16 content")
        class Media17(object):
            content = File("Media 17 content")
        class Media18(object):
            content = File("Media 18 content")
        class Media19(object):
            content = File("Media 19 content")
