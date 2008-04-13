#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# RowsComposite provides a common model and filter engine for
# row-based widgets (tables, lists, etc)
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

"""Group By Ordering List is a special kind of table view that allows
the user to sort the rows and simultaneously group the rows according
to their content and the sorting."""

import Webwidgets.Constants, Webwidgets.Utils, re, math, cgi, types, itertools
import Base

class RowsSimpleModelFilter(Base.Filter):
    # left = RowsPrintableFilter
    # right = BaseTable.WwModel

    debug_expand = False

    # API used by Table
    
    def __init__(self, *arg, **kw):
        Base.Filter.__init__(self, *arg, **kw)
        self.old_sort = None
        self.old_page = None
        self.old_expand = None
	self.expand_version = 0
        self.old_default_expand = None

    def get_rows(self, all, output_options):
        self.ensure()
        if self.non_memory_storage:
            if all:
                return self.ww_filter.get_rows(all, output_options)
            else:
                return self.rows
        else:
            rows = []
            expand_tree = self.get_expand_tree()
            if self.default_expand:
                for row in self.rows:
                    node = expand_tree
                    while (    not node.toggled
                           and self.get_row_col(row, node.col) in node.values):
                        node = node.values[self.get_row_col(row, node.col)]
                    if (   not node.toggled
                        or self.get_row_id(row) in node.rows):
                        rows.append(row)
            else:
                last_row = None
                for row in self.rows:
                    common = self.row_common_sorted_columns(row, last_row)
                    expanded = True
                    node = expand_tree
                    for pos in xrange(0, common):
                        if (   self.get_row_col(row, node.col) not in node.values
                            or not node.values[self.get_row_col(row, node.col)].toggled):
                            expanded = False
                            break
                        node = node.values[self.get_row_col(row, node.col)]
                    if expanded:
                        rows.append(row)

                    last_row = row
            if all:
                return rows
            else:
                return rows[(self.page - 1) * self.rows_per_page:
                            self.page * self.rows_per_page]

    def get_row_col(self, row, col):
        if isinstance(row, dict):
            return row[col]
        else:
            return getattr(row, col)

    def get_row_id(self, row):
        if self.non_memory_storage:
            return self.ww_filter.get_row_id(row)
        else:
            return str(id(row))
    
    def get_row_by_id(self, row_id):
        if self.non_memory_storage:
            return self.ww_filter.get_row_by_id(row_id)
        else:
            for row in self.rows:
                if self.get_row_id(row) == row_id:
                    return row
            raise KeyError(self, row_id)

    def get_pages(self, output_options):
        if self.non_memory_storage:
            return self.ww_filter.get_pages()
        else:
            return int(math.ceil(float(len(self.rows)) / self.rows_per_page))

    def get_columns(self, output_options, only_sortable = False):
        res = Webwidgets.Utils.OrderedDict()
        for name, definition in self.columns.iteritems():
            if isinstance(definition, types.StringTypes):
                res[name] = {"title": definition}
            else:
                res[name] = definition
        return res

    def field_input_expand(self, path, string_value):
        row_id, col = string_value.split(',')
        row = self.object.ww_filter.get_row_by_id(row_id)
        if row_id not in self.expand:
            self.expand[row_id] = {'row': row,
                                   'expanded_cols': set((col,))}
        else:
            if col not in self.expand[row_id]['expanded_cols']:
                self.expand[row_id]['expanded_cols'].add(col)
            else:
                self.expand[row_id]['expanded_cols'].remove(col)
	self.expand_version += 1

    def field_output_expand(self, path):
        return []

    def get_active_expand(self, path):
        return self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, self.path + ['expand'] + path)

    # Internal
    def ensure(self):
        """Reload the list after a repaging/resorting"""
        if (   self.sort != self.old_sort
            or self.page != self.old_page
            or self.expand_version != self.old_expand
            or self.default_expand != self.old_default_expand):
            self.reread()

    def reread(self):
        """Reload the list"""
        if self.non_memory_storage:
            self.rows[:] = self.ww_filter.get_rows(False, {})
        elif self.sort != self.old_sort:
            def row_cmp(row1, row2):
                for col, order in self.sort:
                    diff = cmp(row1[col], row2[col])
                    if diff:
                        if order == 'desc': diff *= -1
                        return diff
                return 0
            self.rows.sort(row_cmp)
        self.old_sort = self.sort
        self.old_page = self.page
        self.old_expand = self.expand_version
        self.old_default_expand = self.default_expand

class RowsPrintableFilter(Base.Filter):
    # left = BaseTable
    # right = RowsSimpleModelFilter
    
    def get_rows(self, output_options):
        return self.ww_filter.get_rows('printable_version' in output_options, output_options)

class RowsRowWrapperFilter(Base.Filter):
    def get_rows(self, all, output_options):
        return [self.RowsRowModelWrapper(table = self.object, ww_model = row)
                for row in self.ww_filter.get_rows(all, output_options)]

    def get_row_id(self, row):
        return "wrap_" + self.ww_filter.get_row_id(row.ww_model)

    def get_row_by_id(self, row_id):
        if not row_id.startswith("wrap_"):
            raise Exception("Invalid row-id %s (should have started with 'wrap_')" % row_id)
        return self.RowsRowModelWrapper(
            table = self.object,
            ww_model = self.ww_filter.get_row_by_id(row_id[5:]))
    

class RowsComposite(Base.CachingComposite):
    class WwModel(Base.Model):
        rows = []
        sort = []
        page = 1
        expand = {}
        non_memory_storage = False
        rows_per_page = 10

        def get_rows(self, all, output_options):
            """Load the list after a repaging/resorting, or for a
            printable version. If you set non_memory_storage to True, you
            _must_ implement this method.
            """
            raise NotImplementedError("get_rows")

        def get_row_by_id(self, row_id):
            raise NotImplementedError("get_row_by_id")

        def get_row_id(self, row):
            raise NotImplementedError("get_row_id")

        def get_pages(self):
            """Returns the total number of pages. If you set
            non_memory_storage to True, you _must_ implement this method.
            """
            raise NotImplementedError("get_pages")
    
    class SourceFilters(Base.Filter):
        WwFilters = ["RowsSimpleModelFilter"]
        class RowsSimpleModelFilter(RowsSimpleModelFilter): pass

    class RowsFilters(Base.Filter):
        WwFilters = ["RowsRowWrapperFilter"]
        class RowsRowWrapperFilter(RowsRowWrapperFilter): pass

    class OutputOptionsFilters(Base.Filter):
        WwFilters = ["RowsPrintableFilter"]
        class RowsPrintableFilter(RowsPrintableFilter): pass

    WwFilters = ["OutputOptionsFilters", "RowsFilters", "SourceFilters"]

    class RowsRowModelWrapper(Base.PersistentWrapper):
        def ww_first_init(self, ww_model, *arg, **kw):
            Base.PersistentWrapper.ww_first_init(self, ww_model = ww_model, *arg, **kw)
            self.__dict__['items'] = {}

            # FIXME: Just remove this stuff I guess? Shouldn't be used...
            if isinstance(ww_model, dict):
                self.ww_row_id = ww_model.get('ww_row_id', id(ww_model))
            else:
                self.ww_row_id = getattr(ww_model, 'ww_row_id', id(ww_model))

        def __getattr__(self, name):
            if isinstance(self.ww_model, dict):
                if name not in self.ww_model:
                    raise AttributeError(self.ww_model, name)
                return self.ww_model[name]
            else:
                return getattr(self.ww_model, name)
