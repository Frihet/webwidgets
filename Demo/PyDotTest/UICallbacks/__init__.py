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

import pydot
import Webwidgets

class MyWindow(object):
    class Body(object):
        class Graph(object):
            def __init__(self, *arg, **kw):
                Webwidgets.DotGraph.__init__(self, *arg, **kw)

            def selected(self, path, node):
                if (self + "1:NodeOps-NodeName1-Field").value:
                    (self + "1:NodeOps-NodeName2-Field").value = node
                else:
                    (self + "1:NodeOps-NodeName1-Field").value = node

        class NodeOps(object):
            class NodeName1(object):
                class Field(object): pass
                
            class NodeName2(object):
                class Field(object): pass
                
            class AddNode(object):
                class Field(object):
                    def clicked(self, path):
                        name = (self + "2:NodeName1-Field").value
                        graph = (self + "3:Graph")
                        graph.graph.add_node(pydot.Node(name, label=name, URL=graph.calculate_callback_url(name)))
                        (self + "2:NodeName1-Field").value = ''
                        (self + "2:NodeName2-Field").value = ''

            class DelNode(object):
                class Field(object): pass

            class AddEdge(object):
                class Field(object):
                    def clicked(self, path):
                        name1 = (self + "2:NodeName1-Field").value
                        name2 = (self + "2:NodeName2-Field").value
                        graph = (self + "3:Graph")
                        graph.graph.add_edge(pydot.Edge(name1, name2, URL=graph.calculate_callback_url("%s:%s" % (name1, name2))))
                        (self + "2:NodeName1-Field").value = ''
                        (self + "2:NodeName2-Field").value = ''

            class DelEdge(object):
                class Field(object): pass
