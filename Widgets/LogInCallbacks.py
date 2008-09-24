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

import Webwidgets, smtplib, traceback

class LogIn(object):
    global_session = True
    user_info = None
    debug_log_in = False
    debug_errors = False
    is_login_widget = True
    
    recovery_email_template = """
From: %(from_email)s
To: %(to_email)s
Subject: Recovered account information

You have requested to recover your account information. Your password
has been reset.

Your username: %(username)s
Your new password: %(new_password)s

Please log in and change your password as soon as possible.
"""
    from_email = 'no-reply@localhost'

    mail_host = 'localhost'
    mail_username = None
    mail_password = None

    def __init__(self, session, win_id, **attrs):
        Webwidgets.Html.__init__(self, session, win_id, **attrs)
        self.user_info_changed(self.path, self.user_info)
  
    class LogIn(object):
        def selected(self, path, value):
            if path != self.path: return
            login_widget = self.get_ansestor_by_attribute("is_login_widget", True)
            if value == 'login':            
                fields = self.get_widgets_by_attribute('field_name')

                if login_widget.debug_log_in: print "Log in attempt:", fields['username'].value, fields['password'].value

                try:
                    login_widget.user_info = login_widget.authenticate(
                        fields['username'].value,
                        fields['password'].value)
                except Exception, e:
                    if login_widget.debug_errors: traceback.print_exc()
                    fields['username'].error = unicode(e)
                else:
                    if login_widget.debug_log_in: print "User logged in:", login_widget.user_info
            if value == 'forgotten':
                Webwidgets.DialogContainer.add_dialog_to_nearest(
                    self,
                    self.Forgotten(self.session, self.win_id, login_widget = login_widget))

        class Forgotten(object):
             class Body(object):
                 class IdentitiesGroup(object):
                     class Username(object):
                         class Field(object):
                             invalid_username_or_email = "You must provide either a username or an email address."
                             def validate_username_or_email(self):
                                 return self.value or self.parent.parent['EMail']['Field'].value
             
             def selected(self, path, value):
                 if path != self.path: return
                 if not self.validate(): return
                 if value == "recover":
                     fields = self.get_widgets_by_attribute('field_name')
                     username = fields['recover_username'].value
                     email = fields['recover_email'].value
                     
                     if not username:
                         username = self.login_widget.get_username_from_email(email)
                     elif not email:
                         email = self.login_widget.get_email_from_username(username)

                     if not (username and email):
                         result_dialog = self.RecoveryFailed
                     else:
                         result_dialog = self.RecoveryComplete
                         new_password = self.login_widget.reset_password_for_user(username)

                         smtp = smtplib.SMTP()
                         smtp.connect(self.login_widget.mail_host)
                         if self.login_widget.mail_username and self.login_widget.mail_password:
                             smtp.login(self.login_widget.mail_username, self.login_widget.mail_password)

                         email_content = self.login_widget.recovery_email_template % {
                             'from_email': self.login_widget.from_email,
                             'to_email': email,
                             'username': username,
                             'new_password': new_password}
                         smtp.sendmail(
                             self.login_widget.from_email, email,
                             email_content)
                         smtp.quit()

                     Webwidgets.DialogContainer.add_dialog_to_nearest(
                         self,
                         result_dialog(self.session, self.win_id))
                 Webwidgets.Dialog.selected(self, path, value)

    def authenticate(self, username, password):
        raise NotImplementedError("You must override the authenticate() method of this widget!")

    def get_username_from_email(self, email):
        raise NotImplementedError("You must override the get_username_from_email() method of this widget!")
    
    def get_email_from_username(self, username):
        raise NotImplementedError("You must override the get_email_from_username() method of this widget!")
    
    def reset_password_for_user(self, username):
        raise NotImplementedError("You must override the reset_password_for_user() method of this widget!")

    def user_info_changed(self, path, value):
        if self.global_session:
            self.session.log_in = self
        if self.user_info is None:
            self['Application'] = Webwidgets.Html(self.session, self.win_id)
            self['LogIn'].visible = True
        else:
            self['Application'] = self.Application(self.session, self.win_id)
            self['LogIn'].visible = False

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
            
