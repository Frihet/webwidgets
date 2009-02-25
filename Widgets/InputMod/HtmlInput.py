#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright © 2007 Egil Möller <redhog@redhog.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import time, os.path
import Webwidgets.Utils
import Webwidgets.Widgets.InputMod.BaseInput
import Webwidgets.Widgets.Base
import Webwidgets.Widgets.WindowMod

class HtmlInput(Webwidgets.Widgets.InputMod.BaseInput.StringInput, Webwidgets.Widgets.Base.DirectoryServer):
    """
    Html Input Widget.
    """
    rows = 40
    cols = 80
    
    def draw(self, output_options):
        """
        Draw input widget.
        """
        Webwidgets.Widgets.WindowMod.HtmlWindow.register_script_link(self, self.calculate_url({'widget_class': 'Webwidgets.HtmlInput',
                                                   'location': ['fckeditor.js']},
                                                  {}))
        widget_id = Webwidgets.Utils.path_to_id(self.path)
        Webwidgets.Widgets.WindowMod.HtmlWindow.register_script(self, 'fckeditor: ' + widget_id,
                            """
webwidgets_add_event_handler(
 window,
 'load',
 'webwidgets_fckeditor_load_%(widget_id)s',
 function()
  {
   var oFCKeditor = new FCKeditor('%(widget_id)s');
   oFCKeditor.BasePath = "%(widget_url)s/" ;
   oFCKeditor.ReplaceTextarea() ;
  });
  """ % {'widget_id': widget_id,
         'widget_url': self.calculate_url({'widget_class': 'Webwidgets.HtmlInput'}, {})})
        return super(HtmlInput, self).draw(output_options)
