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

import Base, ListMod, LocationInput, LocationInputLocations

class AddressInput(object):
    class Country(object):
        class Field(object):
            def value_changed(self, path, value):
                self.parent.parent['County']['Field'].ww_filter.region_prefix = [self.value]
            def draw(self, output_options):
                self.register_submit_action(self.path, 'change')
                return LocationInput.CountryInput.draw(self, output_options)
    
    class County(object):
        class Field(object):
            def value_changed(self, path, value):
                self.parent.parent['Municipality']['Field'].ww_filter.region_prefix = (
                    self.ww_filter.region_prefix + [self.value])
            def draw(self, output_options):
                self.register_submit_action(self.path, 'change')
                return LocationInput.CountyInput.draw(self, output_options)

class ApplicationWindow(object):
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
