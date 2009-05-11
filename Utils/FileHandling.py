# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
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

from __future__ import with_statement
import os.path

extension_to_mime_type = {}
with open(os.path.splitext(__file__)[0] + '.mimetypes.txt') as mimetypes:
    for line in mimetypes:
        ext, mime_type = line[:-1].split(' ')
        extension_to_mime_type[ext] = mime_type

extension_to_encoding = {}
with open(os.path.splitext(__file__)[0] + '.encodings.txt') as encodings:
    for line in encodings:
        ext, encoding = line[:-1].split(' ')
        extension_to_encoding[ext] = encoding

def extension_to_headers(extension):
    headers = {}
    
    headers['Content-type'] = extension_to_mime_type.get(extension, 'application/octet-stream')
    if extension in extension_to_encoding:
        headers['Content-Encoding'] = extension_to_encoding[extension]

    return headers
