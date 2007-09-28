#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Gettext with fallbacks
# This file was taken from the Grimoire system administration framework
# Copyright © 2003 TakeIT AB, Egil Möller <redhog@takeit.se>
# Copyright © 2007 FreeCode AS, Egil Möller <egil.moller@freecode.no>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Founda; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA



import gettext

class UntranslatableError(Exception): pass

class NullTranslations(gettext.NullTranslations):
    def gettext(self, message):
        if self._fallback:
            return self._fallback.gettext(message)
        raise UntranslatableError()

    def ngettext(self, msgid1, msgid2, n):
        if self._fallback:
            return self._fallback.ngettext(msgid1, msgid2, n)
        raise UntranslatableError()

    def ugettext(self, message):
        if self._fallback:
            return self._fallback.ugettext(message)
        raise UntranslatableError()

    def ungettext(self, msgid1, msgid2, n):
        if self._fallback:
            return self._fallback.ungettext(msgid1, msgid2, n)
        raise UntranslatableError()

    def _(self, message):
        message = unicode(message)
        try:
            return self.ugettext(message)
        except UntranslatableError:
            return message

class GNUTranslations(gettext.GNUTranslations, NullTranslations):
    def __init__(self, *arg, **kw):
        gettext.GNUTranslations.__init__(self, *arg, **kw)
        self._catalog[''] = ''
        
    def gettext(self, message):
        try:
            tmsg = self._catalog[message]
            # Encode the Unicode tmsg back to an 8-bit string, if possible
            if self._charset:
                return tmsg.encode(self._charset)
            return tmsg
        except KeyError:
            return NullTranslations.gettext(self, message)

    def ngettext(self, msgid1, msgid2, n):
        try:
            tmsg = self._catalog[(msgid1, self.plural(n))]
            if self._charset:
                return tmsg.encode(self._charset)
            return tmsg
        except KeyError:
            return NullTranslations.ngettext(self, msgid1, msgid2, n)

    def ugettext(self, message):
        try:
            return self._catalog[message]
        except KeyError:
            return NullTranslations.ugettext(self, message)

    def ungettext(self, msgid1, msgid2, n):
        try:
            return self._catalog[(msgid1, self.plural(n))]
        except KeyError:
            return NullTranslations.ungettext(self, msgid1, msgid2, n)

def translation(domain, localedir=None, languages=None,
                class_=GNUTranslations, fallback=False):
    try:
        res = gettext.translation(domain, localedir, languages, class_)
        if fallback:
            res.add_fallback(fallback)
        return res
    except IOError, e:
        if fallback:
            return fallback
        else:
            raise e
