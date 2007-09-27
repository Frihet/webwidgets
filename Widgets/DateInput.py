#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright © 2007 FreeCode AS, Claes Nästén <claes.nasten@freecode.no>
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

import datetime, time, os.path
import Webwidgets.Utils
import Input

class DateInput(Input.StringInput):
    """
    Date Selector Widget.
    """
    __attributes__ = Input.StringInput.__attributes__ + ('format',)
    format = '%Y-%m-%d'
    value = datetime.datetime.now()

    def draw(self, outputOptions):
        """
        Draw input widget.
        """
        super(DateInput, self).draw(outputOptions)

        self.registerStyleLink(self.calculateUrl({'widgetClass': 'Webwidgets.DateInput',
                                                  'file': 'calendar-blue.css',
                                                  'type': 'text/css'},
                                                 {}))
        self.registerScriptLink(self.calculateUrl({'widgetClass': 'Webwidgets.DateInput',
                                                   'file': 'calendar.js',
                                                   'type': 'text/plain'},
                                                  {}),
                                self.calculateUrl({'widgetClass': 'Webwidgets.DateInput',
                                                   'file': 'lang/calendar-en.js',
                                                   'type': 'text/plain'},
                                                  {}),
                                self.calculateUrl({'widgetClass': 'Webwidgets.DateInput',
                                                   'file': 'calendar-setup.js',
                                                   'type': 'text/plain'},
                                                  {}))

        return '''<input %(attr_htmlAttributes)s name="%(name)s" value="%(value)s" autocomplete="off" %(disabled)s />
       <script type="text/javascript">
         Calendar.setup(
           {
             inputField  : "%(attr_html_id)s",
             displayArea : "%(attr_html_id)s",
             ifFormat    : "%(format)s",
             daFormat    : "%(format)s",
             button      : "%(attr_html_id)s"
           }
         );
       </script>''' % {
            'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
            'name': Webwidgets.Utils.pathToId(self.path),
            'value': self.fieldOutput(self.path)[0], 'format': self.format,
            'disabled': ['', 'disabled="disabled"'][not self.getActive(self.path)],
            'attr_html_id': Webwidgets.Utils.pathToId(self.path)}


    def fieldInput(self, path, stringValue):
        try:
            if stringValue == '':
                self.value = None
            else:
                self.value = datetime.datetime(*(time.strptime(stringValue, self.format)[0:6]))
        except ValueError:
            self.value = None
            self.error = 'Invalid date format, expected %s got %s' \
                % (self.format, stringValue)
                
    def fieldOutput(self, path):
        if self.value is None:
            return ['']
        return [self.value.strftime(self.format)]

    def classOutput(cls, session, arguments, outputOptions):
        path = outputOptions['file']
        assert not path.startswith('/')
        while path:
            path, item = os.path.split(path)
            assert item != '..'

        file = open(os.path.join(os.path.dirname(__file__),
                                 'DateInput.scripts',
                                 outputOptions['file']))
        try:
            return {Webwidgets.Constants.FINAL_OUTPUT: file.read(),
                    'Content-type': outputOptions['type']
                    }
        finally:
            file.close()
    classOutput = classmethod(classOutput)
