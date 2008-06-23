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

import Utils, Constants, csv

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
        """Check if an operation is allowed to perform on a widget.

        @param op: Operation to perform
        @param win_id: Window id
        @param path: Widget path within the window
        """
        
        self.debug_print(op, win_id, path, True)
        return True

class ListAccessManager(AccessManager):
    """ListAccessManager controlls access to widgets according to an
    access control list.

    The list is traversed from head to tail comparing the widget path
    to the path pattern for each item until a match is found. The
    result (true or false) from the matching item is returned, or
    False if no item was found matching.
    
    Each list item is a tuple of C{(rule_result, rule_scope,
    rule_path)}.

        - C{rule_result} is the value to return if the item matches,
          either C{True} or C{False}.

        - C{rule_scope} determines how to match the path -
          L{Constants.ONE} for exact comparation or
          L{Constants.SUBTREE} for subtree matching.

        - C{rule_path} is the path to match, expressed as a list of
          strings/unicode strings. The first item is the operation to
          perform, the window id the second, and the rest of the path
          is the widget path.
    """
    
    debug_lists = False
    
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
            if self.debug_lists:
                scope = ''
                if rule_scope is Constants.SUBTREE: scope = '.*'
                print "AccessManager:  %s %s: %s%s" % (
                    marker, rule_result, '.'.join([str(item) for item in rule_path]), scope)
        if result is None: result = False
        self.debug_print_path(operation_path, result)
        return result

    def get_access_list(self):
        """Returns the access control list. This version fetches it
        using L{self.session.get_access_list} Override this in a
        subclass to fetch/construct the list from somewhere else."""
        return self.session.get_access_list()

    def load_access_list_from_file(cls, file):
        for line in csv.reader(file):
            if not line or line[0].startswith('#'): continue
            (result, scope, op, win, path) = line
            yield ({"allow": True,
                    "deny": False}[result.strip()],
                   {"sub": Constants.SUBTREE,
                    "one": Constants.ONE}[scope.strip()],
                   ({"view": Constants.VIEW,
                     "rarr": Constants.REARRANGE,
                     "edit": Constants.EDIT}[op.strip()],
                    (win.strip() == "def" and Constants.DEFAULT_WINDOW) or win.strip()
                    ) + tuple(Utils.id_to_path(path.strip())))
    load_access_list_from_file = classmethod(load_access_list_from_file)

    def load_access_list_from_file_name(cls, name):
        file = open(name)
        try:
            for line in cls.load_access_list_from_file(file):
                yield line
        finally:
            file.close()
    load_access_list_from_file_name = classmethod(load_access_list_from_file_name)
