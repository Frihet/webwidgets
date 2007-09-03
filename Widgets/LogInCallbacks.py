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
    __attributes__ = Webwidgets.Html.__attributes__ + ('globalSession', 'userInfo')
    globalSession = True
    userInfo = None
    debugLogIn = False
    debugErrors = False
    
    class logIn(object):
        def selected(self, path, value):
            fields = self.getWidgetsByAttribute('fieldName')

            if self.parent.debugLogIn: print "Log in attempt:", fields['username'].value, fields['password'].value

            try:
                self.parent.userInfo = self.parent.authenticate(
                    fields['username'].value,
                    fields['password'].value)
            except Exception, e:
                if self.parent.debugErrors: traceback.print_exc()
                fields['username'].error = unicode(e)
                
            else:
                if self.parent.debugLogIn: print "User logged in:", self.parent.userInfo
                
    def authenticate(self, username, password):
        raise Exception("You must override the authenticate() method of this widget!")

    def userInfoChanged(self, path, value):
        if self.globalSession:
            self.session.logIn = self
        if self.userInfo is None:
            self['application'] = Webwidgets.Html(self.session, self.winId)
            self['logIn'].visible = True
        else:
            self['application'] = self.Application(self.session, self.winId)
            self['logIn'].visible = False

class LogOut(object):
    debug = True
    __attributes__ = Webwidgets.Dialog.__attributes__ + ('logIn',)
    logIn = None
    
    def selected(self, path, value):
        if self.logIn is None:
            logIn = self.session.logIn
        elif isinstance(self.logIn, Webwidgets.Widget):
            logIn = self.logIn
        else:
            logIn = self + self.logIn
        logIn.userInfo = None
            
