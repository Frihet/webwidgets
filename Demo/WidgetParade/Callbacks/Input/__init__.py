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

class Input(object):
    class Data(object):
        class UpdatePwd(object):
            class Field(object):
                class PwdClear(object):
                    def clicked(self, path):
                        self.parent.parent.parent['NewPwd']['Field'].value = ''

                class PwdSet(object):
                    def clicked(self, path):
                        newpwd = self.parent.parent.parent['NewPwd']['Field']
                        lastpwd = self.parent.parent.parent['LastPwd']['Field']
                        if newpwd.value is not None:
                            lastpwd.html = newpwd.value

