# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

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

import types

def convert_to_str_any_way_possible(obj):
    try:
        if isinstance(obj, types.StringType):
            return unicode(obj, errors="replace")
        return unicode(obj)
    except Exception, e:
        try:
            return str(obj)
        except Exception, e2:
            return '{' + convert_type_to_str_any_way_possible(obj) + ' @ ' + str(id(obj)) + ': ' +  obj_info(e) + '}'

def convert_type_to_str_any_way_possible(obj):
    try:
        t = type(obj)
    except Exception, e:
        return '{' + obj_info(e) + '}'
    return obj_info(t)

def obj_info(obj):
    res = []
    t = type(obj)
    res += [convert_to_str_any_way_possible(obj)]
    if t == types.InstanceType:
        klass = type(obj)
        res += [obj_info(klass)]
    elif t == types.ClassType:
        klass = obj.__class__
        res += [obj_info(klass)]
    res += [convert_to_str_any_way_possible(t)]
    return '[' + ' '.join(res) + ']'
