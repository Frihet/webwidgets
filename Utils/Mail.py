#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2008 FreeCode AS, Egil Moeller <egil.moeller@freecode.no>

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

import smtplib

class Mailer(object):
    """Mailer class wrapping smtplib  with defaults for sending e-mail
    from a Webwidgets application."""

    smtp_host = 'localhost'
    "Host used when sending e-mail."
    smtp_port = 25
    "Port used when sending e-mail."
    smtp_tls = False
    "Enable TLS on connectino if set."
    smtp_user = None
    "If set, use this username when authenticating to the host."
    smtp_password = None
    "If set, use this password when authenticating to the host."

    def __init__(self, **kwargs):
        """Initialize Mailer, supported kwargs are smtp_KEYs defined
        on the mailer class without the smtp_ prefix."""

        # Set arguments for key, value in
        for key, value in kwargs.iteritems():
            if not hasattr(self, 'smtp_%s' % (key, )):
                raise ValueError('unsupported keyword argument %s' % (key, ))
            setattr(self, 'smtp_%s' % (key, ), value)

    def send(self, mail_from, mail_to, body):
        """Send single mail."""
        smtp = self._init_connection()

        smtp.sendmail(mail_from, mail_to, body)

        self._close_connection(smtp)

    def construct_mail(self, template, args):
        """Create mail body that can be sent with the mail
        method. template is a string with standard %(value)s format
        parameters and args is a dict with the values"""
        return template % args

    def _init_connection(self):
        """Connect to host, authenticate and return smtp
        connection."""

        smtp = smtplib.SMTP()
        smtp.connect(self.smtp_host, self.smtp_port)
        if self.smtp_tls:
            smtp.starttls()

        if self.smtp_user and self.smtp_password:
            smtp.authenticate(self.smtp_user, self.smtp_password)

        return smtp

    def _close_connection(self, smtp):
        """Cleanup SMTP connection."""
        smtp.quit()
