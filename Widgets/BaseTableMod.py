#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Group By Ordering List for the Webwidgets web developement framework
# A list widget with intuitive grouping and sorting controls
# 
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

"""Group By Ordering List is a special kind of table view that allows
the user to sort the rows and simultaneously group the rows according
to their content and the sorting."""

import Webwidgets.Constants, Webwidgets.Utils, re, math, cgi, types, itertools
import Base

def extend_to_dependent_columns(columns, dependent_columns):
    res = []
    for column in columns:
        res.extend([column] + dependent_columns.get(column, []))
    return res

def reverse_dependency(dependent_columns):
    res = {}
    for main, dependent in dependent_columns.iteritems():
        for dependent_column in dependent:
            res[dependent_column] = main
    return res

class TableRow(Base.CachingComposite): pass

class RenderedRowType(object): pass
class RenderedRowTypeRow(RenderedRowType): pass
class RenderedRowTypeHeading(RenderedRowType): pass

class SpecialCell(object):
    """SpecialCells are like mini-widgets that can be put in multiple
    cells. They are usually singletons and should only be used when
    subclassing BaseTable, not when actually using the Table."""
    
    html_class = []
    def get_html_class(self,
        output_options, row, table,
        row_num, column_name, rowspan, colspan, first_level, last_level):
        return self.html_class
    
    def draw_cell(self, output_options, row, table, row_num, column_name, rowspan, colspan, first_level, last_level):
        return ''

class FunctionCell(SpecialCell):
    html_class = ['functions']

    def draw_function(self, table, row_id, value, path, html_class, title, active, output_options):
        input_id = Webwidgets.Utils.path_to_id(table.path + ['_'] + path)
        if active:
            table.session.windows[table.win_id].fields[input_id] = table
        return """<button
                   type="submit"
                   id="%(html_id)s-%(row)s"
                   class="%(html_class)s"
                   %(disabled)s
                   name="%(html_id)s"
                   value="%(value)s">%(title)s</button>""" % {
                       'html_id': input_id,
                       'html_class': html_class,
                       'disabled': ['disabled="disabled"', ''][active],
                       'title': table._(title, output_options),
                       'row': row_id,
                       'value': value}
                       
    def draw_cell(self, output_options, row, table, row_num, column_name, rowspan, colspan, first_level, last_level):
        enabled_functions = getattr(row, 'ww_functions', True)
        row_id = table.ww_filter.get_row_id(row)
        rendered_functions = []
        for function, title in table.functions[column_name].iteritems():
            if enabled_functions is not True and function not in enabled_functions:
                continue
            rendered_functions.append(
                self.draw_function(table, row_id, row_id,
                                   ['function', function],
                                   function, title,
                                   table.get_active(table.path + ['_', 'function', function]),
                                   output_options))
        return ''.join(rendered_functions)

    def __cmp__(self, other):
        return -1

FunctionCellInstance = FunctionCell()

class ExpandCell(FunctionCell):
    html_class = ['expand_col']

    input_path = ['expand']

    def draw_expand(self, table, row_id, value, expanded, active, output_options):
        return self.draw_function(table,
                                  row_id, value,
                                  self.input_path,
                                  ['expand', 'collapse'][expanded],
                                  ['Expand', 'Collapse'][expanded],
                                  active, output_options)
    
    def draw_cell(self, output_options, row, table, row_num, column_name, rowspan, colspan, first_level, last_level):
        row_id = table.ww_filter.get_row_id(row)
        return self.draw_expand(table, row_id, row_id,
                                getattr(row.ww_filter, 'ww_is_expanded', False),
                                table.get_active(table.path + ['_', 'expand']),
                                output_options)

ExpandCellInstance = ExpandCell()

class TableSimpleModelFilter(Base.Filter):
    # left = TablePrintableFilter
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

class TablePrintableFilter(Base.Filter):
    # left = BaseTable
    # right = TableSimpleModelFilter
    
    def get_rows(self, output_options):
        return self.ww_filter.get_rows('printable_version' in output_options, output_options)

class TableRowWrapperFilter(Base.Filter):
    def get_rows(self, all, output_options):
        return [self.TableRowModelWrapper(table = self.object, ww_model = row)
                for row in self.ww_filter.get_rows(all, output_options)]

    def get_row_id(self, row):
        return "wrap_" + self.ww_filter.get_row_id(row.ww_model)

    def get_row_by_id(self, row_id):
        if not row_id.startswith("wrap_"):
            raise Exception("Invalid row-id %s (should have started with 'wrap_')" % row_id)
        return self.TableRowModelWrapper(
            table = self.object,
            ww_model = self.ww_filter.get_row_by_id(row_id[5:]))
    
class TableRowsToTreeFilter(Base.Filter):
    """This filter creates the virtual tree of the table content,
    where rows that merges a cell with a previous row, are children of
    that previous row""" 
        
    def get_tree(self, output_options):
        total_column_order = self.get_total_column_order(output_options)
        rows = self.ww_filter.get_rows(output_options)
        tree = {'level': 0,
                'rows': 0,
                'children':[]}
        for row_num, row in enumerate(rows):
            node = tree
            node['rows'] += 1
            if hasattr(row.ww_filter, 'ww_expanded'):
                node['children'].append({'level': node['level'] + 1,
                                         'top': row_num,
                                         'rows': 1,
                                         'value': row.ww_filter.ww_expanded,
                                         'children':[]})
            else:
                for column in total_column_order:
                    col_value = getattr(row.ww_filter, column)
                    merge = (    column not in self.dont_merge_columns
                             and node['children']
                             and 'value' in node['children'][-1]
                             and (   not self.dont_merge_widgets
                                  or (    not isinstance(node['children'][-1]['value'], Base.Widget)
                                      and not isinstance(col_value, Base.Widget)))
                             and node['children'][-1]['value'] == col_value)
                    if not merge:
                        node['children'].append({'level': node['level'] + 1,
                                                 'top': row_num,
                                                 'rows': 0,
                                                 'value': col_value,
                                                 'children':[]})
                    node = node['children'][-1]
                    node['rows'] += 1
        return (rows, tree)

class BaseTable(Base.CachingComposite, Base.DirectoryServer):
    """This is the basic version of L{Table}; it formats the table
    itself, but does not include any user input controls for changing
    the sorting order, the current page, or for operating on the rows
    in the table.
    """

    class WwModel(Base.Model):
        columns = {}
        """{column_name: title | {"title":title, ...}}"""
        dependent_columns = {}
        """{column_name: [column_name]}"""
        rows = []
        sort = []
        page = 1
        expand = {}
        default_expand = True
        """If true, all rows are expanded until collapsed, if false
        all rows are collapsed until expanded. This reverses the
        meaning of the expand attribute."""
        non_memory_storage = False
        dont_merge_widgets = True
        dont_merge_columns = ()
        rows_per_page = 10
        """This attribute is not used internally by the widget, but is
        intended to be used by the user-provide reread() method."""

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
        WwFilters = [TableSimpleModelFilter]

    class RowsFilters(Base.Filter):
        WwFilters = [TableRowWrapperFilter]

    class OutputOptionsFilters(Base.Filter):
        WwFilters = [TablePrintableFilter]

    class TreeFilters(Base.Filter):
        WwFilters = [TableRowsToTreeFilter]

    WwFilters = ["TreeFilters", "OutputOptionsFilters", "RowsFilters", "SourceFilters"]

    class TableRowModelWrapper(Base.PersistentWrapper):
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

    def is_expanded_node(self, row, level):
        col = self.get_total_column_order({})[level - 1]
        row_id = self.ww_filter.get_row_id(row)
        a = (    row_id in self.ww_filter.expand
             and col in self.ww_filter.expand[row_id]['expanded_cols'])
        b = self.ww_filter.default_expand # Invert the result if default_expand is not True
        return (a and not b) or (b and not a) # a xor b 

    class ExpandTreeNode(object):
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

    def row_common_sorted_columns(self, child, parent):
        """Calculate the number of columns two rows have in common"""
        if parent is None or child is None: return 0
        if 'ww_expanded' in parent: return 0
        total_column_order = self.get_total_column_order({}, only_sortable = True)
        if 'ww_expanded' in child: return len(total_column_order)

        level = 0
        for column in total_column_order:
            if not (    column not in self.dont_merge_columns
                    # This is just because virtual columns might be
                    # added at a higher level than the one where this
                    # is called.
                    and column in parent
                    and column in child
                    and (   not self.dont_merge_widgets
                         or (    not isinstance(parent[column], Base.Widget)
                             and not isinstance(child[column], Base.Widget)))
                    and parent[column] == child[column]):
                break
            level += 1
        return level
    
    def get_active(self, path):
        """@return: Whether the widget is allowing the user to acces
        a given part of it or not.
        """
        
        widget_path = self.path
        sub_widget = self.path_to_subwidget_path(path)

        if not self.active: return False
        return getattr(self.ww_filter, 'get_active_' + sub_widget[0])(sub_widget[1:])

    def get_active_column(self, path):
        return self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id, self.path + ['column'] + path)

    def visible_columns(self, output_options, only_sortable = False):
        # Optimisation: we could have used get_active and constructed a path...
        return Webwidgets.Utils.OrderedDict([(name, definition)
                                             for (name, definition)
                                             in self.ww_filter.get_columns(output_options, only_sortable).iteritems()
                                             if self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id,
                                                                           self.path + ['_', 'column', name])])

    def get_total_column_order(self, output_options, only_sortable = False):
        visible_columns = self.visible_columns(output_options, only_sortable = only_sortable)
        total_column_order = extend_to_dependent_columns(
            [column for column, dir in self.ww_filter.sort],
            self.dependent_columns)
        return  [column for column in total_column_order
                 if column in visible_columns] + [column for column in visible_columns
                                                  if column not in total_column_order]

    def draw_tree(self, node, rows, output_options, first_level = 0, last_level = 0, single = False):
        total_column_order = self.ww_filter.get_total_column_order(output_options)
        visible_columns = self.visible_columns(output_options)
        if node['children']:
            rendered_rows = []
            children = len(node['children'])
            for child in xrange(0, children):
                sub_first = first_level
                sub_last = last_level
                if child != 0:
                    sub_first += 1
                if child != children - 1:
                    sub_last += 1
                rendered_rows.extend(self.draw_tree(node['children'][child],
                                                    rows,
                                                    output_options,
                                                    sub_first, sub_last,
                                                    single or node['rows'] == 1
                                                    ))
        else:
            rendered_rows = []
            for row in xrange(node['top'], node['top'] + node['rows']):
                rendered_rows.append({'cells':[''] * len(visible_columns),
                                      'type': RenderedRowTypeRow,
                                      'row': rows[row]})
        row = rendered_rows[0]['row']
        if 'value' in node:
            if hasattr(row, 'ww_expanded'):
                rendered_rows[0]['cells'] = [
                    self.draw_extended_row(
                    output_options, row, node['value'],
                    total_column_order, node['top'], first_level, last_level, node['level'], single)]
            else:
                column = total_column_order[node['level'] - 1]
                column_position = visible_columns.keys().index(column)
                rendered_rows[0]['cells'][column_position] = self.draw_node(
                    output_options, row, node,
                    column, first_level, last_level, node['level'], single)
        return rendered_rows

    def draw_node(self, output_options, row, node, column, first_level, last_level, node_level, single):
        return self.draw_cell(
            output_options, row, node['value'], node['top'], column, node['rows'], 1, first_level, last_level, node_level, single)

    def draw_extended_row(self, output_options, row, value, total_column_order, row_num, first_level, last_level, node_level, single):
        return self.draw_cell(
            output_options, row, value, row_num, 'ww_expanded', 1, len(total_column_order), first_level, last_level, node_level, single)

    def draw_cell(self, output_options, row, value,
                  row_num, column_name, rowspan, colspan, first_level, last_level, node_level, single):
        html_class = []
        if isinstance(value, SpecialCell):
            html_class = value.get_html_class(
                output_options, row, self,
                row_num, column_name, rowspan, colspan, first_level, last_level)
            value = value.draw_cell(
                output_options, row, self,
                row_num, column_name, rowspan, colspan, first_level, last_level)
        else:
            html_class = getattr(row, 'ww_class', []) + ['column_first_level_%s' % first_level,
                                                         'column_last_level_%s' % last_level]
            # We're just caching child-parent relationships - if a
            # child disappears, so be it. That's up to our model, not
            # us...
            row_widget = self.child_for_row(row)
            if row_widget.children.get(column_name, None) is not value:
                row_widget.children[column_name] = value
            value = row_widget.draw_child(row_widget.path + [column_name], value, output_options, True)

        expand_button = ""
        expanded = self.ww_filter.is_expanded_node(row, node_level)
        if rowspan > 1 or (not expanded and not single):
            row_id = self.ww_filter.get_row_id(row)
            expand_button = ExpandCellInstance.draw_expand(
                self,
                row_id,
                '%s,%s' % (row_id, column_name),
                expanded, True, output_options)
            
        return '<td rowspan="%(rowspan)s" colspan="%(colspan)s" class="%(class)s">%(expand_button)s%(content)s</td>' % {
            'rowspan': rowspan,
            'colspan': colspan,
            'class': ' '.join(html_class),
            'expand_button': expand_button,
            'content': value}

    def child_for_row(self, row):
        row_id = self.ww_filter.get_row_id(row)
        if row_id not in self.children:
            self.children[row_id] = TableRow(self.session, self.win_id)
        return self.children[row_id]

    def draw_rows(self, visible_columns, reverse_dependent_columns, output_options):
        rows, tree = self.ww_filter.get_tree(output_options)

        # Why we need this test here: rows_to_tree would create an empty
        # top-node for an empty set of rows, which draw_tree would
        # render into a single row...
        if rows:
            rendered_rows = self.draw_tree(tree,
                                           rows,
                                           output_options)
        else:
            rendered_rows = []
        return rendered_rows

    def append_classes(self, rendered_rows, output_options):
        for row_num, rendered_row in enumerate(rendered_rows):
            rendered_row['class'] = (  ['row_' + ['even', 'odd'][row_num % 2]]
                                     + getattr(rendered_row['row'], 'ww_class', []))

    def mangle_rendered_rows(self, rendered_rows, visible_columns, reverse_dependent_columns, output_options):
        self.append_classes(rendered_rows, output_options)
        return rendered_rows

    def draw_table(self, rendered_rows, output_options):
        return "<table>%s</table>" % '\n'.join(['<tr class="%s">%s</tr>' % (' '.join(row.get('class', [])),
                                                                            ''.join(row.get('cells', [])))
                                                for row in rendered_rows])
    
    def mangle_output(self, table, output_options):
        return table

    def draw(self, output_options):
        self.register_style_link(self.calculate_url({'widget_class': 'Webwidgets.BaseTable',
                                                     'location': ['Table.css']},
                                                    {}))
        reverse_dependent_columns = reverse_dependency(self.dependent_columns)
        visible_columns = self.visible_columns(output_options)

        return self.mangle_output(
            self.draw_table(
                self.mangle_rendered_rows(
                    self.draw_rows(visible_columns, reverse_dependent_columns, output_options),
                    visible_columns, reverse_dependent_columns, output_options),
                output_options),
            output_options)

    def output(self, output_options):
        return {Webwidgets.Constants.OUTPUT: self.draw_printable_version(output_options),
               'Content-type': 'text/html'
               }

    def draw_printable_version(self, output_options):
        return self.session.windows[self.win_id].draw(output_options,
                                                     body = self.draw(output_options),
                                                     title = self.title)
