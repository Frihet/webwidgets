# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Provides a list-selector widget
# Copyright (C) 2008 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

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
import Base, ListMod, LocationInputLocations

class RegionInput(ListMod.RowsSingleValueListInput):
    class WwModel(ListMod.RowsSingleValueListInput.WwModel):
        string_based = True
        region_prefix = []

    def get_region(self):
        region = LocationInputLocations.world
        for prefix in self.ww_filter.region_prefix:
            if prefix not in region.part_dict: return None
            region = region.part_dict[prefix]
        return region
    
    def get_rows(self):
        return getattr(self.get_region(), "parts", [])
    rows = property(get_rows)

    class ValueFilters(ListMod.RowsSingleValueListInput.ValueFilters):
        WwFilters = ListMod.RowsSingleValueListInput.ValueFilters.WwFilters + ["StringValueFilter"]

        class StringValueFilter(Base.Filter):
            class Value(object):
                def __get__(self, instance, owner):
                    if instance is None: return None
                    value = instance.ww_filter.value
                    if instance.string_based and value is not None:
                        region = instance.get_region()
                        value = region and region.part_dict.get(value, None)
                    return value
                def __set__(self, instance, value):
                    if instance.string_based and value is not None:
                        value = value.symbol
                    instance.ww_filter.value = value
            value = Value()

class CountryInput(RegionInput):
    class WwModel(RegionInput.WwModel):
        region_prefix = []

class CountyInput(RegionInput):
    class WwModel(RegionInput.WwModel):
        region_prefix = [""]

class MunicipalityInput(RegionInput):
    class WwModel(RegionInput.WwModel):
        region_prefix = ["", ""]
