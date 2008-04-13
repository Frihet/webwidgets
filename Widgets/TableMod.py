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
import Base, BaseTableMod

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
    
class Table(BaseTableMod.BaseTable, Base.ActionInput):
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
    
    class WwModel(BaseTableMod.BaseTable.WwModel):
        argument_name = None
        functions = {} # {'column_name': {'function_name': 'title'}}
        group_functions = {} # {'function_name': 'title'}
        disabled_functions = [] # ['function_name']
        disabled_columns = []
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
        button_bars_level_force_min = 0
        # A button bar is drawn if it is active, or its level is >=
        # button_bars_level_force_min or there are other button bars with
        # level < that button bars' level that are to be drawn.

    class RowsFilters(BaseTableMod.BaseTable.RowsFilters):
        WwFilters = ["TableFunctionColFilter"] + BaseTableMod.BaseTable.RowsFilters.WwFilters + ["TableSortFilter"]

        class TableFunctionColFilter(Base.Filter):
            # left = Table
            # right = Table
            def mangle_row(self, row, output_options):
                if (    'printable_version' not in output_options
                    and self.functions
                    and not hasattr(row, 'ww_expanded')):
                    for name in self.functions.iterkeys():
                        setattr(row, name, BaseTableMod.FunctionCellInstance)
                return row

            def get_rows(self, all, output_options):
                return [self.mangle_row(row, output_options)
                        for row
                        in self.ww_filter.get_rows(all, output_options)]        

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

    def field_input(self, path, string_value):
        try:
            sub_widget = self.path_to_subwidget_path(path)
        except Webwidgets.Constants.NotASubwidgetException:
            return
        if string_value != '':
            getattr(self.ww_filter, 'field_input_' + sub_widget[0])(sub_widget[1:], string_value)

    def field_input_sort(self, path, string_value):
        self.ww_filter.user_sort = string_to_sort(string_value)
    def field_input_page(self, path, string_value):
        self.page = int(string_value)
    def field_input_function(self, path, string_value):
        self.notify('function', path[0], string_value)
    def field_input_group_function(self, path, string_value):
        self.notify('group_function', path[0])
    
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
                }
            
        return (back_active or forward_active, """
<span class="left">
 <button type="submit" %(back_active)s id="%(html_id)s-_-first" name="%(html_id)s" value="%(first)s">&lt;&lt;</button>
 <button type="submit" %(back_active)s id="%(html_id)s-_-previous" name="%(html_id)s" value="%(previous)s">&lt;</button>
</span>
<span class="center">
 %(page)s/%(pages)s
</span>
<span class="right">
 <button type="submit" %(forward_active)s id="%(html_id)s-_-next" name="%(html_id)s" value="%(next)s">&gt;</button>
 <button type="submit" %(forward_active)s id="%(html_id)s-_-last" name="%(html_id)s" value="%(last)s">&gt;&gt;</button>
</span>
""" % info)

    def draw_printable_link(self, config, output_options):
        location = self.calculate_url({'widget': Webwidgets.Utils.path_to_id(self.path),
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
            if hasattr(self, 'draw_' + name):
                button_bars[name] = getattr(self, 'draw_' + name)(config, output_options)
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
 <button type="submit" id="%(html_id)s-_-sort-%(column)s" %(disabled)s name="%(html_id)s-_-sort" value="%(sort)s">%(caption)s</button>
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
    class RowsFilters(Table.RowsFilters):
        WwFilters = ["TableExpandableFilter"] + Table.RowsFilters.WwFilters

        class TableExpandableFilter(Base.Filter):
            # left = ExpandableTable
            # right = Table

            # API used by Table
            def get_rows(self, all, output_options):
                res = []
                for row in self.ww_filter.get_rows(all, output_options):
                    row.ww_filter.expand_col = BaseTableMod.ExpandCellInstance
                    res.append(row)

                    if hasattr(row.ww_filter, 'ww_expansion') and getattr(row.ww_filter, 'ww_is_expanded', False):
                        res.append(self.TableRowModelWrapper(
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

            def get_row_by_id(self, row_id):
                if row_id.startswith("child_"):
                    parent = self.ww_filter.get_row_by_id(row_id[6:])
                    return self.TableRowModelWrapper(
                        table = self.object,
                        ww_is_expansion_parent = parent,
                        ww_model = parent.ww_filter.ww_expansion)
                elif row_id.startswith("parent_"):
                    return self.ww_filter.get_row_by_id(row_id[7:])
                raise Exception("Invalid row-id %s (should have started with 'child_' or 'parent_')" % row_id)
