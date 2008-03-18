#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moeller@freecode.no>

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

import Webwidgets
import datetime, math, Model, sqlalchemy.sql

Webwidgets.Program.Session.debug_fields = False
Webwidgets.Program.Session.debug_send_notification = False

True_ = sqlalchemy.sql.text("(1 = 1)")
False_ = sqlalchemy.sql.text("(1 = 2)")

class SQLAlchemyFilter(Webwidgets.Filter):
    non_memory_storage = True

    def get_row_query(self, all, output_options):
        expand_tree = self.get_expand_tree()
        query = self.session.db.query(Model.Service)
        
        if self.default_expand:
            def tree_to_filter(node):
                if node.toggled:
                    return Model.Service.table.c.id.in_(node.rows.keys())
                else:
                    whens = []
                    for value, sub in node.values.iteritems():
                        whens.append((getattr(Model.Service.table.c, node.col) == value,
                                     tree_to_filter(sub)))
                    if whens:
                        return sqlalchemy.sql.case(whens, else_ = True_)
                    else:
                        return True_
        else:
            prev_row = Model.Service.table.alias()
            # FIXME: prev_row.c.id + 1 == Model.Service.table.c.id
            # does not work, since id:s are not in order for every
            # sort! Must be the order of the current sort!
            query = query.select_from(
                Model.Service.table.outerjoin(
                    prev_row,
                    prev_row.c.id + 1 == Model.Service.table.c.id))

            def tree_to_filter(node):
                whens = []
                for value, sub in node.values.iteritems():
                    sub_query = False_
                    if sub.toggled:
                        sub_query = tree_to_filter(sub)
                    whens.append((getattr(Model.Service.table.c, node.col) == value,
                                 sub_query))
                if whens:
                    node_query = sqlalchemy.sql.case(whens, else_ = False_)
                else:
                    node_query = False_
                return sqlalchemy.sql.case([(getattr(prev_row.c, node.col) == getattr(Model.Service.table.c, node.col), node_query)],
                                           else_ = True_)
            
        filter = tree_to_filter(expand_tree)
        query = query.filter(filter)

        for col, order in self.sort:
            query = query.order_by(getattr(getattr(Model.Service.table.c, col), order)())
        query = query.order_by(Model.Service.table.c.id.asc())
        
        if not all:
            query = query[(self.page - 1) * self.rows_per_page:
                          self.page * self.rows_per_page]
            
        print "EXPAND", self.expand
        #print expand_tree
        #print "QUERY"
        #print query
        return query

    def get_rows(self, all, output_options):
        return list(self.get_row_query(all, output_options))

    def get_row_by_id(self, row_id):
        return self.session.db.query(Model.Service).filter(Model.Service.table.c.id == row_id)[0]
    
    def get_row_id(self, row):
        return str(row['id'])

    def get_pages(self):
        return int(math.ceil(float(self.get_row_query(False, {}).count()) / self.rows_per_page))

class MyWindow(object):
    class Body(object):
        class Autoexpand(object):
            default_expand = False
            
            class RowFilters(Webwidgets.Table.RowFilters):
                Filters = Webwidgets.Table.RowFilters.Filters + [SQLAlchemyFilter]
            
            def __init__(self, session, win_id, **attrs):
                Webwidgets.Table.__init__(self, session, win_id, **attrs)
                self.sort = [('country', 'asc'),
                             ('provider', 'asc'),
                             ('technology', 'asc'),
                             ('price', 'asc')]
