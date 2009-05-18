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

import Webwidgets.FilterMod.StandardFilters
import Webwidgets.Widgets.InputMod.LocationInput
import Webwidgets.Widgets.InputMod.LocationInputLocations

def redirect_value_to_address(name):
    class RedirectValueToAddressClass(object):
        RedirectValueToAddress = Webwidgets.FilterMod.StandardFilters.RedirectRenameFilter.redirect([], 2, active = "active", value = name)
    return RedirectValueToAddressClass
    
class AddressInput(object):
    class WwModel(object):
        active = True
        co = ''
        street = ''
        zip = ''
        city = ''
        municipality = ''
        county = ''
        country = ''
        
    class Co(object):
        class Field(redirect_value_to_address('co')): pass
    class Street(object):
        class Field(redirect_value_to_address('street')): pass
    class Zip(object):
        class Field(redirect_value_to_address('zip')): pass
    class City(object):
        class Field(redirect_value_to_address('city')): pass
    class Region(object):
        RegionRedirect = Webwidgets.FilterMod.StandardFilters.RedirectRenameFilter.redirect(
            [], 1,
            active = "active",
            municipality = "municipality",
            county = "county",
            country = "country").add_class_in_ordering(
            'filter', pre = Webwidgets.Widgets.InputMod.LocationInput.MunicipalityInput.ww_filter_last)

def redirect_html_to_address(name):
    class RedirectHtmlToAddressClass(object):
        RedirectHtmlToAddress = Webwidgets.FilterMod.StandardFilters.RedirectRenameFilter.redirect([], 2, html = name)
    return RedirectHtmlToAddressClass
    
class Address(object):
    class WwModel(object):
        co = 'X'
        street = 'Y'
        zip = ''
        city = ''
        municipality = ''
        county = ''
        country = ''
        
    class Co(object):
        class Field(redirect_html_to_address('co')): pass
    class Street(object):
        class Field(redirect_html_to_address('street')): pass
    class Zip(object):
        class Field(redirect_html_to_address('zip')): pass
    class City(object):
        class Field(redirect_html_to_address('city')): pass
    class Region(object):
        RegionRedirect = Webwidgets.FilterMod.StandardFilters.RedirectRenameFilter.redirect([], 1,
                                                               municipality = "municipality",
                                                               county = "county",
                                                               country = "country").add_class_in_ordering(
            'filter', pre = Webwidgets.Widgets.InputMod.LocationInput.Municipality.ww_filter_last)
