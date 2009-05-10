#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
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

"""Output formatting widgets.
"""

import Webwidgets.Utils

try:
    import pydot
except:
    class pydot(object):
        @classmethod
        def Dot(*arg, **kw):
            raise NotImplementedError("This widget requires the pydot Python module. Please ask the system administrator to install it.")

import tempfile
import os
import cgi
import Webwidgets.Utils.FileHandling
import Webwidgets.Constants
import Webwidgets.Widgets.Base

class DotGraph(Webwidgets.Widgets.Base.MultipleActionInput):
    graph = None
    "An instance of pydot.Dot"

    graph_args = {'prog': "neato",
                  'graph_name': 'unnamed',
                  'graph_type': 'digraph',
                  'strict': False,
                  'suppress_disconnected': False,
                  'simplify': False}
    "Arguments for pydot.Dot"

    def __init__(self, *arg, **kw):
        Webwidgets.Widgets.Base.Widget.__init__(self, *arg, **kw)
        self.clear()

    def clear(self):
        self.graph = pydot.Dot(**self.graph_args)

    def _graph_name(self):
        return '_'.join(self.path + ['_', 'graph'])

    def output(self, output_options):
        self.graph.set_name(self._graph_name())
        return {Webwidgets.Constants.OUTPUT: self.graph.create(format = output_options.get('format', 'png')),
                'Content-type': Webwidgets.Utils.FileHandling.extension_to_mime_type[output_options.get('format', 'png')]}

    def draw(self, output_options):
        self.register_input(self.path, Webwidgets.Utils.path_to_id(self.path), False)
        self.graph.set_name(self._graph_name())
        # iframe/object/embed IE workaround from http://www.graphviz.org/webdot/svgembed.html
        # FXIME: Uncomment when we've found out a way to figure out width and height from Graphviz
        return """
<!-- iframe src='%(location_svgz)s' width='%(width)s' height='%(height)s' frameborder='0' marginwidth='0' marginheight='0'>
 <object data='%(location_svgz)s' width='%(width)s' height='%(height)s' type='image/svg+xml'>
  <embed src='%(location_svgz)s' type='image/svg+xml' coding='gzip' palette='foreground' -->
   <img %(html_attributes)s src='%(location_png)s' usemap='#%(graphid)s' />
   %(cmapx)s
  <!-- /embed>
 </object>
</iframe -->
        """ % {'html_attributes': self.draw_html_attributes(self.path),
               'width': 'unknown',
               'height': 'unknown',
               'location_svgz': cgi.escape(self.calculate_output_url(Webwidgets.Utils.subclass_dict(output_options, {'format': 'svgz'}))),
               'location_png': cgi.escape(self.calculate_output_url(Webwidgets.Utils.subclass_dict(output_options, {'format': 'png'}))),
               'graphid': self._graph_name(),
               'cmapx': self.graph.create(format = output_options.get('format', 'cmapx'))}

    def calculate_output_url(self, output_options, format = 'png'):
        return self.calculate_url({'transaction': output_options['transaction'],
                                   'widget': Webwidgets.Utils.path_to_id(self.path),
                                   'format':format})

    def calculate_callback_url(self, selection):
        # Add "" around URL to fix bug in pydot:s escaping 
        return '"%s"' % (self.calculate_url({}, {Webwidgets.Utils.path_to_id(self.path): selection}),)
