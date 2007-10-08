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

def setSort(sort, key):
    if sort and sort[0][0] == key:
        res = [list(key) for key in sort]
        res[0][1] = ['desc', 'asc'][res[0][1] == 'desc']
    else:
        res = [[key, 'desc']] + [orig_key for orig_key in sort
                                 if orig_key[0] != key]
    return res

def stringToSort(str):
    if str == '': return []
    return [key.split('-') for key in str.split('.')]

def sortToString(sort):
    return '.'.join(['-'.join(key) for key in sort])

def sortToClasses(sort, column):
    classes = []
    for level, (key, order) in enumerate(sort):
        if key == column:
            classes.append('column_sort_order_' + order)
            classes.append('column_sort_level_' + str(level))
            break
    return ' '.join(classes)

def sortToOrderBy(sort, quote = "`"):
    order = []
    for key, dir in sort:
        assert column_allowed_name_re.match(key) is not None
        order.append(quote + key + quote + ' ' + ['desc', 'asc'][dir == 'asc'])
    if order:
        return 'order by ' + ', '.join(order)
    return ''

def extendToDependentColumns(columns, dependentColumns):
    res = []
    for column in columns:
        res.extend([column] + dependentColumns.get(column, []))
    return res

def reverseDependency(dependentColumns):
    res = {}
    for main, dependent in dependentColumns.iteritems():
        for dependentColumn in dependent:
            res[dependentColumn] = main
    return res

class ChildNodeCells(Base.ChildNodes):
    def __init__(self, node, row, *arg, **kw):
        self.row = row
        super(ChildNodeCells, self).__init__(node, *arg, **kw)

    def __ensure__(self):
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
        self.__ensure__()
    
    def __ensure__(self):
        for index in xrange(0, len(self)):
            if not isinstance(self[index], ChildNodeCells) or self[index].row != index:
                self[index] = ChildNodeCells(self.node, index, self[index])

    def __setitem__(self, *arg, **kw):
        super(ChildNodeRows, self).__setitem__(*arg, **kw)
        self.__ensure__()

    def __delitem__(self, *arg, **kw):
        super(ChildNodeRows, self).__delitem__(*arg, **kw)
        self.__ensure__()

    def __setslice__(self, *arg, **kw):
        super(ChildNodeRows, self).__setslice__(*arg, **kw)
        self.__ensure__()

    def extend(self, *arg, **kw):
        super(ChildNodeRows, self).extend(*arg, **kw)
        self.__ensure__()

    def append(self, *arg, **kw):
        super(ChildNodeRows, self).append(*arg, **kw)
        self.__ensure__()

    def insert(self, *arg, **kw):
        super(ChildNodeRows, self).insert(*arg, **kw)
        self.__ensure__()

    def reverse(self, *arg, **kw):
        super(ChildNodeRows, self).reverse(*arg, **kw)
        self.__ensure__()
    
    def sort(self, *arg, **kw):
        super(ChildNodeRows, self).sort(*arg, **kw)
        self.__ensure__()
  
class GBOList(Base.ActionInput, Base.Composite):
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
    
    __attributes__ = Base.Composite.__attributes__ + (
        'dependentColumns', 'columns', 'dependentColumns',
        'functions', 'groupFunctions', 'disabledFunctions', 'functionPosition',
        'sort', 'rows', 'page', 'pages', 'rowsPerPage',
        'nonMemoryStorage', 'dontMergeWidgets', 'dontMergeColumns')
    columns = {}
    argument_name = None
    dependentColumns = {}
    functions = {}
    groupFunctions = {}
    disabledFunctions = []
    functionPosition = 0
    sort = []
    rows = []
    page = 1
    pages = 1
    nonMemoryStorage = False
    dontMergeWidgets = True
    dontMergeColumns = ()
    oldSort = []
    rowsPerPage = 10
    """This attribute is not used internally by the widget, but is
    intended to be used by the user-provide reread() method."""

    def __init__(self, session, win_id, **attrs):
        Base.Composite.__init__(self, session, win_id, **attrs)
        self.rows = ChildNodeRows(self, self.rows)
        self.reread()

#     def function(self, path, function, row):
#         raise Exception('%s: Function %s not implemented (called for row %s)' % (Webwidgets.Utils.path_to_id(path), function, row))

#     def groupFunction(self, path, function):
#         raise Exception('%s: Function %s not implemented' % (Webwidgets.Utils.path_to_id(path), function))

    def reread(self):
        """Reload the list after a repaging/resorting here. This is
        not a notification to allow for it to be called from __init__.

        If you set nonMemoryStorage to True, you _must_ override this
        method with your own sorter/loader function.
        """
        def rowCmp(row1, row2):
            for col, order in self.sort:
                diff = cmp(row1[col], row2[col])
                if diff:
                    if order == 'desc': diff *= -1
                return diff
            return 0
        
        if self.sort != self.oldSort:
            self.rows.sort(rowCmp)
            self.oldSort = self.sort

    def sort_changed(self, path, sort):
        """Notification that the list sort order has changed."""
        if path != self.path: return
        self.reread()

    def page_changed(self, path, page):
        """Notification that the user has changed page."""
        if path != self.path: return
        self.reread()

    def getAllRows(self):
        return self.rows
    
    def getRows(self):
        if self.nonMemoryStorage:
            return self.rows
        return self.rows[(self.page - 1) * self.rowsPerPage:
                         self.page * self.rowsPerPage]

    def getPages(self):
        if self.nonMemoryStorage:
            return self.pages        
        return int(math.ceil(float(len(self.rows)) / self.rowsPerPage))

    def get_children(self):
        raise NotImplemented

    def get_child(self, name):
        dummy, row, column = name.split('_')
        row = int(row)
        return self.rows[row][column]
    
    def get_widgets_by_attribute(self, attribute = '__name__'):
        fields = Base.Widget.get_widgets_by_attribute(self, attribute)
        for row in self.getRows():
            for column, child in row.iteritems():
                if isinstance(child, Base.Widget):
                    fields.update(child.get_widgets_by_attribute(attribute))
        return fields

    def field_input(self, path, stringValue):
        widget_path = self.path
        try:
            subWidget = self.path_to_subwidget_path(path)
        except Webwidgets.Constants.NotASubwidgetException:
            return
        
        if subWidget == ['sort']:
            if stringValue != '':
                self.sort = stringToSort(stringValue)
        elif subWidget == ['page']:
            if stringValue != '':
                self.page = int(stringValue)
        elif subWidget[0] == 'function':
            if stringValue != '':
                self.notify('function', subWidget[1], int(stringValue))
        elif subWidget[0] == 'groupFunction':
            if stringValue != '':
                self.notify('groupFunction', subWidget[1])
    
    def field_output(self, path):
        widget_path = self.path
        subWidget = self.path_to_subwidget_path(path)
        
        if subWidget == ['sort']:
            return [sortToString(self.sort)]
        elif subWidget == ['page']:
            return [unicode(self.page)]
        elif subWidget[0] == 'function':
            return []
        elif subWidget[0] == 'groupFunction':
            return []
        else:
            raise Exception('Unknown sub-widget %s in %s' %(subWidget, widget_path))

    def get_active(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        widget_path = self.path
        subWidget = self.path_to_subwidget_path(path)

        if not self.active: return False

        if subWidget == ['sort'] or subWidget == ['page']:
            return self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, path)
        elif subWidget[0] == 'column':
            return self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id, path)
        elif subWidget[0] == 'function':
            if subWidget[1] in self.disabledFunctions: return False
            return self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, path)
        elif subWidget[0] == 'groupFunction':
            if subWidget[1] in self.disabledFunctions: return False
            return self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, path)
        else:
            raise Exception('Unknown sub-widget %s in %s' %(subWidget, widget_path))

    def visibleColumns(self):
        # Optimisation: we could have used get_active and constructed a path...
        return Webwidgets.Utils.OrderedDict([(name, description) for (name, description) in self.columns.iteritems()
                                  if self.session.AccessManager(Webwidgets.Constants.VIEW, self.win_id,
                                                                self.path + ['_', 'column', name])])

    def rowsToTree(self, rows, groupOrder):
        tree = {'level': 0,
                'rows': 0,
                'children':[]}
        for rowNum in xrange(0, len(rows)):
            row = rows[rowNum]
            node = tree
            node['rows'] += 1
            for column in groupOrder:
                merge = (    column not in self.dontMergeColumns
                         and node['children']
                         and (   not self.dontMergeWidgets
                              or (    not isinstance(node['children'][-1]['value'], Base.Widget)
                                  and not isinstance(row[column], Base.Widget)))
                         and node['children'][-1]['value'] == row[column])
                if not merge:
                    node['children'].append({'level': node['level'] + 1,
                                             'top': rowNum,
                                             'rows': 0,
                                             'value': row[column],
                                             'children':[]})
                node = node['children'][-1]
                node['rows'] += 1
        return tree

    def drawTree(self, node, output_options, groupOrder, visibleColumns, firstLevel = 0, lastLevel = 0):
        if node['children']:
            rows = []
            children = len(node['children'])
            for child in xrange(0, children):
                subFirst = firstLevel
                subLast = lastLevel
                if child != 0:
                    subFirst += 1
                if child != children - 1:
                    subLast += 1
                rows.extend(self.drawTree(node['children'][child],
                                          output_options,
                                          groupOrder, visibleColumns,
                                          subFirst, subLast))
        else:
            rows = []
            for row in xrange(0, node['rows']):
                rows.append([''] * len(visibleColumns))
        if 'value' in node:
            column = groupOrder[node['level'] - 1]
            rows[0][visibleColumns.keys().index(column)
                    ] = self.drawNode(output_options, node, column, firstLevel, lastLevel)
        return rows

    def drawNode(self, output_options, node, column, firstLevel, lastLevel):
        return self.drawCell(output_options, node['value'], node['top'], column, node['rows'], firstLevel, lastLevel)
        
    def drawCell(self, output_options, value, row, column, rowspan, firstLevel, lastLevel):
        return '<td rowspan="%(rowspan)s" class="%(class)s">%(content)s</td>' % {
            'rowspan': rowspan,
            'class': 'column_first_level_%s column_last_level_%s' % (firstLevel, lastLevel),
            'content': self.draw_child(self.path + ["cell_%s_%s" % (row, column)],
                                      value, output_options, True)}

    def drawPagingButtons(self, output_options):
        if self.argument_name:
            self.session.windows[self.win_id].arguments[self.argument_name + '_page'] = {
                'widget':self, 'path': self.path + ['_', 'page']}

        pageId = Webwidgets.Utils.path_to_id(self.path + ['_', 'page'])
        pageActive = self.get_active(self.path + ['_', 'page'])
        if pageActive:
            self.session.windows[self.win_id].fields[pageId] = self
        info = {'attr_html_id': pageId,
                'first': 1,
                'previous': self.page - 1,
                'page': self.page,
                'pages': self.getPages(),
                'next': self.page + 1,
                'last': self.getPages(),
                'backActive': ['', 'disabled="disabled"'][not pageActive or self.page <= 1],
                'forwardActive': ['', 'disabled="disabled"'][not pageActive or self.page >= self.getPages()],
                }
            
        return """
<span class="left">
 <button type="submit" %(backActive)s id="%(attr_html_id)s-_-first" name="%(attr_html_id)s" value="%(first)s">&lt;&lt;</button>
 <button type="submit" %(backActive)s id="%(attr_html_id)s-_-previous" name="%(attr_html_id)s" value="%(previous)s">&lt;</button>
</span>
<span class="center">
 %(page)s/%(pages)s
</span>
<span class="right">
 <button type="submit" %(forwardActive)s id="%(attr_html_id)s-_-next" name="%(attr_html_id)s" value="%(next)s">&gt;</button>
 <button type="submit" %(forwardActive)s id="%(attr_html_id)s-_-last" name="%(attr_html_id)s" value="%(last)s">&gt;&gt;</button>
</span>
""" % info

    def drawPrintableLink(self, output_options):
        location = self.calculate_url({'widget': Webwidgets.Utils.path_to_id(self.path),
                                      'printableVersion': 'yes'})
        return """<a class="printable" href="%(location)s">%(caption)s</a>""" % {
            'caption': self._("Printable version", output_options),
            'location': cgi.escape(location),
            }

    def drawGroupFunctions(self, output_options):
        functionActive = {}
        for function in self.groupFunctions:
            functionActive[function] = self.get_active(self.path + ['_', 'groupFunction', function])

        for function in self.groupFunctions:
            if functionActive[function]:
                self.session.windows[self.win_id].fields[Webwidgets.Utils.path_to_id(self.path + ['_', 'groupFunction', function])] = self

        return '\n'.join([
            """<button
                type="submit"
                id="%(attr_html_id)s"
                class="%(attr_html_class)s"
                %(disabled)s
                name="%(attr_html_id)s"
                value="selected">%(title)s</button>""" % {'attr_html_id': Webwidgets.Utils.path_to_id(self.path + ['_', 'groupFunction', function]),
                                                          'attr_html_class': function,
                                                          'disabled': ['disabled="disabled"', ''][functionActive[function]],
                                                          'title': self._(title, output_options)}
            for function, title in self.groupFunctions.iteritems()])

    def drawButtons(self, output_options):
        if 'printableVersion' in output_options:
            return ''
        return """
<div class="buttons">
 %(pagingButtons)s
 %(printableLink)s
 %(groupFunctions)s
</div>
""" % {'pagingButtons': self.drawPagingButtons(output_options),
       'printableLink': self.drawPrintableLink(output_options),
       'groupFunctions': self.drawGroupFunctions(output_options)}

    def drawHeadings(self, visibleColumns, reverseDependentColumns, output_options):
        if self.argument_name:
            self.session.windows[self.win_id].arguments[self.argument_name + '_sort'] = {
                'widget':self, 'path': self.path + ['_', 'sort']}

        sortActive = self.get_active(self.path + ['_', 'sort'])
        headings = []
        inputId = Webwidgets.Utils.path_to_id(self.path + ['_', 'sort'])
        widgetId = Webwidgets.Utils.path_to_id(self.path)
        if sortActive:
            self.session.windows[self.win_id].fields[inputId] = self
        for column, title in visibleColumns.iteritems():
            info = {'inputId': inputId,
                    'attr_html_id': widgetId,
                    'column': column,
                    'disabled': ['disabled="disabled"', ''][sortActive],
                    'caption': self._(title, output_options),
                    'classes': sortToClasses(self.sort, reverseDependentColumns.get(column, column)),
                    'sort': sortToString(setSort(self.sort, reverseDependentColumns.get(column, column)))
                    }
            if 'printableVersion' in output_options:
                headings.append("""
<th id="%(attr_html_id)s-_-head-%(column)s" class="column %(classes)s">
 <span id="%(attr_html_id)s-_-sort-%(column)s">%(caption)s</span>
</th>
""" % info)
            else:
                headings.append("""
<th id="%(attr_html_id)s-_-head-%(column)s" class="column %(classes)s">
 <button type="submit" id="%(attr_html_id)s-_-sort-%(column)s" %(disabled)s name="%(attr_html_id)s-_-sort" value="%(sort)s">%(caption)s</button>
</th>
""" % info)
        return headings

    def appendFunctions(self, rows, headings, output_options):
        if 'printableVersion' not in output_options and self.functions:
            functionPosition = self.functionPosition
            if functionPosition < 0:
                functionPosition += 1
                if functionPosition == 0: 
                    functionPosition = len(headings)
            
            functionActive = {}
            for function in self.functions:
                functionActive[function] = self.get_active(self.path + ['_', 'function', function])

            for function in self.functions:
                if functionActive[function]:
                    self.session.windows[self.win_id].fields[Webwidgets.Utils.path_to_id(self.path + ['_', 'function', function])] = self
            for rowNum in xrange(0, len(rows)):
                functions = '<td class="functions">%s</td>' % ''.join([
                    """<button
                        type="submit"
                        id="%(attr_html_id)s-%(row)s"
                        class="%(attr_html_class)s"
                        %(disabled)s
                        name="%(attr_html_id)s"
                        value="%(row)s">%(title)s</button>""" % {'attr_html_id': Webwidgets.Utils.path_to_id(self.path + ['_', 'function', function]),
                                                                 'attr_html_class': function,
                                                                 'disabled': ['disabled="disabled"', ''][functionActive[function]],
                                                                 'title': self._(title, output_options),
                                                                 'row': rowNum}
                    for function, title in self.functions.iteritems()])
                rows[rowNum].insert(functionPosition, functions)
    
            headings.insert(functionPosition, '<th></th>')

    def drawTable(self, headings, rows, output_options):
        return "<table>%(headings)s%(content)s</table>" % {
            'headings': '<tr>%s</tr>' % (' '.join(headings),),
            'content': '\n'.join(['<tr>%s</tr>' % (''.join(row),) for row in rows])}
            
    def draw(self, output_options):
        widgetId = Webwidgets.Utils.path_to_id(self.path)

        reverseDependentColumns = reverseDependency(self.dependentColumns)
        visibleColumns = self.visibleColumns()

        groupOrder = extendToDependentColumns(
            [column for column, dir in self.sort],
            self.dependentColumns)
        groupOrder = [column for column in groupOrder
                      if column in visibleColumns] + [column for column in visibleColumns
                                                     if column not in groupOrder]

        headings = self.drawHeadings(visibleColumns, reverseDependentColumns, output_options)
        # Why we need this test here: rowsToTree would create an empty
        # top-node for an empty set of rows, which drawTree would
        # render into a single row...
        if 'printableVersion' in output_options:
            rows = self.getAllRows()
        else:
            rows = self.getRows()
        if rows:
            renderedRows = self.drawTree(self.rowsToTree(rows, groupOrder),
                                         output_options,
                                         groupOrder, visibleColumns)
        else:
            renderedRows = []

        self.appendFunctions(renderedRows, headings, output_options)

        return """
<div %(attr_html_attributes)s>
 %(table)s
 %(buttons)s
</div>
""" % {'attr_html_attributes': self.draw_html_attributes(self.path),
       'table': self.drawTable(headings, renderedRows, output_options),
       'buttons': self.drawButtons(output_options)
       }

    def output(self, output_options):
        return {Webwidgets.Constants.OUTPUT: self.drawPrintableversion(output_options),
               'Content-type': 'text/html'
               }

    def drawPrintableversion(self, output_options):
        return self.session.windows[self.win_id].draw(output_options,
                                                     body = self.draw(output_options),
                                                     title = self.title)
