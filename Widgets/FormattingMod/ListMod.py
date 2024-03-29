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
import Webwidgets.FilterMod.StandardFilters
import Webwidgets.Widgets.Base
import Webwidgets.Widgets.RowsMod

class RowsListInput(Webwidgets.Widgets.Base.ValueInput, Webwidgets.Widgets.RowsMod.RowsComposite):
    """Scrollable list of selectable items. The list can optionally
    allow the user to select multiple items. The currently selected
    item(s) are stored in a list, regardless of if multiple items can
    be shoosen or not."""
    
    original_value = []

    class WwModel(Webwidgets.Widgets.RowsMod.RowsComposite.WwModel, Webwidgets.Widgets.Base.ValueInput.WwModel):
        rows_per_page = 0
        
        value = []

        column_separator = ' '
        """If multiple columns are to be displayed (see L{column}),
        separate their contents within each row with this string."""
        
        multiple = True
        """Allow the user to select multiple items."""

        allow_none = True
        """Allow the user to select no item at all. Only applicable if
        multiple is False. Noet: that value can still be None if the
        list is empty."""

        size = 0
        """Size of the widget."""

    class ValueFilters(Webwidgets.FilterMod.Base.Filter):
        """This filter groups all filters that mangles the L{value} of
        the widget, that is, the item selection."""
    ValueFilters.add_class_in_ordering('filter', post = Webwidgets.Widgets.RowsMod.RowsComposite.ww_filter_first)


    def only_one_row(self):
        # Check if there is exactly one row to select from
        rows = self.ww_filter.get_rows(output_options = {})
        
        return (    not self.ww_filter.multiple
                and not self.ww_filter.allow_none
                and len(rows) == 1)

    def no_rows(self):
        # Check if there is no rows at all to select from from
        rows = self.ww_filter.get_rows(output_options = {})
        return len(rows) == 0
        
    def get_active(self, path):
        return (    not self.no_rows()
                and Webwidgets.Widgets.Base.ValueInput.get_active(self, path))

    @property
    def html_disabled(self):
        return ['', 'disabled="disabled"'][self.only_one_row() or not self.get_active(self.path)]

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
        if not self.ww_filter.multiple and self.allow_none:
            none = [self.draw_option(not self.ww_filter.value, "", "&lt;None selected&gt;", output_options)]
        return none + [self.draw_row(row, output_options)
                       for row in self.ww_filter.get_rows(output_options = output_options)]

    def draw(self, output_options):
        Webwidgets.Widgets.Base.ValueInput.draw(self, output_options)

        active = self.get_active(self.path)

        res = """<select %(html_attributes)s %(multiple)s %(size)s name="%(name)s">
         %(options)s
         </select>""" % {
            'html_attributes': self.draw_html_attributes(self.path),
            'multiple': self.ww_filter.multiple and 'multiple' or '',
            'size': self.size != 0 and 'size="%s"' % self.size or '',
            'name': Webwidgets.Utils.path_to_id(self.path),
            'options': '\n'.join(self.draw_options(output_options))
            }

        if self.only_one_row():
            rows = self.ww_filter.get_rows(output_options = output_options)
            res += """<input id="%(html_id)s-_-only_one_row" type="hidden" name="%(name)s" value="%(value)s" />""" % {
                'html_id': self.html_id,
                'name': Webwidgets.Utils.path_to_id(self.path),
                'value': self.ww_filter.get_row_id(rows[0]),
                }
        return res

    def field_input(self, path, *string_values):
        self.ww_filter.value = [self.ww_filter.get_row_by_id(value).ww_model
                                for value in string_values
                                if value]

    def field_output(self, path):
        if not self.ww_filter.value:
            return ['']
        return [self.ww_filter.get_row_id_from_row_model(row) for row in self.ww_filter.value]

class RowsSingleValueListInput(RowsListInput):
    """Scrollable list of selectable items. Only one item can be
    selected at a time."""

    
    class WwModel(RowsListInput.WwModel):
        value = None

    class ValueFilters(RowsListInput.ValueFilters):
        class SingleValueFilter(Webwidgets.FilterMod.Base.Filter):
            """This filter makes L{value} contain either the currently
            selected list item (row), or C{None} if none is currently
            selected."""
            multiple = False

            class Value(object):
                def __get__(self, instance, owner):
                    if instance is None: return None
                    if instance.ww_filter.value is None:
                        return []
                    else:
                        return [instance.ww_filter.value]

                def __set__(self, instance, value):
                    if not value:
                        instance.ww_filter.value = None
                    else:
                        instance.ww_filter.value = value[0]
            value = Value()
        SingleValueFilter.add_class_in_ordering('filter', post = RowsListInput.ValueFilters.ww_filter_first)
