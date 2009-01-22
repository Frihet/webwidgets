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

"""
Webwidgets provide a built-in access control
method, where access to individual widgets (both viewing and
changing values) can be controlled using a type of ACL (Access
Control List).

To enable this feature, you must override the
C{AccessManager} class attribute when subclassing
C{Webwidgets.Program.Session}.

AccessManager should be a subclass of
C{Webwidgets.ListAccessManager} and provide a method
C{get_access_list()} that returns an apropriate ACL list,
given the status of the current session (a user is logged in, the
user is of this or that type, is a member of this or that group,
etc).

The format of the ACL is a list of tripples C{(Allow, Scope, Path)}.
The list is traversed from top to bottom, and the boolean C{Allow}
attribute first row whose C{Path} and C{Scope} matches the widget and
action determines if the action is allowed or not.

C{Path} is a path to the widget, with the action and window
prepended. C{Scope} is either C{SUB} or C{ONE}
to match the path and all child widgets to that path, or to match
just that widget, respectively.

The actions that can start a path are C{EDIT},
C{RARR} and C{VIEW}. The window is either
C{DEFAULT_WINDOW} or a window name::

  (True,  ONE,     (VIEW, DEFAULT_WINDOW, 'Body', 'LogIn', 'Application', 'Menu', 'AppMenu')),
  (False, SUB, (VIEW, DEFAULT_WINDOW, 'Body', 'LogIn', 'Application', 'Menu', 'AppMenu')),
  (False, SUB, (VIEW, DEFAULT_WINDOW, 'Body', 'LogIn', 'Application', 'Menu', 'AppMenu', 'Home', 'Stones'),
  (True,  SUB, (VIEW, DEFAULT_WINDOW, 'Body', 'LogIn', 'Application', 'Menu', 'AppMenu', 'Home'),
  (True,  SUB, (VIEW, DEFAULT_WINDOW, 'Body', 'LogIn', 'Application')),

To ease the creation of these lists, you can set the
C{debug} class attribute to C{True} on your
C{AccessManager} class. This will print the paths for all
attempts that Webwidgets does to access your widgets, and the
outcome of each attempt.
"""

import Utils, Constants, csv, re

allow_deny_strings = {"allow": True,
                      "deny": False}
allow_deny_values = dict((value, name) for (name, value) in allow_deny_strings.iteritems())
scope_strings = {"sub": Constants.SUB,
                 "one": Constants.ONE}
scope_values = dict((value, name) for (name, value) in scope_strings.iteritems())
op_strings = {"view": Constants.VIEW,
              "rarr": Constants.RARR,
              "edit": Constants.EDIT}
op_values = dict((value, name) for (name, value) in op_strings.iteritems())

class AccessManager(object):
    """This class can be overridden to control access to
    widgets."""
    debug = ()
    
    def __init__(self, session):
        self.session = session

    def debug_print(self, op, win_id, path, result):
        if self.debug and (self.debug is True or result in self.debug):
            print "AccessManager: %s, %s, %s, %s" % (allow_deny_values[result],
                                                     op_values[op],
                                                     win_id == Constants.DEFAULT_WINDOW and 'def' or win_id,
                                                     Utils.path_to_id(path))

    def __call__(self, op, win_id, path):
        """Check if an operation is allowed to perform on a widget.

        @param op: Operation to perform
        @param win_id: Window id
        @param path: Widget path within the window
        """
        
        self.debug_print(op, win_id, path, True)
        return True

class AbstractListAccessManager(AccessManager):
    debug_lists = False
    debug_list_match = False

    def op_to_path(self, op, win_id, path):
        return (op, win_id) + tuple(path)

    def __call__(self, op, win_id, path):
        result = self.call_path(self.op_to_path(op, win_id, path))
        self.debug_print(op, win_id, path, result)
        return result

    def get_access_list(self):
        """Returns the access control list. This version fetches it
        using L{self.session.get_access_list} Override this in a
        subclass to fetch/construct the list from somewhere else."""
        return self.session.get_access_list()

    @classmethod
    def load_access_list_from_file_name(cls, name):
        file = open(name)
        try:
            for line in cls.load_access_list_from_file(file):
                yield line
        finally:
            file.close()

    def call_path(self, operation_path):
        for rule in self.get_access_list():
            rule_result = self.call_rule_path(rule[1:], operation_path)
            if self.debug_lists or (self.debug_list_match and rule_result):
                print "AccessManager:  %s %s" % (['   ', '==>'][not not rule_result], self.print_rule(rule))
            if rule_result:
                return rule[0]
        return False

    def call_rule_path(self, rule, operation_path):
        raise NotImplementedError

    def load_access_list_from_file(cls, file):
        raise NotImplementedError

class ListAccessManager(AbstractListAccessManager):
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
          L{Constants.SUB} for subtree matching.

        - C{rule_path} is the path to match, expressed as a list of
          strings/unicode strings. The first item is the operation to
          perform, the window id the second, and the rest of the path
          is the widget path.
    """
    
    def call_rule_path(self, (rule_scope, rule_path), operation_path):
        return (   (rule_scope is Constants.SUB and Utils.is_prefix(rule_path, operation_path))
                or (rule_scope is Constants.ONE and rule_path == operation_path))

    def print_rule(self, (rule_result, rule_scope, rule_path)):
        scope = ''
        if rule_scope is Constants.SUB:
            scope = '.*'
        return "%s: %s%s" % (rule_result, '.'.join([str(item) for item in rule_path]), scope)

    @classmethod
    def load_access_list_from_file(cls, file):
        for line in csv.reader(file):
            if not line or line[0].startswith('#'): continue
            (result, scope, op, win, path) = line
            yield (allow_deny_strings[result.strip()],
                   scope_strings[scope.strip()],
                   (op_strings[op.strip()],
                    (win.strip() == "def" and Constants.DEFAULT_WINDOW) or win.strip()
                    ) + tuple(Utils.id_to_path(path.strip())))


class RegexpListAccessManager(AbstractListAccessManager):
    """RegexpListAccessManager controlls access to widgets according
    to an access control list made up of regular expressions.

    The list is traversed from head to tail comparing the widget path
    to the path pattern for each item until a match is found. The
    result (true or false) from the matching item is returned, or
    False if no item was found matching.
    
    Each list item is a tuple of C{(rule_result, rule_path_pattern)}.

        - C{rule_result} is the value to return if the item matches,
          either C{True} or C{False}.

        - C{rule_path} is the path to match, expressed as regular
          expression object that is matched against
          path_to_id(widget_path).
    """

    class Regexp(object):
        def __init__(self, regexp_string):
            self.regexp_string = regexp_string
            self.regexp = re.compile("^%s$" % (regexp_string,))
            
        def __getattr__(self, name):
            return getattr(self.regexp, name)

        def __unicode__(self):
            return unicode(self.regexp_string)

        def __str__(self):
            return str(self.regexp_string)

        def __repr__(self):
            return repr(self.regexp_string)

    def op_to_path(self, op, win_id, path):
        return Utils.path_to_id([unicode(item) for item in (op, win_id) + tuple(path)])

    def debug_print(self, op, win_id, path, result):
        if self.debug and (self.debug is True or result in self.debug):
            print "AccessManager: %s, %s" % (allow_deny_values[result],
                                             self.op_to_path(op, win_id, path))

    def call_rule_path(self, (rule_regexp,), operation_path):
        return rule_regexp.match(operation_path)

    def print_rule(self, (rule_result, rule_regexp)):
        return "%s: %s" % (rule_result, rule_regexp)

    @classmethod
    def load_access_list_from_file(cls, file):
        for line in csv.reader(file):
            if not line or line[0].startswith('#'): continue
            (result, rule_regexp) = line
            yield (allow_deny_strings[result.strip()], cls.Regexp(rule_regexp.strip()))
