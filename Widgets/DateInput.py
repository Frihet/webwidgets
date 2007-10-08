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
import Input, Base 

class DateInput(Input.StringInput, Base.DirectoryServer):
    """
    Date Selector Widget.
    """
    __attributes__ = Input.StringInput.__attributes__ + ('format',)
    format = '%Y-%m-%d'
    value = datetime.datetime.now()

    def draw(self, output_options):
        """
        Draw input widget.
        """
        super(DateInput, self).draw(output_options)

        self.register_style_link(self.calculate_url({'widget_class': 'Webwidgets.DateInput',
                                                  'location': ['calendar-blue.css']},
                                                 {}))
        self.register_script_link(self.calculate_url({'widget_class': 'Webwidgets.DateInput',
                                                   'location': ['calendar.js']},
                                                  {}),
                                self.calculate_url({'widget_class': 'Webwidgets.DateInput',
                                                   'location': ['lang', 'calendar-en.js']},
                                                  {}),
                                self.calculate_url({'widget_class': 'Webwidgets.DateInput',
                                                   'location': ['calendar-setup.js']},
                                                  {}))

        return '''<input %(attr_html_attributes)s name="%(name)s" value="%(value)s" autocomplete="off" %(disabled)s />
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
            'attr_html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'value': self.field_output(self.path)[0], 'format': self.format,
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)],
            'attr_html_id': Webwidgets.Utils.path_to_id(self.path)}


    def field_input(self, path, string_value):
        try:
            if string_value == '':
                self.value = None
            else:
                self.value = datetime.datetime(*(time.strptime(string_value, str(self.format))[0:6]))
        except ValueError:
            self.value = None
            self.error = 'Invalid date format, expected %s got %s' \
                % (self.format, string_value)
                
    def field_output(self, path):
        if self.value is None:
            return ['']
        return [self.value.strftime(str(self.format))]
