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
import Input, Base

class HtmlInput(Input.StringInput, Base.DirectoryServer):
    """
    Html Input Widget.
    """
    rows = 40
    cols = 80
    
    def draw(self, output_options):
        """
        Draw input widget.
        """
        self.registerScriptLink(self.calculate_url({'widget_class': 'Webwidgets.HtmlInput',
                                                   'location': ['fckeditor.js']},
                                                  {}))
        widgetId = Webwidgets.Utils.path_to_id(self.path)
        self.registerScript('fckeditor: ' + widgetId,
                            """
webwidgets_add_event_handler(
 window,
 'load',
 'webwidgets_fckeditor_load_%(widgetId)s',
 function()
  {
   var oFCKeditor = new FCKeditor('%(widgetId)s');
   oFCKeditor.BasePath = "%(widgetUrl)s/" ;
   oFCKeditor.ReplaceTextarea() ;
  });
  """ % {'widgetId': widgetId,
         'widgetUrl': self.calculate_url({'widget_class': 'Webwidgets.HtmlInput'})})
        return super(HtmlInput, self).draw(output_options)
