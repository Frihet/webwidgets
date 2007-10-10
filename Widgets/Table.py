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

import Webwidgets.Constants, Webwidgets.Utils, re, math, cgi
import Base

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
    return ''

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

class ChildNodeCells(Base.ChildNodes):
    def __init__(self, node, row, *arg, **kw):
        self.row = row
        super(ChildNodeCells, self).__init__(node, *arg, **kw)

    def ensure(self):
        for name in self.iterkeys():
            value = self[name]
            if isinstance(value, type) and issubclass(value, Base.Widget):
                value = self[name] = value(self.node.session, self.node.win_id)
            if isinstance(value, Base.Widget):
                value.parent = self.node
                value.name = "cell_%s_%s" % (self.row, name)

class ChildNodeRows(list):
    def __init__(self, node, *arg, **kw):
        super(ChildNodeRows, self).__init__(*arg, **kw)
        self.node = node
        self.ensure()
    
    def ensure(self):
        for index in xrange(0, len(self)):
            if not isinstance(self[index], ChildNodeCells) or self[index].row != index:
                self[index] = ChildNodeCells(self.node, index, self[index])

    def __setitem__(self, *arg, **kw):
        super(ChildNodeRows, self).__setitem__(*arg, **kw)
        self.ensure()

    def __delitem__(self, *arg, **kw):
        super(ChildNodeRows, self).__delitem__(*arg, **kw)
        self.ensure()

    def __setslice__(self, *arg, **kw):
        super(ChildNodeRows, self).__setslice__(*arg, **kw)
        self.ensure()

    def extend(self, *arg, **kw):
        super(ChildNodeRows, self).extend(*arg, **kw)
        self.ensure()

    def append(self, *arg, **kw):
        super(ChildNodeRows, self).append(*arg, **kw)
        self.ensure()

    def insert(self, *arg, **kw):
        super(ChildNodeRows, self).insert(*arg, **kw)
        self.ensure()

    def reverse(self, *arg, **kw):
        super(ChildNodeRows, self).reverse(*arg, **kw)
        self.ensure()
    
    def sort(self, *arg, **kw):
        super(ChildNodeRows, self).sort(*arg, **kw)
        self.ensure()
  
class Table(Base.ActionInput, Base.Composite):
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
    
    columns = {}
    argument_name = None
    dependent_columns = {}
    functions = {}
    group_functions = {}
    disabled_functions = []
    function_position = 0
    sort = []
    rows = []
    page = 1
    pages = 1
    non_memory_storage = False
    dont_merge_widgets = True
    dont_merge_columns = ()
    old_sort = []
    rows_per_page = 10
    """This attribute is not used internally by the widget, but is
    intended to be used by the user-provide reread() method."""

    def __init__(self, session, win_id, **attrs):
        Base.Composite.__init__(self, session, win_id, **attrs)
        self.rows = ChildNodeRows(self, self.rows)
        self.reread()

#     def function(self, path, function, row):
#         raise Exception('%s: Function %s not implemented (called for row %s)' % (Webwidgets.Utils.path_to_id(path), function, row))

#     def group_function(self, path, function):
#         raise Exception('%s: Function %s not implemented' % (Webwidgets.Utils.path_to_id(path), function))

    def reread(self):
        """Reload the list after a repaging/resorting here. This is
        not a notification to allow for it to be called from __init__.

        If you set non_memory_storage to True, you _must_ override this
        method with your own sorter/loader function.
        """
        def row_cmp(row1, row2):
            for col, order in self.sort:
                diff = cmp(row1[col], row2[col])
                if diff:
                    if order == 'desc': diff *= -1
                return diff
            return 0
        
        if self.sort != self.old_sort:
            self.rows.sort(row_cmp)
            self.old_sort = self.sort

    def sort_changed(self, path, sort):
        """Notification that the list sort order has changed."""
        if path != self.path: return
        self.reread()

    def page_changed(self, path, page):
        """Notification that the user has changed page."""
        if path != self.path: return
        self.reread()

    def get_all_rows(self):
        return self.rows
    
    def get_rows(self):
        if self.non_memory_storage:
            return self.rows
        return self.rows[(self.page - 1) * self.rows_per_page:
                         self.page * self.rows_per_page]

    def get_pages(self):
        if self.non_memory_storage:
            return self.pages        
        return int(math.ceil(float(len(self.rows)) / self.rows_per_page))

    def get_children(self):
        raise NotImplemented

    def get_child(self, name):
        dummy, row, column = name.split('_')
        row = int(row)
        return self.rows[row][column]
    
    def get_widgets_by_attribute(self, attribute = '__name__'):
        fields = Base.Widget.get_widgets_by_attribute(self, attribute)
        for row in self.get_rows():
            for column, child in row.iteritems():
                if isinstance(child, Base.Widget):
                    fields.update(child.get_widgets_by_attribute(attribute))
        return fields

    def field_input(self, path, string_value):
        widget_path = self.path
        try:
            sub_widget = self.path_to_subwidget_path(path)
        except Webwidgets.Constants.NotASubwidgetException:
            return
        
        if sub_widget == ['sort']:
            if string_value != '':
                self.sort = string_to_sort(string_value)
        elif sub_widget == ['page']:
            if string_value != '':
                self.page = int(string_value)
        elif sub_widget[0] == 'function':
            if string_value != '':
                self.notify('function', sub_widget[1], int(string_value))
        elif sub_widget[0] == 'group_function':
            if string_value != '':
                self.notify('group_function', sub_widget[1])
    
    def field_output(self, path):
        widget_path = self.path
        sub_widget = self.path_to_subwidget_path(path)
        
        if sub_widget == ['sort']:
            return [sort_to_string(self.sort)]
        elif sub_widget == ['page']:
            return [unicode(self.page)]
        elif sub_widget[0] == 'function':
            return []
        elif sub_widget[0] == 'group_function':
            return []
        else:
            raise Exception('Unknown sub-widget %s in %s' %(sub_widget, widget_path))

    def get_active(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        widget_path = self.path
        sub_widget = self.path_to_subwidget_path(path)

        if not self.active: return False

        if sub_widget == ['sort'] or sub_widget == ['page']:
            return self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, path)
        elif sub_widget[0] == 'column':
            return self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id, path)
        elif sub_widget[0] == 'function':
            if sub_widget[1] in self.disabled_functions: return False
            return self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, path)
        elif sub_widget[0] == 'group_function':
            if sub_widget[1] in self.disabled_functions: return False
            return self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, path)
        else:
            raise Exception('Unknown sub-widget %s in %s' %(sub_widget, widget_path))

    def visible_columns(self):
        # Optimisation: we could have used get_active and constructed a path...
        return Webwidgets.Utils.OrderedDict([(name, description) for (name, description) in self.columns.iteritems()
                                  if self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id,
                                                                self.path + ['_', 'column', name])])

    def rows_to_tree(self, rows, group_order):
        tree = {'level': 0,
                'rows': 0,
                'children':[]}
        for row_num in xrange(0, len(rows)):
            row = rows[row_num]
            node = tree
            node['rows'] += 1
            for column in group_order:
                merge = (    column not in self.dont_merge_columns
                         and node['children']
                         and (   not self.dont_merge_widgets
                              or (    not isinstance(node['children'][-1]['value'], Base.Widget)
                                  and not isinstance(row[column], Base.Widget)))
                         and node['children'][-1]['value'] == row[column])
                if not merge:
                    node['children'].append({'level': node['level'] + 1,
                                             'top': row_num,
                                             'rows': 0,
                                             'value': row[column],
                                             'children':[]})
                node = node['children'][-1]
                node['rows'] += 1
        return tree

    def draw_tree(self, node, output_options, group_order, visible_columns, first_level = 0, last_level = 0):
        if node['children']:
            rows = []
            children = len(node['children'])
            for child in xrange(0, children):
                sub_first = first_level
                sub_last = last_level
                if child != 0:
                    sub_first += 1
                if child != children - 1:
                    sub_last += 1
                rows.extend(self.draw_tree(node['children'][child],
                                          output_options,
                                          group_order, visible_columns,
                                          sub_first, sub_last))
        else:
            rows = []
            for row in xrange(0, node['rows']):
                rows.append([''] * len(visible_columns))
        if 'value' in node:
            column = group_order[node['level'] - 1]
            rows[0][visible_columns.keys().index(column)
                    ] = self.draw_node(output_options, node, column, first_level, last_level)
        return rows

    def draw_node(self, output_options, node, column, first_level, last_level):
        return self.draw_cell(output_options, node['value'], node['top'], column, node['rows'], first_level, last_level)
        
    def draw_cell(self, output_options, value, row, column, rowspan, first_level, last_level):
        return '<td rowspan="%(rowspan)s" class="%(class)s">%(content)s</td>' % {
            'rowspan': rowspan,
            'class': 'column_first_level_%s column_last_level_%s' % (first_level, last_level),
            'content': self.draw_child(self.path + ["cell_%s_%s" % (row, column)],
                                      value, output_options, True)}

    def draw_paging_buttons(self, output_options):
        if self.argument_name:
            self.session.windows[self.win_id].arguments[self.argument_name + '_page'] = {
                'widget':self, 'path': self.path + ['_', 'page']}

        page_id = Webwidgets.Utils.path_to_id(self.path + ['_', 'page'])
        page_active = self.get_active(self.path + ['_', 'page'])
        if page_active:
            self.session.windows[self.win_id].fields[page_id] = self
        info = {'attr_html_id': page_id,
                'first': 1,
                'previous': self.page - 1,
                'page': self.page,
                'pages': self.get_pages(),
                'next': self.page + 1,
                'last': self.get_pages(),
                'back_active': ['', 'disabled="disabled"'][not page_active or self.page <= 1],
                'forward_active': ['', 'disabled="disabled"'][not page_active or self.page >= self.get_pages()],
                }
            
        return """
<span class="left">
 <button type="submit" %(back_active)s id="%(attr_html_id)s-_-first" name="%(attr_html_id)s" value="%(first)s">&lt;&lt;</button>
 <button type="submit" %(back_active)s id="%(attr_html_id)s-_-previous" name="%(attr_html_id)s" value="%(previous)s">&lt;</button>
</span>
<span class="center">
 %(page)s/%(pages)s
</span>
<span class="right">
 <button type="submit" %(forward_active)s id="%(attr_html_id)s-_-next" name="%(attr_html_id)s" value="%(next)s">&gt;</button>
 <button type="submit" %(forward_active)s id="%(attr_html_id)s-_-last" name="%(attr_html_id)s" value="%(last)s">&gt;&gt;</button>
</span>
""" % info

    def draw_printable_link(self, output_options):
        location = self.calculate_url({'widget': Webwidgets.Utils.path_to_id(self.path),
                                      'printable_version': 'yes'})
        return """<a class="printable" href="%(location)s">%(caption)s</a>""" % {
            'caption': self._("Printable version", output_options),
            'location': cgi.escape(location),
            }

    def draw_group_functions(self, output_options):
        function_active = {}
        for function in self.group_functions:
            function_active[function] = self.get_active(self.path + ['_', 'group_function', function])

        for function in self.group_functions:
            if function_active[function]:
                self.session.windows[self.win_id].fields[Webwidgets.Utils.path_to_id(self.path + ['_', 'group_function', function])] = self

        return '\n'.join([
            """<button
                type="submit"
                id="%(attr_html_id)s"
                class="%(attr_html_class)s"
                %(disabled)s
                name="%(attr_html_id)s"
                value="selected">%(title)s</button>""" % {'attr_html_id': Webwidgets.Utils.path_to_id(self.path + ['_', 'group_function', function]),
                                                          'attr_html_class': function,
                                                          'disabled': ['disabled="disabled"', ''][function_active[function]],
                                                          'title': self._(title, output_options)}
            for function, title in self.group_functions.iteritems()])

    def draw_buttons(self, output_options):
        if 'printable_version' in output_options:
            return ''
        return """
<div class="buttons">
 %(paging_puttons)s
 %(printable_link)s
 %(group_functions)s
</div>
""" % {'paging_puttons': self.draw_paging_buttons(output_options),
       'printable_link': self.draw_printable_link(output_options),
       'group_functions': self.draw_group_functions(output_options)}

    def draw_headings(self, visible_columns, reverse_dependent_columns, output_options):
        if self.argument_name:
            self.session.windows[self.win_id].arguments[self.argument_name + '_sort'] = {
                'widget':self, 'path': self.path + ['_', 'sort']}

        sort_active = self.get_active(self.path + ['_', 'sort'])
        headings = []
        input_id = Webwidgets.Utils.path_to_id(self.path + ['_', 'sort'])
        widget_id = Webwidgets.Utils.path_to_id(self.path)
        if sort_active:
            self.session.windows[self.win_id].fields[input_id] = self
        for column, title in visible_columns.iteritems():
            info = {'input_id': input_id,
                    'attr_html_id': widget_id,
                    'column': column,
                    'disabled': ['disabled="disabled"', ''][sort_active],
                    'caption': self._(title, output_options),
                    'ww_classes': sort_to_classes(self.sort, reverse_dependent_columns.get(column, column)),
                    'sort': sort_to_string(set_sort(self.sort, reverse_dependent_columns.get(column, column)))
                    }
            if 'printable_version' in output_options:
                headings.append("""
<th id="%(attr_html_id)s-_-head-%(column)s" class="column %(ww_classes)s">
 <span id="%(attr_html_id)s-_-sort-%(column)s">%(caption)s</span>
</th>
""" % info)
            else:
                headings.append("""
<th id="%(attr_html_id)s-_-head-%(column)s" class="column %(ww_classes)s">
 <button type="submit" id="%(attr_html_id)s-_-sort-%(column)s" %(disabled)s name="%(attr_html_id)s-_-sort" value="%(sort)s">%(caption)s</button>
</th>
""" % info)
        return headings

    def append_functions(self, rows, headings, output_options):
        if 'printable_version' not in output_options and self.functions:
            function_position = self.function_position
            if function_position < 0:
                function_position += 1
                if function_position == 0: 
                    function_position = len(headings)
            
            function_active = {}
            for function in self.functions:
                function_active[function] = self.get_active(self.path + ['_', 'function', function])

            for function in self.functions:
                if function_active[function]:
                    self.session.windows[self.win_id].fields[Webwidgets.Utils.path_to_id(self.path + ['_', 'function', function])] = self
            for row_num in xrange(0, len(rows)):
                functions = '<td class="functions">%s</td>' % ''.join([
                    """<button
                        type="submit"
                        id="%(attr_html_id)s-%(row)s"
                        class="%(attr_html_class)s"
                        %(disabled)s
                        name="%(attr_html_id)s"
                        value="%(row)s">%(title)s</button>""" % {'attr_html_id': Webwidgets.Utils.path_to_id(self.path + ['_', 'function', function]),
                                                                 'attr_html_class': function,
                                                                 'disabled': ['disabled="disabled"', ''][function_active[function]],
                                                                 'title': self._(title, output_options),
                                                                 'row': row_num}
                    for function, title in self.functions.iteritems()])
                rows[row_num].insert(function_position, functions)
    
            headings.insert(function_position, '<th></th>')

    def draw_table(self, headings, rows, output_options):
        return "<table>%(headings)s%(content)s</table>" % {
            'headings': '<tr>%s</tr>' % (' '.join(headings),),
            'content': '\n'.join(['<tr>%s</tr>' % (''.join(row),) for row in rows])}
            
    def draw(self, output_options):
        widget_id = Webwidgets.Utils.path_to_id(self.path)

        reverse_dependent_columns = reverse_dependency(self.dependent_columns)
        visible_columns = self.visible_columns()

        group_order = extend_to_dependent_columns(
            [column for column, dir in self.sort],
            self.dependent_columns)
        group_order = [column for column in group_order
                      if column in visible_columns] + [column for column in visible_columns
                                                     if column not in group_order]

        headings = self.draw_headings(visible_columns, reverse_dependent_columns, output_options)
        # Why we need this test here: rows_to_tree would create an empty
        # top-node for an empty set of rows, which draw_tree would
        # render into a single row...
        if 'printable_version' in output_options:
            rows = self.get_all_rows()
        else:
            rows = self.get_rows()
        if rows:
            rendered_rows = self.draw_tree(self.rows_to_tree(rows, group_order),
                                         output_options,
                                         group_order, visible_columns)
        else:
            rendered_rows = []

        self.append_functions(rendered_rows, headings, output_options)

        return """
<div %(attr_html_attributes)s>
 %(table)s
 %(buttons)s
</div>
""" % {'attr_html_attributes': self.draw_html_attributes(self.path),
       'table': self.draw_table(headings, rendered_rows, output_options),
       'buttons': self.draw_buttons(output_options)
       }

    def output(self, output_options):
        return {Webwidgets.Constants.OUTPUT: self.draw_printable_version(output_options),
               'Content-type': 'text/html'
               }

    def draw_printable_version(self, output_options):
        return self.session.windows[self.win_id].draw(output_options,
                                                     body = self.draw(output_options),
                                                     title = self.title)
