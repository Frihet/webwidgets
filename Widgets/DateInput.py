#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

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
    format = '%Y-%m-%d'
    original_value = value = datetime.datetime.now()

    def draw(self, output_options):
        """
        Draw input widget.
        """
        super(DateInput, self).draw(output_options)

        self.register_style_link(self.calculate_url({'transaction': output_options['transaction'],
                                                     'widget_class': 'Webwidgets.DateInput',
                                                     'location': ['calendar-blue.css']},
                                                    {}))
        self.register_script_link(self.calculate_url({'transaction': output_options['transaction'],
                                                      'widget_class': 'Webwidgets.DateInput',
                                                      'location': ['calendar.js']},
                                                     {}),
                                  self.calculate_url({'transaction': output_options['transaction'],
                                                      'widget_class': 'Webwidgets.DateInput',
                                                      'location': ['lang', 'calendar-en.js']},
                                                     {}),
                                  self.calculate_url({'transaction': output_options['transaction'],
                                                      'widget_class': 'Webwidgets.DateInput',
                                                      'location': ['calendar-setup.js']},
                                                     {}))

        return '''<input %(html_attributes)s name="%(name)s" value="%(value)s" autocomplete="off" %(disabled)s />
       <script type="text/javascript">
         Calendar.setup(
           {
             inputField  : "%(html_id)s",
             displayArea : "%(html_id)s",
             ifFormat    : "%(format)s",
             daFormat    : "%(format)s",
             button      : "%(html_id)s"
           }
         );
       </script>''' % {
            'html_attributes': self.draw_html_attributes(self.path),
            'name': Webwidgets.Utils.path_to_id(self.path),
            'value': self.field_output(self.path)[0], 'format': self.format,
            'disabled': ['', 'disabled="disabled"'][not self.get_active(self.path)],
            'html_id': Webwidgets.Utils.path_to_id(self.path)}


    def field_input(self, path, string_value):
        try:
            if string_value == '':
                self.ww_filter.value = None
            else:
                self.ww_filter.value = datetime.datetime(*(time.strptime(string_value, str(self.format))[0:6]))
        except ValueError:
            self.ww_filter.value = None
            self.error = 'Invalid date format, expected %s got %s' \
                % (self.format, string_value)
                
    def field_output(self, path):
        if self.ww_filter.value is None:
            return ['']
        return [self.ww_filter.value.strftime(str(self.format))]
