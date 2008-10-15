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
    encoding_priority = ('ascii', 'iso-8859-1', 'utf-8')
    "List of encoding, earlier elements have higher priority."""

    def __init__(self, **kwargs):
        """Initialize Mailer, supported kwargs are smtp_KEYs defined
        on the mailer class without the smtp_ prefix."""

        # Set arguments for key, value in
        for key, value in kwargs.iteritems():
            if not hasattr(self, 'smtp_%s' % (key, )):
                raise ValueError('unsupported keyword argument %s' % (key, ))
            setattr(self, 'smtp_%s' % (key, ), value)

    def send(self, mail_from, mail_to, body):
        """Send single mail. Raises socket.error on connection
        issues. Raises smtplib.SMTPAuthenticationError if
        authentication fails."""
        smtp = self._init_connection()

        smtp.sendmail(mail_from, mail_to, body)

        self._close_connection(smtp)

    def construct_mail(self, template, args):
        """Create mail body that can be sent with the mail
        method. template is a string with standard %(value)s format
        parameters and args is a dict with the values"""
        template_enc = template
        args_enc = None

        if isinstance(template, unicode):
            for encoding in self.encoding_priority:
                try:
                    template_enc = template.encode(encoding)
                    args_enc = self._encode_arguments(encoding, args)
                except UnicodeEncodeError:
                    template_enc = None

                if template_enc is not None and args_enc is not None:
                    break

            # If encoding failed, force encoding with last encoding in the list.
            if template_enc is None:
                template_enc = template.encode(self.encoding_priority[-1], 'replace')

        # If encoding failed or default encoding is use, use last in
        # priority and replace errors to be safe.
        if args_enc is None:
            args_enc = self._encode_arguments(self.encoding_priority[-1], args, 'replace')

        return template_enc % args_enc

    def _encode_arguments(self, encoding, args, errors='strict'):
        try:
            args_encoded = {}
            for key, value in args.iteritems():
                if isinstance(value, unicode):
                    value = value.encode(encoding, errors)
                args_encoded[key] = value
        except UnicodeEncodeError:
            args_encoded = None

        return args_encoded

    def _init_connection(self):
        """Connect to host, authenticate and return smtp
        connection."""

        smtp = smtplib.SMTP()
        smtp.connect(self.smtp_host, self.smtp_port)
        if self.smtp_tls:
            smtp.starttls()

        if self.smtp_user and self.smtp_password:
            smtp.login(self.smtp_user, self.smtp_password)

        return smtp

    def _close_connection(self, smtp):
        """Cleanup SMTP connection."""
        smtp.quit()
