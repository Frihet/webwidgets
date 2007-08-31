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

import Webwidgets.Constants, Webwidgets.Utils, re, math
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

def sortToOrderBy(sort):
    order = []
    for key, dir in sort:
        assert column_allowed_name_re.match(key) is not None
        order.append(key + ' ' + ['desc', 'asc'][dir == 'asc'])
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
                value = self[name] = value(self.node.session, self.node.winId)
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
  
class GBOList(Base.Input, Base.Composite):
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
        'functions', 'disabledFunctions', 'functionPosition',
        'sort', 'rows', 'page', 'pages', 'rowsPerPage',
        'nonMemoryStorage', 'dontMergeWidgets', 'dontMergeColumns')
    columns = {}
    argumentName = None
    dependentColumns = {}
    functions = {}
    disabledFunctions = []
    functionPosition = 0
    sort =[]
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

    def __init__(self, session, winId, **attrs):
        Base.Composite.__init__(self, session, winId, **attrs)
        self.rows = ChildNodeRows(self, self.rows)
        self.reread()

    def function(self, path, function, row):
        raise Exception('%s: Function %s not implemented (called for row %s)' % (Webwidgets.Utils.pathToId(path), function, row))

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

    def sortChanged(self, path, sort):
        """Notification that the list sort order has changed."""
        if path != self.path: return
        self.reread()

    def pageChanged(self, path, page):
        """Notification that the user has changed page."""
        if path != self.path: return
        self.reread()

    def getRows(self):
        if self.nonMemoryStorage:
            return self.rows
        return self.rows[(self.page - 1) * self.rowsPerPage:
                         self.page * self.rowsPerPage]

    def getPages(self):
        if self.nonMemoryStorage:
            return self.pages        
        return int(math.ceil(float(len(self.rows)) / self.rowsPerPage))

    def getChildren(self):
        raise NotImplemented

    def getChild(self, name):
        dummy, row, column = name.split('_')
        row = int(row)
        return self.getRows()[row][column]
    
    def getWidgetsByAttribute(self, attribute = '__name__'):
        fields = Base.Widget.getWidgetsByAttribute(self, attribute)
        for row in self.getRows():
            for column, child in row.iteritems():
                if isinstance(child, Base.Widget):
                    fields.update(child.getWidgetsByAttribute(attribute))
        return fields

    def fieldInput(self, path, stringValue):
        widgetPath = self.path
        try:
            subWidget = self.pathToSubwidgetPath(path)
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
    
    def fieldOutput(self, path):
        widgetPath = self.path
        subWidget = self.pathToSubwidgetPath(path)
        
        if subWidget == ['sort']:
            return [sortToString(self.sort)]
        elif subWidget == ['page']:
            return [unicode(self.page)]
        elif subWidget[0] == 'function':
            return []
        else:
            raise Exception('Unknown sub-widget %s in %s' %(subWidget, widgetPath))

    def getActive(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        widgetPath = self.path
        subWidget = self.pathToSubwidgetPath(path)

        if not self.active: return False

        if subWidget == ['sort'] or subWidget == ['page']:
            return self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.winId, path)
        elif subWidget[0] == 'column':
            return self.session.AccessManager(Webwidgets.Constants.VIEW, self.winId, path)
        elif subWidget[0] == 'function':
            if subWidget[1] in self.disabledFunctions: return False
            return self.session.AccessManager(Webwidgets.Constants.EDIT, self.winId, path)
        else:
            raise Exception('Unknown sub-widget %s in %s' %(subWidget, widgetPath))

    def visibleColumns(self):
        path = self.path
        # Optimisation: we could have used getActive and constructed a path...
        return Webwidgets.Utils.OrderedDict([(name, description) for (name, description) in self.columns.iteritems()
                                  if self.session.AccessManager(Webwidgets.Constants.VIEW, self.winId,
                                                                path + ['_', 'column', name])])

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

    def drawTree(self, node, path, outputOptions, groupOrder, visibleColumns, firstLevel = 0, lastLevel = 0):
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
                                          path, outputOptions,
                                          groupOrder, visibleColumns,
                                          subFirst, subLast))
        else:
            rows = []
            for row in xrange(0, node['rows']):
                rows.append([''] * len(visibleColumns))
        if 'value' in node:
            column = groupOrder[node['level'] - 1]
            rows[0][visibleColumns.keys().index(column)
                    ] = self.drawNode(path, outputOptions, node, column, firstLevel, lastLevel)
        return rows

    def drawNode(self, path, outputOptions, node, column, firstLevel, lastLevel):
        return self.drawCell(path, outputOptions, node['value'], node['top'], column, node['rows'], firstLevel, lastLevel)
        
    def drawCell(self, path, outputOptions, value, row, column, rowspan, firstLevel, lastLevel):
        return '<td rowspan="%(rowspan)s" class="%(class)s">%(content)s</td>' % {
            'rowspan': rowspan,
            'class': 'column_first_level_%s column_last_level_%s' % (firstLevel, lastLevel),
            'content': self.drawChild(path + ["cell_%s_%s" % (row, column)],
                                      value, outputOptions, True)}

    def drawPagingButtons(self, path):
        if self.argumentName:
            self.session.windows[self.winId].arguments[self.argumentName + '_page'] = {
                'widget':self, 'path': path + ['_', 'page']}

        pageId = Webwidgets.Utils.pathToId(path + ['_', 'page'])
        pageActive = self.getActive(path + ['_', 'page'])
        if pageActive:
            self.session.windows[self.winId].fields[pageId] = self
        return """
<div class="buttons">
 <span class="left">
  <button type="submit" %(backActive)s id="%(attr_html_id)s_first" name="%(attr_html_id)s" value="%(first)s" />&lt;&lt;</button>
  <button type="submit" %(backActive)s id="%(attr_html_id)s_previous" name="%(attr_html_id)s" value="%(previous)s" />&lt;</button>
 </span>
 <span class="center">
  %(page)s/%(pages)s
 </span>
 <span class="right">
  <button type="submit" %(forwardActive)s id="%(attr_html_id)s_next" name="%(attr_html_id)s" value="%(next)s" />&gt;</button>
  <button type="submit" %(forwardActive)s id="%(attr_html_id)s_last" name="%(attr_html_id)s" value="%(last)s" />&gt;&gt;</button>
 </span>
</div>
""" % {'attr_html_id': pageId,
       'first': 1,
       'previous': self.page - 1,
       'page': self.page,
       'pages': self.getPages(),
       'next': self.page + 1,
       'last': self.getPages(),
       'backActive': ['', 'disabled="true"'][not pageActive or self.page <= 1],
       'forwardActive': ['', 'disabled="true"'][not pageActive or self.page >= self.getPages()],
       }

    def drawHeadings(self, path, visibleColumns, reverseDependentColumns):
        if self.argumentName:
            self.session.windows[self.winId].arguments[self.argumentName + '_sort'] = {
                'widget':self, 'path': path + ['_', 'sort']}

        sortActive = self.getActive(path + ['_', 'sort'])
        headings = []
        inputId = Webwidgets.Utils.pathToId(path + ['_', 'sort'])
        if sortActive:
            self.session.windows[self.winId].fields[inputId] = self
        for column, title in visibleColumns.iteritems():
            headings.append("""
<th class="column %(classes)s">
 <button type="submit" id="%(attr_html_id)s_%(column)s" %(disabled)s name="%(attr_html_id)s" value="%(sort)s" />%(caption)s</button>
</th>
""" %
                            {'attr_html_id': inputId,
                             'column': column,
                             'disabled': ['disabled="true"', ''][sortActive],
                             'caption': title,
                             'classes': sortToClasses(self.sort, reverseDependentColumns.get(column, column)),
                             'sort': sortToString(setSort(self.sort, reverseDependentColumns.get(column, column)))
                             })
        return headings

    def appendFunctions(self, path, rows, headings):
        if self.functions:
            functionPosition = self.functionPosition
            if functionPosition < 0:
                functionPosition += 1
                if functionPosition == 0: 
                    functionPosition = len(headings)
            
            functionActive = {}
            for function in self.functions:
                functionActive[function] = self.getActive(path + ['_', 'function', function])

            for function in self.functions:
                if functionActive[function]:
                    self.session.windows[self.winId].fields[Webwidgets.Utils.pathToId(path + ['_', 'function', function])] = self
            for rowNum in xrange(0, len(rows)):
                functions = '<td class="functions">%s</td>' % ''.join([
                    """<button type="submit" id="%(attr_html_id)s" %(disabled)s name="%(attr_html_id)s" value="%(row)s" />%(title)s</button>""" % {
                        'attr_html_id': Webwidgets.Utils.pathToId(path + ['_', 'function', function]),
                        'disabled': ['disabled="true"', ''][functionActive[function]],
                        'title': title,
                        'row':rowNum}
                    for function, title in self.functions.iteritems()])
                rows[rowNum].insert(functionPosition, functions)
    
            headings.insert(functionPosition, '<th></th>')

    def drawTable(self, headings, rows):
        return "<table>%(headings)s%(content)s</table>" % {
            'headings': '<tr>%s</tr>' % (' '.join(headings),),
            'content': '\n'.join(['<tr>%s</tr>' % (''.join(row),) for row in rows])}
            
    def draw(self, outputOptions):
        widgetId = Webwidgets.Utils.pathToId(self.path)

        reverseDependentColumns = reverseDependency(self.dependentColumns)
        visibleColumns = self.visibleColumns()

        groupOrder = extendToDependentColumns(
            [column for column, dir in self.sort],
            self.dependentColumns)
        groupOrder = [column for column in groupOrder
                      if column in visibleColumns] + [column for column in visibleColumns
                                                     if column not in groupOrder]

        headings = self.drawHeadings(self.path, visibleColumns, reverseDependentColumns)
        # Why we need this test here: rowsToTree would create an empty
        # top-node for an empty set of rows, which drawTree would
        # render into a single row...
        if self.getRows():
            renderedRows = self.drawTree(self.rowsToTree(self.getRows(), groupOrder),
                                         self.path, outputOptions,
                                         groupOrder, visibleColumns)
        else:
            renderedRows = []

        self.appendFunctions(self.path, renderedRows, headings)

        return """
<div %(attr_htmlAttributes)s>
 %(table)s
 %(pagingButtons)s
</div>
""" % {'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
       'table': self.drawTable(headings, renderedRows),
       'pagingButtons': self.drawPagingButtons(self.path)
       }
