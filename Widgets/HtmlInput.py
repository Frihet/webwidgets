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
import Input

class HtmlInput(Input.StringInput):
    """
    Html Input Widget.
    """
    rows = 10
    
    def draw(self, outputOptions):
        """
        Draw input widget.
        """
        self.registerScriptLink(self.calculateUrl({'widgetClass': 'Webwidgets.HtmlInput',
                                                   'location': ['fckeditor.js']},
                                                  {}))
        widgetId = Webwidgets.Utils.pathToId(self.path)
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
         'widgetUrl': self.calculateUrl({'widgetClass': 'Webwidgets.HtmlInput'})})
        return super(HtmlInput, self).draw(outputOptions)

    def classOutput(cls, session, arguments, outputOptions):
        path = outputOptions['location']
        for item in path:
            assert item != '..'

        ext = os.path.splitext(path[-1])[1][1:]
        file = open(os.path.join(os.path.dirname(__file__),
                                 'HtmlInput.scripts',
                                 *path))
        try:
            return {Webwidgets.Constants.FINAL_OUTPUT: file.read(),
                    'Content-type': {'html':'text/html',
                                     'xml':'text/xml',
                                     'js':'pplication/x-javascript',
                                     'css':'text/css',
                                     'gif':'image/gif',
                                     'png':'image/png',
                                     'jpg':'image/jpeg',
                                     }[ext]}
        finally:
            file.close()
    classOutput = classmethod(classOutput)
