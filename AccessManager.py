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

    def debugPrint(self, op, winId, path, result):
        if self.debug:
            print "AccessManager: %s: %s: %s:%s" % (result, op, winId, '.'.join(path))

    def __call__(self, op, winId, path):
        self.debugPrint(op, winId, path, True)
        return True

class ListAccessManager(AccessManager):
    debugLists = False
    
    def debugPrintPath(self, opPath, result):
        if self.debug:
            print "AccessManager: %s: %s" % (result, '.'.join([str(item) for item in opPath]))

    def __call__(self, op, winId, path):
        return self.callPath((op, winId) + tuple(path))

    def callPath(self, opPath):
        lst = self.getAccessList()
        result = None
        for ruleResult, ruleScope, rulePath in lst:
            marker = '   '
            if (   (ruleScope is Constants.SUBTREE and Utils.isPrefix(rulePath, opPath))
                or (ruleScope is Constants.ONE and rulePath == opPath)):
                marker = ' ->'
                if result is None:
                    marker = '==>'
                    result = ruleResult
            if self.debugLists:
                scope = ''
                if ruleScope is Constants.SUBTREE: scope = '.*'
                print "AccessManager:  %s %s: %s%s" % (
                    marker, ruleResult, '.'.join([str(item) for item in rulePath]), scope)
        if result is None: result = False
        self.debugPrintPath(opPath, result)
        return result

    def getAccessList(self):
        return self.session.getAccessList()
