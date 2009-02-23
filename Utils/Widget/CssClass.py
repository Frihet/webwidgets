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

def classes_remove_bases(classes, cls):
    base_classes = set()
    for base in cls.__bases__:
        base_classes.update(base.ww_classes)
    return [cls for cls in classes if cls not in base_classes]

def classes_to_css_classes(classes, postfix = []):
    if postfix:
        postfix = ['', '_'] + postfix
    cls_set = set(classes)
    if len(cls_set) != len(classes):
        res = []
        for cls in reversed(classes):
            if cls in cls_set:
                res.append(cls)
                cls_set.remove(cls)
        classes = reversed(res)
    return ' '.join([c.replace('.', '-') + '-'.join(postfix)
                     for c in classes])
