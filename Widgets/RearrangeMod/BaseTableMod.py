#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

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

import re, math, cgi, types, itertools
import Webwidgets.Constants
import Webwidgets.Utils
import Webwidgets.FilterMod.StandardFilters
import Webwidgets.Widgets.Base
import Webwidgets.Widgets.ApplicationMod.WindowMod
import Webwidgets.Widgets.RowsMod

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
    
    def draw_table_cell(self, output_options, row, table, row_num, column_name, rowspan, colspan, first_level, last_level):
        return ''

class FunctionCell(SpecialCell):
    """Draws a function button that when clicked operates on the
    current row in some fashion."""
    
    html_class = ['functions']

    def draw_function(self, table, row_id, value, path, html_class, title, active, output_options):
        input_path = table.path + ['_'] + path
        if active:
            table.register_input(input_path)
        return """<button
                   type="submit"
                   id="%(html_id)s"
                   class="%(html_class)s"
                   %(disabled)s
                   name="%(html_id)s"
                   title="%(title)s"
                   value="%(value)s"><span class='button-text'>%(title)s</span></button>""" % {
                       'html_id': Webwidgets.Utils.path_to_id(input_path),
                       'html_class': html_class + [' ww-disabled', ''][active],
                       'disabled': ['disabled="disabled"', ''][active],
                       'title': table._(title, output_options),
                       'value': value}
                       
    def draw_table_cell(self, output_options, row, table, row_num, column_name, rowspan, colspan, first_level, last_level):
        enabled_functions = getattr(row.ww_filter, 'ww_functions', True)
        row_id = table.ww_filter.get_row_id(row)
        rendered_functions = []
        for function, title in table.functions[column_name].iteritems():
            if enabled_functions is not True and function not in enabled_functions:
                continue
            sub_path = ['function', function, row_id]
            rendered_functions.append(
                self.draw_function(table, row_id, row_id,
                                   sub_path,
                                   function, title,
                                   table.get_active(table.path + ['_'] + sub_path),
                                   output_options))
        return ''.join(rendered_functions)

    def __cmp__(self, other):
        return -1

FunctionCellInstance = FunctionCell()

class ExpandCell(FunctionCell):
    """Draws an expansion/collapse button that lets the user show/hide
    a subtree under the current row."""
    
    html_class = ['expand_col']

    input_path = ['expand']

    def draw_expand(self, table, row_id, value, expanded, active, output_options):
        return self.draw_function(table,
                                  row_id, value,
                                  self.input_path,
                                  ['expand', 'collapse'][expanded],
                                  ['Expand', 'Collapse'][expanded],
                                  active, output_options)
    
    def draw_table_cell(self, output_options, row, table, row_num, column_name, rowspan, colspan, first_level, last_level):
        row_id = table.ww_filter.get_row_id(row)
        return self.draw_expand(table, row_id, row_id,
                                getattr(row.ww_filter, 'ww_is_expanded', False),
                                table.get_active(table.path + ['_', 'expand']),
                                output_options)

ExpandCellInstance = ExpandCell()

class TableRowsToTreeFilter(Webwidgets.FilterMod.Base.Filter):
    """This filter creates the virtual tree of the table content,
    where rows that merges a cell with a previous row, are children of
    that previous row""" 
        
    def get_tree(self, output_options):
        total_column_order = self.get_total_column_order(output_options)
        rows = self.ww_filter.get_rows(output_options = output_options)
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
                    merge = (    self.merge_columns_exclude == (column in self.merge_columns)
                             and node['children']
                             and 'value' in node['children'][-1]
                             and (   not self.dont_merge_widgets
                                  or (    not isinstance(node['children'][-1]['value'], Webwidgets.Widgets.Base.Widget)
                                      and not isinstance(col_value, Webwidgets.Widgets.Base.Widget)))
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

class BaseTable(Webwidgets.Widgets.RowsMod.RowsComposite, Webwidgets.Widgets.Base.DirectoryServer):
    """This is the basic version of L{Table}; it formats the table
    itself, but does not include any user input controls for changing
    the sorting order, the current page, or for operating on the rows
    in the table.
    """

    class WwModel(Webwidgets.Widgets.RowsMod.RowsComposite.WwModel):
        allow_collapse_columns = ()
        """List of columns that the user can collapse/expand if allow_collapse_columns_exclude = False or
        not if True"""
        allow_collapse_columns_exclude = True
        """If False, allow collapse/expand for columns in allow_collapse_columns, if True allow for all
        but the ones in allow_collapse_columns"""        

        cache_html_output = False
        """If set, HTML output is cached as long as
        self.ww_filter.needs_refresh() returns False. This is a BAD
        idea if your table contains other widgets..."""
        html_output_cache = None

    class SourceFilters(Webwidgets.Widgets.RowsMod.RowsComposite.SourceFilters):
        class HtmlCacheFilter(Webwidgets.FilterMod.Base.Filter):
            def reread(self):
                self.html_output_cache = None
                self.ww_filter.reread()
        HtmlCacheFilter.add_class_in_ordering('filter', pre = Webwidgets.Widgets.RowsMod.RowsComposite.SourceFilters.ww_filter_last)

    empty_table_message = """There is no data in this table / no entries matched your search."""

    class TreeFilters(Webwidgets.FilterMod.Base.Filter):
        """This filter groups filters that mangle the virtual tree of
        rows (that has merged cells, according to the current sorting
        order)."""
        class TableRowsToTreeFilter(TableRowsToTreeFilter): pass
    TreeFilters.add_class_in_ordering('filter', post = Webwidgets.Widgets.RowsMod.RowsComposite.ww_filter_first)

    def get_active(self, path):
        """@return: Whether the widget is allowing the user to acces
        a given part of it or not.
        """
        
        widget_path = self.path

        if '_' not in path:
            return self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id, path)

        sub_widget = self.path_to_subwidget_path(path)

        if not self.active: return False
        return getattr(self.ww_filter, 'get_active_' + sub_widget[0])(sub_widget[1:])

    def get_active_column(self, path):
        return self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id, self.path + ['column'] + path)

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
        return self.draw_table_cell(
            output_options, row, node['value'], node['top'], column, node['rows'], 1, first_level, last_level, node_level, single)

    def draw_extended_row(self, output_options, row, value, total_column_order, row_num, first_level, last_level, node_level, single):
        return self.draw_table_cell(
            output_options, row, value, row_num, 'ww_expanded', 1, len(total_column_order), first_level, last_level, node_level, single)

    def draw_table_cell(self, output_options, row, value,
                  row_num, column_name, rowspan, colspan, first_level, last_level, node_level, single):
        html_class = []
        if isinstance(value, SpecialCell):
            html_class = value.get_html_class(
                output_options, row, self,
                row_num, column_name, rowspan, colspan, first_level, last_level)
            value = value.draw_table_cell(
                output_options, row, self,
                row_num, column_name, rowspan, colspan, first_level, last_level)
        else:
            html_class = getattr(row, 'ww_class', []) + ['column_first_level_%s' % first_level,
                                                         'column_last_level_%s' % last_level]
            value = self.draw_cell(row, column_name, value, output_options)

        expand_button = ""
        expanded = self.ww_filter.is_expanded_node(row, node_level)
        if (   (not expanded and not single)
            or (    rowspan > 1
                and self.ww_filter.allow_collapse_columns_exclude == (column_name not in self.ww_filter.allow_collapse_columns))):            
            row_id = self.ww_filter.get_row_id(row)
            expand_button = ExpandCellInstance.draw_expand(
                self,
                row_id,
                '%s,%s' % (row_id, column_name),
                expanded, True, output_options)

        # FIXME: Remove base classes of this class from list.
        html_class = html_class + [Webwidgets.Utils.classes_to_css_classes(self.ww_classes, ['column', column_name])]
        
        return '<td rowspan="%(rowspan)s" colspan="%(colspan)s" class="%(class)s">%(expand_button)s%(content)s</td>' % {
            'rowspan': rowspan,
            'colspan': colspan,
            'class': ' '.join(html_class),
            'expand_button': expand_button,
            'content': value}

    def draw_rows(self, visible_columns, reverse_dependent_columns, output_options):
        rows, tree = self.ww_filter.get_tree(output_options)

        # Why we need this test here: rows_to_tree would create an empty
        # top-node for an empty set of rows, which draw_tree would
        # render into a single row with empty cells...
        if rows:
            rendered_rows = self.draw_tree(tree,
                                           rows,
                                           output_options)
        else:
            rendered_rows = [{'cells': ["<td colspan='%(colspan)s' class='empty_table_message'>%(message)s</td>" % {
                                            'colspan': len(visible_columns),
                                            'message': self._(self.empty_table_message, output_options)
                                            }],
                              'row': {}}]
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

    def reverse_dependency(self, dependent_columns):
        res = {}
        for main, dependent in dependent_columns.iteritems():
            for dependent_column in dependent:
                res[dependent_column] = main
        return res

    def draw_uncached(self, output_options):
        reverse_dependent_columns = self.reverse_dependency(self.dependent_columns)
        visible_columns = self.visible_columns(output_options)

        return self.mangle_output(
            self.draw_table(
                self.mangle_rendered_rows(
                    self.draw_rows(visible_columns, reverse_dependent_columns, output_options),
                    visible_columns, reverse_dependent_columns, output_options),
                output_options),
            output_options)

    def draw_cached(self, output_options):
        return self.ww_filter.html_output_cache

    def draw(self, output_options):
        Webwidgets.Widgets.ApplicationMod.WindowMod.HtmlWindow.register_style_link(self, self.calculate_url({'transaction': output_options['transaction'],
                                                     'widget_class': 'Webwidgets.BaseTable',
                                                     'location': ['Table.css']},
                                                    {}))
        
        if self.ww_filter.cache_html_output:            
            print "TABLE CACHED"
            # Reset the cache if it needs refresh (this will reread
            # the rows in that case too, but it would be done later
            # anyway, so we're just hastening it :)
            self.ww_filter.ensure()
            if self.ww_filter.html_output_cache is None:
                print "TABLE CACHE REFRESH"
                self.ww_filter.html_output_cache = self.draw_uncached(output_options)
                return self.ww_filter.html_output_cache
            else:
                return self.draw_cached(output_options)
        else:
            return self.draw_uncached(output_options)

    def output(self, output_options):
        return {Webwidgets.Constants.OUTPUT: self.draw_printable_version(output_options),
               'Content-type': 'text/html'
               }

    def draw_printable_version(self, output_options):
        return self.session.windows[self.win_id].draw(output_options,
                                                     body = self.draw(output_options),
                                                     title = self.title)
