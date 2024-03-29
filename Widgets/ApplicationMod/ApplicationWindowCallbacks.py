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

class ApplicationWindow(object):
    is_dialog_container = True

    class Body(object):
        class LogIn(object):
            class Application(object):
                class Title(object):
                    def __get__(self, instance, owner):
                        if (   instance is None
                            or instance.parent is None
                            or instance.parent.parent is None
                            or instance.parent.parent.parent is None):
                            return None
                        return instance.parent.parent.parent.title
                title = Title()

    def add_dialog(self, dialog, name = None):
        if name is None: name = str(len(self['Body']['Dialogs'].children))
        self['Body']['Dialogs'][name] = dialog
        dialog.remove_on_close = True

