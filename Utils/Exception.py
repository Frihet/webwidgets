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

import os, os.path, traceback, syslog

log_exception_path = "/tmp" #None
"""Path to directory where exceptions are logged with log_exception
function. If this is None exceptions are not logged."""

log_exception_max_log=65534
"""Max number of logged exception files."""


def is_log_exceptions():
    return not not log_exception_path

def get_log_exception_path():
    """Return path exception directory."""
    return log_exception_path

def set_log_exception_path(path):
    """Set path to exception directory creating it if it does not
    exist."""
    globals()['log_exception_path'] = None

    if path:
        if not os.path.exists(path):
            os.makedirs(path)

        if not os.path.isdir(path):
            raise ValueError('%s path is not a directory' % (path, ))

        globals()['log_exception_path'] = path

def log_exception():
    """Log exception to file and return exception (exception, ID). On
    failure or if log_exception_path is empty/None return (exception, None)."""

    if not log_exception_path:
        return None

    try:
        exc_string = traceback.format_exc()

        try:
            exc_id, exc_fo = _log_exception_new()
            if exc_id and exc_fo:
                exc_fo.write(exc_string)

                syslog.syslog('%s exception logged with id %s' % (str(sys.exc_info()[1]), exc_id))
        finally:
            if exc_fo:
                exc_fo.close()
    except:
        exc_id = None

    return exc_id

def _log_exception_new():
    """Create a new exception file with ID id and return (id, fo)
    tuple where fo is an open file object."""
    exc_id = exc_fo = None

    if log_exception_path:
        # FIXME: Make something like mkstemp here to make this safe

        i = 0
        while not exc_fo and i < log_exception_max_log:
            path = os.path.join(log_exception_path, '%05d.info' % (i, ))
            if not os.path.exists(path):
                exc_fo = open(path, 'w')
                exc_id = '%05d' % (i, )
            i += 1

    return (exc_id, exc_fo)
