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

import time, os.path
import Webwidgets.Utils
import Input

class DateInput(Input.StringInput):
    """
    Date Selector Widget.
    """
    __attributes__ = Input.StringInput.__attributes__ + ('format',)
    format = '%Y-%m-%d'
    value = time.localtime()

    def draw(self, path):
        """
        Draw input widget.
        """
        super(DateInput, self).draw(path)

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

        return '''<input %(attr_htmlAttributes)s name="%(name)s" value="%(value)s" autocomplete="off" />
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
            'attr_htmlAttributes': self.drawHtmlAttributes(path),
            'name': Webwidgets.Utils.pathToId(path),
            'value': self.fieldOutput(path)[0], 'format': self.format,
            'disabled': ['', 'disabled="true"'][not self.getActive(path)],
            'attr_html_id': Webwidgets.Utils.pathToId(path)}


    def fieldInput(self, path, stringValue):
        try:
            self.value = time.strptime(stringValue, self.format)
        except ValueError:
            self.error = 'Invalid date format, expected %s got %s' \
                % (self.format, stringValue)
                
    def fieldOutput(self, path):
        return [time.strftime(self.format, self.value)]

    def classOutput(cls, window, outputOptions):
        path = outputOptions['file']
        assert not path.startswith('/')
        while path:
            path, item = os.path.split(path)
            assert item != '..'

        file = open(os.path.join(os.path.dirname(__file__),
                                 'DateInput.scripts',
                                 outputOptions['file']))
        try:
            return {Webwidgets.Constants.OUTPUT: file.read(),
                    'Content-type': outputOptions['type']
                    }
        finally:
            file.close()
    classOutput = classmethod(classOutput)
