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

class MyWindow(object):
    class Body(object):
        class TreeModel(Webwidgets.TreeModel):
            class Node(Webwidgets.TreeModelGroupingWrapperNode):
                limit = 5
                class Node(Webwidgets.TreeModelNode):
                    def __init__(self, tree, parent = None, path = ['root']):
                        Webwidgets.Tree.TreeModel.Node.__init__(
                            self, tree, parent, path[-1])
                        self.path = path
                        self.sub_nodes = Webwidgets.Utils.OrderedDict()
                        self.expandable = len(path) < 4
                        if self.expandable:
                            for n1 in range(ord("a"), ord("z")):
                                for n2 in range(ord("a"), ord("c")):
                                    name = unichr(n1) + unichr(n2) + "foo" + str(len(path))
                                    self.sub_nodes[name] = type(self)(tree, self, path + [name])
