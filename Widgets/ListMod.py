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
import Base, RowsMod

class RowsListInput(Base.ValueInput, RowsMod.RowsComposite):
    """Scrollable list of selectable items. The list can optionally
    allow the user to select multiple items."""
    
    original_value = []

    class WwModel(RowsMod.RowsComposite.WwModel, Base.ValueInput.WwModel):
        value = []

        column_separator = ' '
        
        multiple = True
        """Allow the user to select multiple items."""

        size = 0
        """Size of the widget."""

    WwFilters = RowsMod.RowsComposite.WwFilters + ["ValueFilters"]

    class ValueFilters(Base.Filter):
        WwFilters = []

    def draw_option(self, selected, value, description, output_options):
        return """<option %(selected)s value="%(value)s">
                   %(description)s
                  </option>""" % {'selected': selected and 'selected="selected"' or '',
                                  'value': value,
                                  'description': description}
    def draw_row(self, row, output_options):
        return self.draw_option(
            row.ww_model in self.ww_filter.value,
            self.ww_filter.get_row_id(row),
            self.column_separator.join(
                [self.draw_cell(row, column_name, getattr(row, column_name), output_options)
                 for (column_name, column_def)
                 in self.visible_columns(output_options).iteritems()]),
            output_options)
        
    def draw_options(self, output_options):
        none = []
        if not self.ww_filter.multiple:
            none = [self.draw_option(not self.ww_filter.value, "", "&lt;None selected&gt;", output_options)]
        return none + [self.draw_row(row, output_options)
                       for row in self.ww_filter.get_rows(output_options)]
    
    def draw(self, output_options):
        Base.ValueInput.draw(self, output_options)

        return """<select %(html_attributes)s %(multiple)s %(size)s name="%(name)s" %(disabled)s>
         %(options)s
         </select>""" % {
            'html_attributes': self.draw_html_attributes(self.path),
            'multiple': self.ww_filter.multiple and 'multiple' or '',
            'size': self.size != 0 and 'size="%s"' % self.size or '',
            'name': Webwidgets.Utils.path_to_id(self.path),
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)],
            'options': '\n'.join(self.draw_options(output_options))
            }

    def field_input(self, path, *string_values):
        self.ww_filter.value = [self.ww_filter.get_row_by_id(value).ww_model
                                for value in string_values
                                if value]

    def field_output(self, path):
        if not self.ww_filter.value:
            return ['']
        return [self.ww_filter.get_row_id_from_row_model(row) for row in self.ww_filter.value]

class RowsSingleValueListInput(RowsListInput):
    class ValueFilters(RowsListInput.ValueFilters):
        WwFilters = ["SingleValueFilter"] + RowsListInput.ValueFilters.WwFilters

        class SingleValueFilter(Base.Filter):
            multiple = False

            class Value(object):
                def __get__(self, owner, instance):
                    return [instance.ww_filter.value]

                def __set__(self, instance, value):
                    instance.ww_filter.value = value[0]

            value = Value()
