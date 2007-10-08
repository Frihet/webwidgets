#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moeller@freecode.no>

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

import Utils, Constants

class AccessManager(object):
    """This class can be overridden to control access to
    widgets."""
    debug = False
    
    def __init__(self, session):
        self.session = session

    def debug_print(self, op, win_id, path, result):
        if self.debug:
            print "AccessManager: %s: %s: %s:%s" % (result, op, win_id, '.'.join(path))

    def __call__(self, op, win_id, path):
        self.debug_print(op, win_id, path, True)
        return True

class ListAccessManager(AccessManager):
    debugLists = False
    
    def debug_print_path(self, operation_path, result):
        if self.debug:
            print "AccessManager: %s: %s" % (result, '.'.join([str(item) for item in operation_path]))

    def __call__(self, op, win_id, path):
        return self.call_path((op, win_id) + tuple(path))

    def call_path(self, operation_path):
        lst = self.get_access_list()
        result = None
        for rule_result, rule_scope, rule_path in lst:
            marker = '   '
            if (   (rule_scope is Constants.SUBTREE and Utils.is_prefix(rule_path, operation_path))
                or (rule_scope is Constants.ONE and rule_path == operation_path)):
                marker = ' ->'
                if result is None:
                    marker = '==>'
                    result = rule_result
            if self.debugLists:
                scope = ''
                if rule_scope is Constants.SUBTREE: scope = '.*'
                print "AccessManager:  %s %s: %s%s" % (
                    marker, rule_result, '.'.join([str(item) for item in rule_path]), scope)
        if result is None: result = False
        self.debug_print_path(operation_path, result)
        return result

    def get_access_list(self):
        return self.session.get_access_list()
