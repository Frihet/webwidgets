# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Provides a list-selector widget
# Copyright (C) 2008 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

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

import os.path

class GeographicRegion(object):
    file_pattern = "ISO_3166-2/%(symbols)s/names.txt"
    file_sep = os.path.sep
    
    def __init__(self, symbols, title):
        self.symbols = symbols
        self.title = title
        self.parts, self.sym_dict, self.name_dict = self.load_list(
            symbols,
            os.path.join(os.path.dirname(__file__), 
                         self.file_pattern % {'symbols': self.file_sep.join(symbols)}))

    def load_list(cls, symbols, file_name):
        def entry_to_region(symbol, title):
            return GeographicRegion(symbols + [symbol], title)
        if not os.access(file_name, os.F_OK): return [], {}, {}
        file = open(file_name)
        try:
            result = [entry_to_region(*entry[:-1].decode('utf-8').split(" ", 1))
                      for entry in file]
            result.sort(lambda l, r: cmp(l.title, r.title))
            sym_dict = dict([(r.symbols[-1], r) for r in result])
            name_dict = dict([(r.title, r) for r in result])
            return result, sym_dict, name_dict
        finally:
            file.close()
    load_list = classmethod(load_list)
    
    def __unicode__(self):
        return self.title
    def __str__(self):
        return str(unicode(self))

class GeographicRegionWorld(GeographicRegion):
    file_pattern = "ISO_3166-1_alpha-2.txt"

world = GeographicRegionWorld([], "World")
