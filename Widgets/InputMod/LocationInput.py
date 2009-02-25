# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

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

import Webwidgets.Utils
import Webwidgets.ObjectMod
import Webwidgets.FilterMod
import Webwidgets.Widgets.WindowMod
import Webwidgets.Widgets.FormattingMod.BaseFormatting
import Webwidgets.Widgets.FormattingMod.ListMod
import Webwidgets.Widgets.InputMod.LocationInputLocations

class GenericRegionPart(Webwidgets.ObjectMod.Object):
    class WwModel(Webwidgets.ObjectMod.Object):
        string_based = True
        store_symbol = True
        region_prefix = []

    def get_region_from_sym(self):
        region = Webwidgets.Widgets.InputMod.LocationInputLocations.world
        for prefix in self.ww_filter.region_prefix:
            if prefix not in region.sym_dict: return None
            region = region.sym_dict[prefix]
        return region

    def get_region_from_name(self):
        region = Webwidgets.Widgets.InputMod.LocationInputLocations.world
        for prefix in self.ww_filter.region_prefix:
            if prefix not in region.name_dict: return None
            region = region.name_dict[prefix]
        return region
    
    WwFilters = ['RegionNameFilter']

    class RegionNameFilter(Webwidgets.FilterMod.Filter):
        class Value(object):
            def __get__(self, instance, owner):
                if instance is None: return None
                value = instance.ww_filter.value

                if instance.string_based and value is not None:
                    if instance.store_symbol:
                        region = instance.get_region_from_sym()
                        value = region and region.sym_dict.get(value, None)
                    else:
                        region = instance.get_region_from_name()
                        value = region and region.name_dict.get(value, None)
                return value
            def __set__(self, instance, value):
                if instance.string_based and value is not None:
                    if instance.store_symbol:
                        value = value.symbols[-1]
                    else:
                        value = value.title
                instance.ww_filter.value = value
        value = Value()

class RegionPartInput(GenericRegionPart, Webwidgets.Widgets.FormattingMod.ListMod.RowsSingleValueListInput):
    class WwModel(GenericRegionPart.WwModel, Webwidgets.Widgets.FormattingMod.ListMod.RowsSingleValueListInput.WwModel): pass
    WwFilters = Webwidgets.Widgets.FormattingMod.ListMod.RowsSingleValueListInput.WwFilters + GenericRegionPart.WwFilters
    
    def get_rows(self):
        if self.ww_model.store_symbol:
            return getattr(self.get_region_from_sym(), "parts", [])
        else:
            return getattr(self.get_region_from_name(), "parts", [])
    rows = property(get_rows)

class CountryPartInput(RegionPartInput):
    class WwModel(RegionPartInput.WwModel):
        region_prefix = []

class CountyPartInput(RegionPartInput):
    __input_subordinates__ = (CountryPartInput, )
    class WwModel(RegionPartInput.WwModel):
        region_prefix = [""]

class MunicipalityPartInput(RegionPartInput):
    __input_subordinates__ = (RegionPartInput, )
    class WwModel(RegionPartInput.WwModel):
        region_prefix = ["", ""]

class CountryInput(Webwidgets.Html):
    html = "%(Country)s%(Update)s"
    __wwml_html_override__ = False

    class WwModel(object):
        active = True
        country = ''

    class Update(Webwidgets.UpdateButton): pass
    
    class Country(Webwidgets.Field):
        class Label(Webwidgets.Html): html = "Country"
        class Field(CountryPartInput):
            field_name = "country"
            WwFilters = CountryPartInput.WwFilters + [Webwidgets.FilterMod.RedirectRenameFilter.redirect([], 2, active = "active", value ='country')]

class CountyInput(CountryInput):
    html = "%(County)s" + CountryInput.html

    class WwModel(CountryInput.WwModel):
        county = ''

    class Country(CountryInput.Country):
        class Field(CountryInput.Country.Field):
            def draw(self, output_options):
                Webwidgets.Widgets.WindowMod.HtmlWindow.register_submit_action(self, self.path, 'change')
                return CountryInput.Country.Field.draw(self, output_options)

            def value_changed(self, path, value):
                # Ignore output this request as this changes the list
                # of valid values.
                self.parent.parent['County']['Field'].ignore_input_this_request = True
                self.parent.parent['County']['Field'].ww_filter.value = []
                CountryInput.Country.Field.value_changed(self, path, value)

    class County(Webwidgets.Field):
        class Label(Webwidgets.Html): html = "Region"
        class Field(CountyPartInput):
            field_name = "county"
            WwFilters = CountyPartInput.WwFilters + [
                Webwidgets.FilterMod.RedirectRenameFilter.redirect([], 2, active = "active", value ='county'),
                Webwidgets.FilterMod.MangleFilter.mangle(
                    region_prefix = lambda self: [self.parent.parent.ww_filter.country])]

class MunicipalityInput(CountyInput):
    html = "%(Municipality)s" + CountyInput.html

    class WwModel(CountyInput.WwModel):
        municipality = ''

    class Country(CountyInput.Country):
        class Field(CountyInput.Country.Field):
            def value_changed(self, path, value):
                # Ignore output this request as this changes the list
                # of valid values.                
                for part in ('Municipality', 'County'):
                    self.parent.parent[part]['Field'].ignore_input_this_request = True
                    self.parent.parent[part]['Field'].ww_filter.value = []
                CountyInput.Country.Field.value_changed(self, path, value)

    class County(CountyInput.County):
        class Field(CountyInput.County.Field):
            def draw(self, output_options):
                Webwidgets.Widgets.WindowMod.HtmlWindow.register_submit_action(self, self.path, 'change')
                return CountyInput.County.Field.draw(self, output_options)

            def value_changed(self, path, value):
                # Ignore input this request as this changes the list
                # of valid values.
                self.parent.parent['Municipality']['Field'].ignore_input_this_request = True
                self.parent.parent['Municipality']['Field'].ww_filter.value = []
                CountyInput.County.Field.value_changed(self, path, value)

    class Municipality(Webwidgets.Field):
        class Label(Webwidgets.Html): html = "Municipality"
        class Field(MunicipalityPartInput):
            field_name = "municipality"
            WwFilters = MunicipalityPartInput.WwFilters + [
                Webwidgets.FilterMod.RedirectRenameFilter.redirect([], 2, active = "active", value ='municipality'),
                Webwidgets.FilterMod.MangleFilter.mangle(
                region_prefix = lambda self: [self.parent.parent.ww_filter.country,
                                              self.parent.parent.ww_filter.county])]

class RegionPart(GenericRegionPart, Webwidgets.Widgets.FormattingMod.BaseFormatting.Html):
    class WwModel(GenericRegionPart.WwModel): pass
    WwFilters = Webwidgets.Widgets.FormattingMod.BaseFormatting.Html.WwFilters + [Webwidgets.FilterMod.RenameFilter.rename(html = "value"),
                                             Webwidgets.FilterMod.MapValueFilter.map_values(value = {'-': None})] + GenericRegionPart.WwFilters

class CountryPart(RegionPart):
    class WwModel(RegionPart.WwModel):
        region_prefix = []

class CountyPart(RegionPart):
    class WwModel(RegionPart.WwModel):
        region_prefix = [""]

class MunicipalityPart(RegionPart):
    class WwModel(RegionPart.WwModel):
        region_prefix = ["", ""]

class Country(Webwidgets.Html):
    html = "%(Country)s"
    __wwml_html_override__ = False

    class WwModel(object):
        country = ''

    class Country(Webwidgets.Field):
        class Label(Webwidgets.Html): html = "Country"
        class Field(CountryPart):
            field_name = "country"
            WwFilters = CountryPart.WwFilters + [Webwidgets.FilterMod.RedirectRenameFilter.redirect([], 2, value ='country')]

class County(Country):
    html = "%(County)s" + Country.html

    class WwModel(Country.WwModel):
        county = ''

    class County(Webwidgets.Field):
        class Label(Webwidgets.Html): html = "Region"
        class Field(CountyPart):
            field_name = "county"
            WwFilters = CountyPart.WwFilters + [
                Webwidgets.FilterMod.RedirectRenameFilter.redirect([], 2, value ='county'),
                Webwidgets.FilterMod.MangleFilter.mangle(
                    region_prefix = lambda self: [self.parent.parent.ww_filter.country])]

class Municipality(County):
    html = "%(Municipality)s" + County.html

    class WwModel(County.WwModel):
        municipality = ''

    class Municipality(Webwidgets.Field):
        class Label(Webwidgets.Html): html = "Municipality"
        class Field(MunicipalityPart):
            field_name = "municipality"
            WwFilters = MunicipalityPart.WwFilters + [
                Webwidgets.FilterMod.RedirectRenameFilter.redirect([], 2, value = 'municipality'),
                Webwidgets.FilterMod.MangleFilter.mangle(
                region_prefix = lambda self: [self.parent.parent.ww_filter.country,
                                              self.parent.parent.ww_filter.county])]
