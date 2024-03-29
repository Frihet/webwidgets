# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

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

import re, math, cgi, types, itertools
import Webwidgets.Constants
import Webwidgets.Utils
import Webwidgets.FilterMod.StandardFilters
import Webwidgets.Widgets.Base

class RowsSimpleModelFilter(Webwidgets.FilterMod.Base.Filter):
    """This filter adds support for memmory mapped L{RowsComposite} -
    that is for when L{RowsComposite.WwModel.non_memory_storage} is
    set to C{False} and for row caching when set to C{True}. It also
    provides a base implementation of the row/tree collapse algorithm
    for rows with merged cells (in L{get_rows}).
    """

    # left = RowsPrintableFilter
    # right = BaseTable.WwModel

    debug_expand = False

    # API used by Table
    
    def __init__(self, *arg, **kw):
        Webwidgets.FilterMod.Base.Filter.__init__(self, *arg, **kw)
        self.old_sort = None
        self.old_page = None
        self.old_expand = None
        self.expand_version = 0
        self.old_default_expand = None

    def get_rows(self, all = False, output_options = {}, **kw):
        """This method implements row sorting and the row/tree
        collapse algorithm for rows with merged cells. This method
        should/could be used as a basis when implementing the same
        functionality in some other way - e.g. as a compiler of
        sorting lists to SQL queries."""
        self.ensure()
        if self.non_memory_storage:
            if all:
                return self.ww_filter.get_rows(all = all, output_options = output_options, **kw)
            else:
                return self.rows
        else:
            # Just here to support very simple list-like rows back-ends.
            rows = self.rows
            if self.dont_sort_in_place or hasattr(rows, 'sort'):
                rows = list(rows)
                rows.sort(self.row_cmp)
                
            result_rows = []
            expand_tree = self.get_expand_tree()
            
            if self.default_expand:
                for row in rows:
                    node = expand_tree
                    while (    not node.toggled
                           and self.get_row_col(row, node.col) in node.values):
                        node = node.values[self.get_row_col(row, node.col)]
                    if (   not node.toggled
                        or self.get_row_id(row) in node.rows):
                        result_rows.append(row)
            else:
                last_row = None
                for row in rows:
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
                        result_rows.append(row)
                    last_row = row

            if all or self.rows_per_page == 0:
                return result_rows
            else:
                return result_rows[(self.page - 1) * self.rows_per_page:
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

    def get_row_id_from_row_model(self, row_model):
        return self.get_row_id(row_model)
    
    def get_row_id_to_model_row_id(self, row_id):
        return self.get_row_id_from_row_model(self.object.ww_filter.get_row_by_id(row_id).ww_model)

    def get_row_by_id(self, row_id, **kwargs):
        if self.non_memory_storage:
            return self.ww_filter.get_row_by_id(row_id, **kwargs)
        else:
            for row in self.rows:
                if self.get_row_id(row) == row_id:
                    return row
            raise KeyError(self, row_id)

    def get_pages(self, output_options):
        return int(math.ceil(float(self.get_number_of_rows(output_options)) / self.rows_per_page))

    def get_number_of_rows(self, output_options):
        if self.non_memory_storage:
            return self.ww_filter.get_number_of_rows(output_options)
        else:
            return len(self.rows)

    def get_columns(self, output_options, only_sortable = False):
        res = Webwidgets.Utils.OrderedDict()
        for name, definition in self.columns.iteritems():
            if isinstance(definition, types.StringTypes):
                res[name] = {"title": definition}
            else:
                res[name] = definition
        return res

    def expand_row(self, row_id, col):
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

    def needs_refresh(self):
        return (   self.object.ww_filter.sort != self.old_sort
                or self.page != self.old_page
                or self.expand_version != self.old_expand
                or self.default_expand != self.old_default_expand)

    # Internal
    def ensure(self):
        """Reload the list after a repaging/resorting"""
        if self.object.ww_filter.needs_refresh():
            self.object.ww_filter.reread()

    def row_cmp(self, row1, row2):
        for col, order in self.object.ww_filter.sort:
            if hasattr(row1, '__getitem__'):
                diff = cmp(row1[col], row2[col])
            elif hasattr(row1, 'title'):
                diff = cmp(row1.title, row2.title)
            else:
                diff = cmp(str(row1), str(row2))
                
            if diff:
                if order == 'desc': diff *= -1
                return diff
        return 0

    def reread(self):
        """Reload the list"""
        if self.non_memory_storage:
            self.rows[:] = self.ww_filter.get_rows()
        elif (    not self.dont_sort_in_place
              and hasattr(self.rows, 'sort')
              and self.object.ww_filter.sort != self.old_sort):
            self.rows.sort(self.row_cmp)
        self.old_sort = self.object.ww_filter.sort
        self.old_page = self.page
        self.old_expand = self.expand_version
        self.old_default_expand = self.default_expand

class RowsPrintableFilter(Webwidgets.FilterMod.Base.Filter):
    """This filter handles the 'printable_version' output option -
    when set, I{all} rows are returned, not just the current page."""
    # left = BaseTable
    # right = RowsSimpleModelFilter
    
    def get_rows(self, **kw):
        # Previously this overwrote all parameter, which is not ok causing a
        # call to get_rows(all=True) never to return all rows.
        if 'printable_version' in kw.get('output_options', {}):
            kw['all'] = True
        return self.ww_filter.get_rows(**kw)

class RowsRowWrapperFilter(Webwidgets.FilterMod.Base.Filter):
    """This filter wraps all rows in L{RowsComposite.RowsRowModelWrapper}. This adds
       a filtering chain on individual rows; to override cells in a
       row (columns) you can add L{Filter}s to the
       L{RowsComposite.RowsRowModelWrapper} class."""
    
    def get_rows(self, **kw):
        return [self.RowsRowModelWrapper(table = self.object, ww_model = row)
                for row in self.ww_filter.get_rows(**kw)]

    def get_row_id(self, row):
        return "wrap_" + self.ww_filter.get_row_id(row.ww_model)

    def get_row_by_id(self, row_id, **kwargs):
        if not row_id.startswith("wrap_"):
            raise Exception("Invalid row-id %s (should have started with 'wrap_')" % row_id)
        return self.RowsRowModelWrapper(
            table = self.object,
            ww_model = self.ww_filter.get_row_by_id(row_id[5:], **kwargs))
    

class RowsComposite(Webwidgets.Widgets.Base.CachingComposite):
    """
    RowsComposite is the base class for widgets that provide some
    kind of list or table of other widgets that can be sorted,
    collapsed and filtered in various ways.

    Notable/special features:

        - The list can be divided into pages, shown one at a time.

        - The list can be sorted on any number of columns, in any order.

        - Consecutive rows have their cells merged if they share values in
          the first sorted columns (prefix).

        - Rows that have merged cells can be collapsed.

        - The above essentially creats a collapsible tree of the rows,
          where the cells, put in the current sorting order, are elements
          in the path to the row.

        - The set of rows as well as the content of individual rows can be
          filtered using L{Filter}s.

    """

    class WwModel(Webwidgets.ObjectMod.Model):
        rows = []
        sort = []

        page = 1

        expand = {}
        default_expand = True
        """If true, all rows are expanded until collapsed, if false
        all rows are collapsed until expanded. This reverses the
        meaning of the expand attribute."""

        rows_per_page = 8

        columns = {'title': 'Title'}
        """{column_name: title | {"title":title, ...}}"""
        dependent_columns = {}
        """{column_name: [column_name]}"""
        dont_merge_widgets = True
        
        merge_columns = ()
        """List of columns to merge if merge_columns_exclude = True or
        include if False"""
        merge_columns_exclude = False
        """If False, merge columns not in merge_columns, if True merge all
        but the ones in merge_columns"""

        non_memory_storage = False

        """This base class along with the standard L{Filter}s it
        provides supports two basic back-ends, selected by this
        variable:

        If set to C{True}, the subclass using this base class I{must}
        implement L{get_rows}, L{get_row_by_id}, etc.

        If set to C{False}, the subclass using this base class I{must}
        provide a rows member variable containing the rows to display.
        """

        dont_sort_in_place = False
        """Don't modify the L{rows} member variable when resorting the
        list.

        Only applies if L{non_memory_storage} is set to C{False}."""

        def __init__(self):
            super(RowsComposite.WwModel, self).__init__()
            self.expand = dict(self.expand)
            self.sort = list(self.sort)
            self.rows = list(self.rows)

        def get_rows(self, **kw):
            """Load the list after a repaging/resorting, or for a
            printable version. If you set L{non_memory_storage} to
            C{True}, you I{must} implement this method.
            """
            raise NotImplementedError("get_rows")

        def get_row_by_id(self, row_id, **kwargs):
            """Load one row given its internal id returned by a
            previous call to L{get_row_id}. If you set
            L{non_memory_storage} to C{True}, you I{must} implement
            this method.
            """
            raise NotImplementedError("get_row_by_id")

        def get_row_id(self, row):
            """Return the internal id for a row to be used in a later
            call to L{get_row_by_id}. The returned value must be a
            string and unique for this row. If you set
            L{non_memory_storage} to C{True}, you I{must} implement
            this method.
            """
            raise NotImplementedError("get_row_id")

        def get_pages(self):
            """Return the total number of pages. If you set
            L{non_memory_storage} to C{True}, you I{must} implement
            this method.
            """
            raise NotImplementedError("get_pages")

    class RowsRowWidget(Webwidgets.Widgets.Base.CachingComposite): pass

    class SourceFilters(Webwidgets.FilterMod.Base.Filter):
        """This filter groups all filters that provides rows from some
        kind of back-end - e.g. a database query, a redirect from
        another table etc.""" 

        class RowsSimpleModelFilter(RowsSimpleModelFilter): pass

    class SourceErrorFilter(Webwidgets.FilterMod.Base.Filter):
        """This filter is before the SourceFilter and is there to be
        able to catch errors in the data fetching SourceFilters."""

        class CatchErrorFilter(Webwidgets.Filter):
            sort_error_msg = u'Unable to sort with specified order, resetting sort order'
            """Message displayed when get_rows fails, assume it is a sorting issue"""

            def get_rows(self, **kwargs):
                """Get rows from database, resetting sort order if
                something goes wrong."""
                try:
                    result = self.ww_filter.get_rows(**kwargs)
                except Exception, exc:
                    # Reset sort order, try again
                    self.ww_filter.sort = getattr(self.ww_filter, 'default_sort', [])
                    result = self.ww_filter.get_rows(**kwargs)
                    self.object.append_exception(self.sort_error_msg)

                return result
    SourceErrorFilter.add_class_in_ordering('filter', post = [SourceFilters])

    class RowsFilters(Webwidgets.FilterMod.Base.Filter):
        """This filter groups all filters that mangle rows in some way
        - wrapping them, adding extra rows, hiding rows etc."""
        
        class RowsRowWrapperFilter(RowsRowWrapperFilter): pass
    RowsFilters.add_class_in_ordering('filter', post = [SourceErrorFilter])

    class OutputOptionsFilters(Webwidgets.FilterMod.Base.Filter):
        """This filter groups all filters that generate options for
        L{get_rows} based on L{output_options}."""
        class RowsPrintableFilter(RowsPrintableFilter): pass
    OutputOptionsFilters.add_class_in_ordering('filter', post = [RowsFilters])

    class RowsRowModelWrapper(Webwidgets.FilterMod.StandardFilters.PersistentWrapper):
        """This class is a wrapper that all rows are wrapped in by
        L{RowsRowWrapperFilter}. This adds a filtering chain on
        individual rows; to override cells in a row (columns) you can
        add L{Filter}s to this class."""
        
        def ww_wrapper_key(cls, table, ww_model, **attrs):
            return "%s-%s" % (id(table), id(ww_model))
        ww_wrapper_key = classmethod(ww_wrapper_key)

        def ww_first_init(self, ww_model, *arg, **kw):
            Webwidgets.FilterMod.StandardFilters.PersistentWrapper.ww_first_init(self, ww_model = ww_model, *arg, **kw)
            self.__dict__['items'] = {}

            # FIXME: Just remove this stuff I guess? Shouldn't be used...
            if isinstance(ww_model, dict):
                self.ww_row_id = ww_model.get('ww_row_id', id(ww_model))
            else:
                self.ww_row_id = getattr(ww_model, 'ww_row_id', id(ww_model))

        class RowFilters(Webwidgets.FilterMod.Base.Filter):
            """This filter groups are ordinary filters for cells in
            the row."""

        def __getattr__(self, name):
            if isinstance(self.ww_model, dict):
                if name not in self.ww_model:
                    raise AttributeError(self.ww_model, name)
                return self.ww_model[name]
            else:
                return getattr(self.ww_model, name)

    class ExpandTreeNode(object):
        """L{get_expand_tree} returns a tree of instances of this
        class representing the currently expanded/collapsed rows."""
        
        def __init__(self, col, values = None, toggled = False, rows = None):
            self.col = col
            self.values = values or {}
            self.toggled = toggled
            self.rows = rows or {}

        def __str__(self, indent = ''):
            return '%s%s=\n%s\n' % (indent,
                                    self.col,
                                    ''.join(['%s [%s]%s:\n%s' % (indent,
                                                                 ['-', '+'][sub.toggled],
                                                                 value,
                                                                 sub.__str__(indent + '  '))
                                             for (value, sub) in self.values.iteritems()]))


    def row_common_sorted_columns(self, child, parent):
        """Calculate the number of columns two rows have in common"""
        if parent is None or child is None: return 0
        if 'ww_expanded' in parent: return 0
        total_column_order = self.get_total_column_order({}, only_sortable = True)
        if 'ww_expanded' in child: return len(total_column_order)

        level = 0
        for column in total_column_order:
            if not (    self.merge_columns_exclude == (column in self.merge_columns)
                    # This is just because virtual columns might be
                    # added at a higher level than the one where this
                    # is called.
                    and column in parent
                    and column in child
                    and (   not self.dont_merge_widgets
                         or (    not isinstance(parent[column], Webwidgets.Widgets.Base.Widget)
                             and not isinstance(child[column], Webwidgets.Widgets.Base.Widget)))
                    and parent[column] == child[column]):
                break
            level += 1
        return level

    def get_expand_tree(self):
        col_order = self.get_total_column_order({}, only_sortable = True)

        tree = self.ExpandTreeNode(col = col_order[0], toggled = not self.ww_filter.default_expand)

        for row_id, row in self.ww_filter.expand.iteritems():
            if not row['expanded_cols']:
                continue
            node = tree
            for pos in xrange(0, len(col_order) - 1): # You can not expand/collapse the last column
                col = col_order[pos]
                value = getattr(row['row'], col)
                if value not in node.values:
                    next_col = col_order[pos + 1]
                    node.values[value] = self.ExpandTreeNode(col=next_col)
                node = node.values[value]
                if col in row['expanded_cols']:
                    node.toggled = True
                    node.rows[row_id] = row['row']
        return tree

    def is_expanded_node(self, row, level):
        col = self.get_total_column_order({})[level - 1]
        row_id = self.ww_filter.get_row_id(row)
        a = (    row_id in self.ww_filter.expand
             and col in self.ww_filter.expand[row_id]['expanded_cols'])
        b = self.ww_filter.default_expand # Invert the result if default_expand is not True
        return (a and not b) or (b and not a) # a xor b 


    @Webwidgets.Utils.Cache.cache(time = "request", context="class")
    def visible_columns(self, output_options, only_sortable = False):
        # Optimisation: we could have used get_active and constructed a path...
        return Webwidgets.Utils.OrderedDict([(name, definition)
                                             for (name, definition)
                                             in self.ww_filter.get_columns(output_options, only_sortable).iteritems()
                                             if self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id,
                                                                           self.path + ['_', 'column', name])])

    def extend_to_dependent_columns(self, columns, dependent_columns):
        res = []
        for column in columns:
            res.extend([column] + dependent_columns.get(column, []))
        return res

    def get_total_column_order(self, output_options, only_sortable = False):
        visible_columns = self.visible_columns(output_options, only_sortable = only_sortable)
        total_column_order = self.extend_to_dependent_columns(
            [column for column, dir in self.ww_filter.sort],
            self.dependent_columns)
        return  [column for column in total_column_order
                 if column in visible_columns] + [column for column in visible_columns
                                                  if column not in total_column_order]

    def child_for_row(self, row):
        row_id = self.ww_filter.get_row_id(row)
        if row_id not in self.children:
            self.children[row_id] = self.RowsRowWidget(self.session, self.win_id, parent_row = row)
        return self.children[row_id]

    def draw_cell(self, row, column_name, value, output_options):
        # We're just caching child-parent relationships - if a
        # child disappears, so be it. That's up to our model, not
        # us...
        row_widget = self.child_for_row(row)
        if row_widget.children.get(column_name, None) is not value:
            row_widget.children[column_name] = value
        return row_widget.draw_child(row_widget.path + [column_name], value, output_options, True)
