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

import Webwidgets, traceback

class LogIn(object):
    global_session = True
    user_info = None
    debug_log_in = False
    debug_errors = False
    
    class log_in(object):
        def selected(self, path, value):
            fields = self.get_widgets_by_attribute('field_name')

            if self.parent.debug_log_in: print "Log in attempt:", fields['username'].value, fields['password'].value

            try:
                self.parent.user_info = self.parent.authenticate(
                    fields['username'].value,
                    fields['password'].value)
            except Exception, e:
                if self.parent.debug_errors: traceback.print_exc()
                fields['username'].error = unicode(e)
            else:
                if self.parent.debug_log_in: print "User logged in:", self.parent.user_info
                
    def authenticate(self, username, password):
        raise Exception("You must override the authenticate() method of this widget!")

    def user_info_changed(self, path, value):
        if self.global_session:
            self.session.log_in = self
        if self.user_info is None:
            self['application'] = Webwidgets.Html(self.session, self.win_id)
            self['log_in'].visible = True
        else:
            self['application'] = self.Application(self.session, self.win_id)
            self['log_in'].visible = False

class LogOut(object):
    debug = True
    log_in = None
    
    def selected(self, path, value):
        if self.log_in is None:
            log_in = self.session.log_in
        elif isinstance(self.log_in, Webwidgets.Widget):
            log_in = self.log_in
        else:
            log_in = self + self.log_in
        log_in.user_info = None
            
