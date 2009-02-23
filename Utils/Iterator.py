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

class Ilen(object):
    def __init__(self, itr):
        self.iter = iter(itr)
        
    def __int__(self):
        l = 0
        for obj in self.iter:
            l += 1
        return l
    
    def __cmp__(self, other):
        if not isinstance(other, Ilen):
            other = Ilen(xrange(0, other)) 
        while True:
            try:
                self.iter.next()
            except StopIteration:
                try:
                    other.iter.next()
                except StopIteration:
                    return 0
                else:
                    return -1
            try:
                other.iter.next()
            except StopIteration:
                try:
                    self.iter.next()
                except StopIteration:
                    return 0
                else:
                    return 1
