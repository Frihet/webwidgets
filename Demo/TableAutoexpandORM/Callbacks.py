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

class SQLAlchemyFilter(Webwidgets.Filter):
    non_memory_storage = True

    def get_row_query(self, all, output_options):
        expand_tree = self.get_expand_tree()
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
        filter = tree_to_filter(expand_tree)
        query = self.session.db.query(Model.Service).filter(filter)

        for col, order in self.sort:
            query = query.order_by(getattr(getattr(Model.Service.table.c, col), order)())
        query = query.order_by(Model.Service.table.c.id.asc())
        
        if not all:
            query = query[(self.page - 1) * self.rows_per_page:
                          self.page * self.rows_per_page]

        #print "QUERY", query
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
            class RowFilters(Webwidgets.Table.RowFilters):
                Filters = Webwidgets.Table.RowFilters.Filters + [SQLAlchemyFilter]
            
            def __init__(self, session, win_id, **attrs):
                Webwidgets.Table.__init__(self, session, win_id, **attrs)
                self.sort = [('country', 'asc'),
                             ('provider', 'asc'),
                             ('technology', 'asc'),
                             ('price', 'asc')]
