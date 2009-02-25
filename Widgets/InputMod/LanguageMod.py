#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moller@freecode.no>
# Copyright (C) 2007 FreeCode AS, Axel Liljencrantz <axel.liljencrantz@freecode.no>

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

import Webwidgets.Widgets.InputMod.BaseInput

class LanguageInput(Webwidgets.Widgets.InputMod.BaseInput.ListInput):
    languages = {'en':u'English', 'sv':u'Svenska', 'no':u'Norsk'}
    
    def get_children(self):
        return self.languages.iteritems()

class LanguageSelector(LanguageInput):
    class Value(object):
        def __get__(self, instance, owner):
            if not hasattr(instance, 'session'):
                return None
            if instance.session.languages is None:
                return instance.get_languages({})[0]
            return instance.session.languages[0]
        def __set__(self, instance, value):
            instance.session.languages = (value,)
    value = Value()
