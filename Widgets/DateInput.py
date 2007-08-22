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

class DateInputWidget(Input.StringInputWidget):
    """
    Date Selector Widget.
    """
    __attributes__ = Input.StringInputWidget.__attributes__ + ('format',)
    format = '%Y-%m-%d'
    value = time.localtime()

    def draw(self, path):
        """
        Draw input widget.
        """
        super(DateInputWidget, self).draw(path)

        widgetId = Webwidgets.Utils.pathToId(self.path())
        self.registerStyleLink(self.calculateUrl({'widget': widgetId,
                                                  'file': 'jscalendar/calendar-blue.css',
                                                  'type': 'text/css'}))
        self.registerScriptLink(self.calculateUrl({'widget': widgetId,
                                                   'file': 'jscalendar/calendar.js',
                                                   'type': 'text/plain'}),
                                self.calculateUrl({'widget': widgetId,
                                                   'file': 'jscalendar/lang/calendar-en.js',
                                                   'type': 'text/plain'}),
                                self.calculateUrl({'widget': widgetId,
                                                   'file': 'jscalendar/calendar-setup.js',
                                                   'type': 'text/plain'}))

        return '''<input name="%(name)s" id="%(id)s" value="%(value)s" autocomplete="off" />
       <script type="text/javascript">
         Calendar.setup(
           {
             inputField  : "%(id)s",
             displayArea : "%(id)s",
             ifFormat    : "%(format)s",
             daFormat    : "%(format)s",
             button      : "%(id)s"
           }
         );
       </script>''' % {
            'name': Webwidgets.Utils.pathToId(path),
            'value': self.fieldOutput(path)[0], 'format': self.format,
            'disabled': ['', 'disabled="true"'][not self.getActive(path)],
            'id': Webwidgets.Utils.pathToId(path)}


    def fieldInput(self, path, stringValue):
        try:
            self.value = time.strptime(stringValue, self.format)
            self.notify('valueChanged', self.value)
        except ValueError:
            self.error = 'Invalid date format, expected %s got %s' \
                % (self.format, stringValue)
            self.notify('errorChanged', self.error)
                
    def fieldOutput(self, path):
        return [time.strftime(self.format, self.value)]

    def output(self, outputOptions):
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
    
