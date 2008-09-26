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

import Webwidgets.Constants, Webwidgets.Utils, re, math, cgi, types, itertools
import Base, BaseTableMod, Composite

column_allowed_name_re = re.compile("^[a-z_]*$")

def set_sort(sort, key):
    if sort and sort[0][0] == key:
        res = [list(key) for key in sort]
        res[0][1] = ['desc', 'asc'][res[0][1] == 'desc']
    else:
        res = [[key, 'desc']] + [orig_key for orig_key in sort
                                 if orig_key[0] != key]
    return res

def string_to_sort(str):
    if str == '': return []
    return [key.split('-') for key in str.split('.')]

def sort_to_string(sort):
    return '.'.join(['-'.join(key) for key in sort])

def sort_to_classes(sort, column):
    ww_classes = []
    for level, (key, order) in enumerate(sort):
        if key == column:
            ww_classes.append('column_sort_order_' + order)
            ww_classes.append('column_sort_level_' + str(level))
            break
    return ' '.join(ww_classes)

def sort_to_order_by(sort, quote = "`"):
    order = []
    for key, dir in sort:
        assert column_allowed_name_re.match(key) is not None
        order.append(quote + key + quote + ' ' + ['desc', 'asc'][dir == 'asc'])
    if order:
        return 'order by ' + ', '.join(order)
    return    
    
class SelectionCell(BaseTableMod.SpecialCell):
    """Draws a checkbox that lets the user add/remove the current row
    from a list of selected rows."""
    
    html_class = ['functions']

    def draw_selectbox(self, table, value, path, html_class, active, checked, output_options):
        input_id = Webwidgets.Utils.path_to_id(table.path + ['_'] + path)
        if active:
            table.session.windows[table.win_id].fields[input_id] = table
        return """<input
                   type="checkbox"
                   id="%(html_id)s"
                   class="%(html_class)s"
                   name="%(html_id)s"
                   value="%(value)s"
                   %(checked)s
                   %(disabled)s />""" % {
                   'html_id': input_id,
                   'html_class': html_class,
                   'value': value,
                   'checked': ["", 'checked="checked"'][not not checked],
                   'disabled': ['disabled="disabled"', ''][not not active]}

    def draw_table_cell(self, output_options, row, table, row_num, column_name, rowspan, colspan, first_level, last_level):
        row_id = table.ww_filter.get_row_id(row)
        return self.draw_selectbox(
            table, row_id, ['selection'], "selection",
            table.get_active(table.path + ['_', 'selection']),
            row.ww_model in table.ww_filter.selection,
            output_options)

    def __cmp__(self, other):
        return -1

SelectionCellInstance = SelectionCell()

class Table(BaseTableMod.BaseTable, Base.MixedInput):
    """Group By Ordering List is a special kind of table view that
    allows the user to sort the rows and simultaneously group the rows
    according to their content and the sorting.

    The content is provided as a list of rows, each row a dictionary
    of cell values (strings or widgets).

    The list can optionally be paged, and the application asked to
    provide the previous or next page of content uppon user input.

    In addition, the application should provide a dictionary of column
    titles and handle the resorted notigication, resorting the rows
    according to the sorting specification. Note: This is the
    responsibility of the application, as the list shown might be only
    one page of a huge set of data, so that resorting actually changes
    the content alltogether. In addition, this allows the sorting to
    be done by e.g a database back-end.
    """

    first_title = u'First page'
    previous_title = u'Previous page'
    next_title = u'Next page'
    last_title = u'Last page'

    class WwModel(BaseTableMod.BaseTable.WwModel):
        argument_name = None
        functions = {}
        """{'column_name': {'function_name': 'title'}}"""
        group_functions = {}
        """{'function_name': 'title'}"""
        disabled_functions = []
        """['function_name']"""
        disabled_columns = []
        """["column_name"]"""
        column_groups = {}
        """[column_group_name -> columnt_group_title]"""

        pre_sort = []
        sort = []
        post_sort = []
        
        button_bars = {'bottom':
                       Webwidgets.Utils.OrderedDict([('paging_buttons',  {'level': 0}),
                                                     ('printable_link',  {'level': 2,
                                                                          'title': 'Printable version'}),
                                                     ('group_functions', {'level': 1})]),
                       'top':
                       Webwidgets.Utils.OrderedDict([  #('title_bar', {'level': 2}),
                                                     ])}
        """{"position": {"button_bar_name": {"level": value, "option_name": value}}}"""
        button_bars_level_force_min = 0
        """A button bar is drawn if it is active, or its level is >=
        button_bars_level_force_min or there are other button bars with
        level < that button bars level that are to be drawn."""

        selection = []
        """Currently selected rows if a column named "selection_col" is added"""

        def __init__(self):
            super(Table.WwModel, self).__init__()
            self.selection = list(self.selection)
            
    class RowsFilters(BaseTableMod.BaseTable.RowsFilters):
        WwFilters = ["SelectionColFilter",
                     "TableFunctionColFilter"] + BaseTableMod.BaseTable.RowsFilters.WwFilters + ["TableSortFilter"]

        class SelectionColFilter(Base.Filter):
            """This filter adds a C{selection_col} column with
            selection checkboxes that the user can use to add/remove
            the current row from the L{selection} list."""
            def mangle_row(self, row, output_options):
                if 'printable_version' not in output_options:
                    setattr(row, "selection_col", SelectionCellInstance)
                return row

            def get_rows(self, output_options = {}, **kw):
                return [self.mangle_row(row, output_options)
                        for row
                        in self.ww_filter.get_rows(output_options = output_options, **kw)]
            
        class TableFunctionColFilter(Base.Filter):
            """This filter adds columns with function buttons
            according to L{functions} that can be used to let the user
            perform operations on individual rows."""
            # left = Table
            # right = Table
            def mangle_row(self, row, output_options):
                if (    'printable_version' not in output_options
                    and self.functions
                    and not hasattr(row, 'ww_expanded')):
                    for name in self.functions.iterkeys():
                        setattr(row, name, BaseTableMod.FunctionCellInstance)
                return row

            def get_rows(self, output_options = {}, **kw):
                return [self.mangle_row(row, output_options)
                        for row
                        in self.ww_filter.get_rows(output_options = output_options, **kw)]        

            def get_columns(self, output_options, only_sortable):
                if (   only_sortable
                    or (    'printable_version' in output_options
                        and self.functions)):
                    res = Webwidgets.Utils.OrderedDict(self.ww_filter.get_columns(output_options, only_sortable))
                    for key in self.functions.iterkeys():
                        if key in res:
                            del res[key]
                    return res
                else:
                    return self.ww_filter.get_columns(output_options, only_sortable)

        class TableSortFilter(Base.Filter):
            """This filter prepends L{pre_sort} and appends
            L{post_sort} to any sorting selected by the user,
            effectively overriding his/her choice for certain columns,
            and providing a default sorting order."""
            class Sort(object):
                def __get__(self, instance, owner):
                    if instance is None: instance = owner
                    return instance.pre_sort + instance.user_sort + instance.post_sort
            sort = Sort()

            class UserSort(object):
                def __get__(self, instance, owner):
                    if instance is None: instance = owner
                    return instance.ww_filter.sort
                def __set__(self, instance, value):
                    instance.ww_filter.sort = value
            user_sort = UserSort()

    def field_input(self, path, *string_values):
        try:
            sub_widget = self.path_to_subwidget_path(path)
        except Webwidgets.Constants.NotASubwidgetException:
            return
        getattr(self.ww_filter, 'field_input_' + sub_widget[0])(sub_widget[1:], *string_values)

    def field_input_expand(self, path, string_value):
        if string_value == '': return
        row_id, col = string_value.split(',')
        self.ww_filter.expand_row(row_id, col)
    def field_input_sort(self, path, string_value):
        if string_value == '': return
        self.ww_filter.user_sort = string_to_sort(string_value)
    def field_input_page(self, path, string_value):
        if string_value == '': return
        self.page = int(string_value)
    def field_input_function(self, path, string_value):
        if string_value == '': return
        self.notify('function', path[0], string_value)
    def field_input_group_function(self, path, string_value):
        if string_value == '': return
        self.notify('group_function', path[0])
    def field_input_selection(self, path, *string_values):
        if len(string_values) == 1 and not string_values[0]:
            string_values = []
        for row in self.ww_filter.get_rows():
            row_id = self.ww_filter.get_row_id(row)
            if row_id in string_values:
                if row not in self.ww_filter.selection:
                    self.ww_filter.selection.append(row.ww_model)
            else:
                if row in self.ww_filter.selection:
                    self.ww_filter.selection.remove(row.ww_model)
        
    def field_output_expand(self, path):
        return []
    def field_output(self, path):
        sub_widget = self.path_to_subwidget_path(path)
        return getattr(self.ww_filter, 'field_output_' + sub_widget[0])(sub_widget[1:])
    def field_output_sort(self, path):
        return [sort_to_string(self.ww_filter.user_sort)]
    def field_output_page(self, path):
        return [unicode(self.page)]
    def field_output_function(self, path):
        return []
    def field_output_group_function(self, path):
        return []
    def field_output_selection(self, path):
        return [self.ww_filter.get_row_id_from_row_model(row)
                for row in self.ww_filter.selection]

    def get_active_expand(self, path):
        return self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, self.path + ['expand'] + path)
    def get_active_sort(self, path):
        if path and (   path[0] in self.disabled_columns
                     or [key for (key, order) in self.ww_filter.pre_sort
                         if key == path[0]]
                     or [key for (key, order) in self.ww_filter.post_sort
                         if key == path[0]]
                     or path[0] in self.functions): return False
        return self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, self.path + ['sort'] + path)
    def get_active_page(self, path):
        return self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, self.path + ['page'] + path)
    def get_active_function(self, path):
        if path[0] in self.disabled_functions: return False
        return self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, self.path + ['function'] + path)
    def get_active_group_function(self, path):
        if path[0] in self.disabled_functions: return False
        return self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, self.path + ['group_function'] + path)
    def get_active_selection(self, path):
        return self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, self.path + ['selection'] + path)

    def draw_title_bar(self, config, output_options):
        title = getattr(self, 'title', None)
        if title is None:
            return (False, '')
        return (True, "<h1>%s</h1>" % (title,))
    
    def draw_paging_buttons(self, config, output_options):
        if self.argument_name:
            self.session.windows[self.win_id].arguments[self.argument_name + '_page'] = {
                'widget':self, 'path': self.path + ['_', 'page']}

        pages = self.ww_filter.get_pages(output_options)
        page_id = Webwidgets.Utils.path_to_id(self.path + ['_', 'page'])
        page_active = self.get_active(self.path + ['_', 'page'])
        if page_active:
            self.session.windows[self.win_id].fields[page_id] = self
        back_active = page_active and self.page > 1
        forward_active = page_active and self.page < pages
        info = {'html_id': page_id,
                'first': 1,
                'previous': self.page - 1,
                'page': self.page,
                'pages': pages,
                'next': self.page + 1,
                'last': pages,
                'back_active': ['', 'disabled="disabled"'][not back_active],
                'forward_active': ['', 'disabled="disabled"'][not forward_active],
                'first_title': self._(self.first_title, output_options),
                'previous_title': self._(self.previous_title, output_options),
                'next_title': self._(self.next_title, output_options),
                'last_title': self._(self.last_title, output_options)
                }
            
        return (back_active or forward_active, """
<span class="left">
 <button type="submit" %(back_active)s id="%(html_id)s-_-first" name="%(html_id)s" value="%(first)s" title="%(first_title)s>&lt;&lt;</button>
 <button type="submit" %(back_active)s id="%(html_id)s-_-previous" name="%(html_id)s" value="%(previous)s" title="%(previous_title)s">&lt;</button>
</span>
<span class="center">
 %(page)s/%(pages)s
</span>
<span class="right">
 <button type="submit" %(forward_active)s id="%(html_id)s-_-next" name="%(html_id)s" value="%(next)s title="%(next_title)s">&gt;</button>
 <button type="submit" %(forward_active)s id="%(html_id)s-_-last" name="%(html_id)s" value="%(last)s" title="%(last_title)s">&gt;&gt;</button>
</span>
""" % info)

    def draw_printable_link(self, config, output_options):
        location = self.calculate_url({'transaction': output_options['transaction'],
                                       'widget': Webwidgets.Utils.path_to_id(self.path),
                                       'printable_version': 'yes'})
        return (True, """<a class="printable" href="%(location)s">%(caption)s</a>""" % {
            'caption': self._(config['title'], output_options),
            'location': cgi.escape(location),
            })

    def draw_group_function(self, path, html_class, title, output_options):
        path = self.path + ['_'] + path
        active = self.get_active(path)
        if active:
            self.register_input(path)
        return """<button
                   type="submit"
                   id="%(html_id)s"
                   class="%(html_class)s"
                   %(disabled)s
                   name="%(html_id)s"
                   title="%(title)s"
                   value="selected">%(title)s</button>""" % {
                   'html_id': Webwidgets.Utils.path_to_id(path),
                   'html_class': html_class,
                   'disabled': ['disabled="disabled"', ''][active],
                   'title': self._(title, output_options)}

    def draw_group_functions(self, config, output_options):
        res = '\n'.join([self.draw_group_function(['group_function', function],
                                                  function,
                                                  title,
                                                  output_options)
                         for function, title in self.group_functions.iteritems()])
        return (res != '', res)

    def draw_buttons(self, position, output_options):
        if (   'printable_version' in output_options
            or position not in self.button_bars):
            return ''

        configs = self.button_bars[position]
        button_bars_level_min = self.button_bars_level_force_min
        button_bars = Webwidgets.Utils.OrderedDict()
        for name, config in configs.iteritems():
            if hasattr(self.ww_filter, 'draw_' + name):
                button_bars[name] = getattr(self.ww_filter, 'draw_' + name)(config, output_options)
                if button_bars[name][0]:
                     button_bars_level_min = min(config['level'], button_bars_level_min)

        button_bars_html = ''.join([html
                                    for name, (active, html) in button_bars.iteritems()
                                    if configs[name]['level'] >= button_bars_level_min])
        if not button_bars_html:
            return ''
        return "<div class='buttons'>%s</div>" % (button_bars_html,)

    def draw_headings(self, visible_columns, reverse_dependent_columns, output_options):
        sort_path = self.path + ['_', 'sort']
        headings = []
        input_id = Webwidgets.Utils.path_to_id(sort_path)
        widget_id = Webwidgets.Utils.path_to_id(self.path)

        if self.argument_name:
            self.session.windows[self.win_id].arguments[self.argument_name + '_sort'] = {
                'widget':self, 'path': sort_path}
        self.session.windows[self.win_id].fields[input_id] = self

        # Column headings
        for column, definition in visible_columns.iteritems():
            sort_active = self.get_active(sort_path + [column])
            info = {'input_id': input_id,
                    'html_id': widget_id,
                    'column': column,
                    'disabled': ['disabled="disabled"', ''][sort_active],
                    'caption': self._(definition["title"], output_options),
                    'ww_classes': sort_to_classes(self.ww_filter.sort, reverse_dependent_columns.get(column, column)),
                    'sort': sort_to_string(set_sort(self.ww_filter.user_sort, reverse_dependent_columns.get(column, column)))
                    }
            if 'printable_version' in output_options:
                headings.append("""
<th id="%(html_id)s-_-head-%(column)s" class="column %(column)s %(ww_classes)s">
 <span id="%(html_id)s-_-sort-%(column)s">%(caption)s</span>
</th>
""" % info)
            else:
                headings.append("""
<th id="%(html_id)s-_-head-%(column)s" class="column %(column)s %(ww_classes)s">
 <button type="submit" id="%(html_id)s-_-sort-%(column)s" %(disabled)s name="%(html_id)s-_-sort" value="%(sort)s title="%(caption)s">%(caption)s</button>
</th>
""" % info)

        # Group headings
        group_headings = []
        for group_row_name, group_row_def in self.column_groups.iteritems():
            group_row_headings = []
            for col_name, col_def in visible_columns.iteritems():
	        if group_row_name in col_def:
                    col_group = col_def[group_row_name]
                    if group_row_headings and group_row_headings[-1][0] == col_group:
                        group_row_headings[-1][1] += 1
                    else:
                        group_row_headings.append([col_group, 1])
                else:
                    group_row_headings.append([None, 1])
            group_headings.append(["<th colspan='%(colspan)s'>%(title)s</th>" % {
                                    'colspan': colspan,
                                    'title': group_row_def.get(group, '')
                                   }
                                  for (group, colspan)
                                  in group_row_headings])

        return group_headings + [headings]

    def append_headings(self, rows, headings, output_options):
        rows[0:0] = [{'cells': headings_row,
                      'type': BaseTableMod.RenderedRowTypeHeading}
                     for headings_row
                     in headings]

    def mangle_rendered_rows(self, rendered_rows, visible_columns, reverse_dependent_columns, output_options):
        super(Table, self).mangle_rendered_rows(rendered_rows, visible_columns, reverse_dependent_columns, output_options)

        headings = self.draw_headings(visible_columns, reverse_dependent_columns, output_options)
        self.append_headings(rendered_rows, headings, output_options)

        return rendered_rows

    def mangle_output(self, table, output_options):
        info = {'html_attributes': self.draw_html_attributes(self.path),
                'table': table,
                'buttons_top': self.draw_buttons('top', output_options),
                'buttons_bottom': self.draw_buttons('bottom', output_options)
                }
        return """
<div %(html_attributes)s>
 %(buttons_top)s
 %(table)s
 %(buttons_bottom)s
</div>
""" % info

class ExpandableTable(Table):
    """This widget allows rows to contain a "subtree row" in
    L{ww_expansion} that is inserted below the row if
    L{ww_is_expanded} is set on the row. It also adds an expand button
    that allows the user to set/reset L{ww_is_expanded}.
    """
    
    class RowsFilters(Table.RowsFilters):
        WwFilters = ["TableExpandableFilter"] + Table.RowsFilters.WwFilters

        class TableExpandableFilter(Base.Filter):
            """This filter provides the functionality of L{ExpandableTable}."""
            
            # left = ExpandableTable right = Table

            # API used by Table
            def get_rows(self, **kw):
                res = []
                for row in self.ww_filter.get_rows(**kw):
                    row.ww_filter.expand_col = BaseTableMod.ExpandCellInstance
                    res.append(row)

                    if hasattr(row.ww_filter, 'ww_expansion') and getattr(row.ww_filter, 'ww_is_expanded', False):
                        res.append(self.RowsRowModelWrapper(
                            table = self.object,
                            ww_is_expansion_parent = row,
                            ww_model = row.ww_filter.ww_expansion))
                return res

            def get_columns(self, output_options, only_sortable = False):
                if only_sortable: return self.ww_filter.get_columns(output_options, only_sortable)
                res = Webwidgets.Utils.OrderedDict(expand_col = {"title": ''})
                res.update(self.ww_filter.get_columns(output_options, only_sortable))
                return res

            def field_input_expand(self, path, string_value):
                if string_value == '': return
                row = self.object.ww_filter.get_row_by_id(string_value)
                row.ww_filter.ww_is_expanded = not getattr(row.ww_filter, 'ww_is_expanded', False)

            def field_output_expand(self, path):
                return []

            def get_active_expand(self, path):
                return self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, self.path + ['expand'] + path)

            def get_row_id(self, row):
                if hasattr(row, 'ww_is_expansion_parent'):
                    return "child_" + self.ww_filter.get_row_id(row.ww_is_expansion_parent)
                return "parent_" + self.ww_filter.get_row_id(row)

            def get_row_by_id(self, row_id, **kwargs):
                if '_' in row_id:
                    prefix, row_id = row_id.split('_', 1)

                    if prefix == "child" or kwargs.get("get_child", False):
                        parent = self.ww_filter.get_row_by_id(row_id, **kwargs)
                        return self.RowsRowModelWrapper(
                            table = self.object,
                            ww_is_expansion_parent = parent,
                            ww_model = parent.ww_filter.ww_expansion)
                    elif prefix == "parent":
                        return self.ww_filter.get_row_by_id(row_id, **kwargs)
                    
                raise Exception("Invalid row-id %s (should have started with 'child_' or 'parent_')" % row_id)

class ExpansionTable(ExpandableTable):
    """This widget allows any row to be "expanded" by inserting an
    extra row containing an instance of the L{ExpansionViewer} widget
    after the row if L{ww_is_expanded} is set on the row. It also adds
    an expand button that allows the user to set/reset
    L{ww_is_expanded}."""

    class ExpansionViewer(Base.Widget):
        """Override this member variable with any widget to display
        beneath the rows of the table as expansion."""
    
    class RowsRowModelWrapper(ExpandableTable.RowsRowModelWrapper):
        WwFilters = ["ExpansionFilter"] + ExpandableTable.RowsRowModelWrapper.WwFilters

        class ExpansionFilter(Webwidgets.Filter):
            def __init__(self, *arg, **kw):
                Webwidgets.Filter.__init__(self, *arg, **kw)
                if hasattr(self, 'is_expansion'): return
                self.ww_expansion = {
                    'is_expansion': True,
                    'ww_functions': [],
                    'ww_expanded': self.table.ExpansionViewer(
                    self.table.session, self.table.win_id,
                    parent_row = self.object)}

    def get_expansion_widget(self, row_id):
        table = self.ww_filter
        child = table.get_row_by_id(row_id,
                                    get_child = True)
        child_widget = table.child_for_row(child)
        child_widget['ww_expanded'] = child.ww_expanded
        return child_widget['ww_expanded']

class EditFunctionCell(BaseTableMod.FunctionCell):
    """Draws a set of editing buttons for a row. The set of buttons
    drawn depends on if L{is_editing} returns C{True} for the row."""
    
    html_class = ['edit_function_col']

    input_path = ['edit']

    edit_function_titles = {'edit': 'Edit',
                            'save': 'Save',
                            'revert': 'Revert',
                            'delete': 'Delete'}

    def draw_edit_function(self, table, row_id, is_editing, is_new, output_options):
        if is_editing:
            functions = ['save', 'revert']
            if not is_new:
                functions.append('delete')
        else:
            functions = ('edit', 'delete')
            
        res = ''
        for function in functions:
            res += self.draw_function(table,
                                      row_id, row_id,
                                      ['edit_function', function],
                                      function,
                                      self.edit_function_titles[function],
                                      table.get_active(table.path + ['_', 'edit_function', function]),
                                      output_options)
        return res
    
    def draw_table_cell(self, output_options, row, table, row_num, column_name, rowspan, colspan, first_level, last_level):
        row_id = table.ww_filter.get_row_id(row)
        return self.draw_edit_function(table, row_id,
                                       row.ww_filter.is_editing(), row.ww_filter.is_new(),
                                       output_options)

EditFunctionCellInstance = EditFunctionCell()

class EditableTable(Table):
    """This widget is a base class for tables that provides in-place
    editing of individual rows. The semantics provided are

    new-save
    edit-save
    edit-revert
    delete = edit-delete == new-delete == new-revert
    """
    
    class WwModel(Table.WwModel):
        edit_operations = {'edit': True,
                           'revert': True,
                           'save': True,
                           'delete': True,
                           'new': True}
        
        edit_columns = {'ww_default': True}
        edit_new_columns = {'ww_default': True}

    class RowsRowModelWrapper(Table.RowsRowModelWrapper):
        WwFilters = ["EditingFilters"] + Table.RowsRowModelWrapper.WwFilters
        class EditingFilters(Base.Filter):
            """This filter groups filters managing input fields for
            the row."""
        

    class RowsFilters(Table.RowsFilters):
        WwFilters = ["TableEditableFilter"] + Table.RowsFilters.WwFilters
    
        class TableEditableFilter(Base.Filter):
            """This filter provides a column called
            L{edit_function_col} with the editing buttons."""
            def get_rows(self, **kw):
                res = []
                for row in self.ww_filter.get_rows(**kw):
                    row.edit_function_col = EditFunctionCellInstance
                    res.append(row)
                return res

            def field_input_edit_function(self, path, string_value):
                if string_value == '': return
                row = self.object.ww_filter.get_row_by_id(string_value)
                function = path[0]	
                if function == "edit":
                    row.ww_filter.edit()
                elif function == "revert":
                    row.ww_filter.revert()
                elif function == "save":
                    row.ww_filter.save()
                elif function == "delete":
                    class Confirm(Composite.DeleteConfirmationDialog):
                        def selected(self, path, value):
                            if value == '1':
                                self.row.ww_filter.delete()
                            Composite.DeleteConfirmationDialog.selected(self, path, value)
                    Composite.DialogContainer.add_dialog_to_nearest(self, Confirm(self.session, self.win_id, row=row))
                    
            def field_output_edit_function(self, path):
                return []

            def get_active_edit_function(self, path):
                return (    self.ww_filter.edit_operations.get(path[0], False)
                        and self.session.AccessManager(Webwidgets.Constants.EDIT,
                                                       self.win_id, self.path + ['edit'] + path))

            def field_input_edit_group_function(self, path, string_value):
                if string_value == '': return
                if path[0] == "new":
                    self.pre_rows.append(self.object.ww_filter.create_new_row())

            def field_output_edit_group_function(self, path):
                return []

            def draw_edit_group_function(self, config, output_options):
                return (self.ww_filter.edit_operations['new'],
                        self.draw_group_function(['edit_group_function', "new"],
                                                 "new",
                                                 "Add new",
                                                 output_options))

            def get_active_edit_group_function(self, path):
                return (    self.ww_filter.edit_operations.get(path[0], False)
                        and self.session.AccessManager(Webwidgets.Constants.EDIT,
                                                       self.win_id, self.path + ['edit_group_function'] + path))

