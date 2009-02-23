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


#### fixme ####
# name = "Generalize WidgetPath to some kind of WidgetSelector"
# description = """Generalize WidgetPath to some kind of
# WidgetSelector set of classes that can select widgets based on
# several different criterias, esp. doing what
# get_widgets_by_attribute is doing."""
#### end ####

class WidgetPath(object):
    """WidgetPath is a representation of a path that identifies some
    point in the widget tree (that is, some widget in your
    application).

    Relative paths consists of a number of steps (the level) to walk
    'upwards' in the tree (like cd .. in unix), and then some path to
    walk downwards from that point. Example: 3:foo-bar-fie means go
    three levels up, then down along the branch foo and bar and end up
    at the node fie.

    Absolute paths consists of just the path to walk downward from the
    root. Example: root:foo-bar-fie means to go down along the branch
    foo and bar and end up at the node fie.
    """
    def __new__(cls, path, levels = 0, path_as_list = False):
        """Create a new WidgetPath instance. There are three formats
        for creating WidgetPath instances:

         - 'WidgetPath(string path)' The string should be of the
           format 3:foo-bar-fie, which is also the format output from
           L{__str__}.

         - 'WidgetPath(list path, int levels = 0)' creates a
           relative path from its two components - a list of strings
           representing the path, and an integer for the levels to
           walk upwards or None for an absolute path.

         - 'WidgetPath(WidgetPath path)' copies an existing path.
        """

        if path is None:
            return None

        self = super(WidgetPath, cls).__new__(cls)
        
        if isinstance(path, basestring):
            if ':' in path:
                levels, path = path.split(':')
                if levels == 'root':
                    levels = None
                else:
                    levels = int(levels)
            if path:
                path = path.split('-')
            else:
                path = []
        elif isinstance(path, WidgetPath):
            levels = path.levels
            path = path.path
        self.levels = levels
        self.path = list(path)

        # Both relative and absolute paths can be represented as
        # simple lists... This ambiguity is intentional.
        if path_as_list and not self.levels:
            return self.path
        return self
        
    def __add__(self, child):
        """If a is rooted at c and b is rooted at a, then a + b
        references b and is rooted at c."""
        if not isinstance(child, WidgetPath):
            child = type(self)(child)
        if child.levels is None:
            raise ValueError("Can not add an absolute path to a relative path: %s + %s" % (self, child))
        if child.levels > len(self.path):
            if self.levels is None:
                raise ValueError("Can not add a relative pointing above the root of an absolute path: %s + %s" % (self, child))
            levels = self.levels + child.levels - len(self.path)
            path = child.path
        else:
            levels = self.levels
            path = self.path
            if child.levels:
                path = path[:-child.levels]
            path = path + child.path
        return type(self)(path, levels)
    
    def __sub__(self, child):
        """If a and b are both rooted at c, a - b will reference a but
        rooted at b. This _assumes_ a actually resides under b, if
        not, the result is: garbage in - garbage out :P. Examples:
        '3:foo-bar-fie-naja' - '3:foo-bar' = '0:fie-naja'
        '3:foo-bar-fie-naja' - '3:foo-xxx' = '1:bar-fie-naja'
        
        And the 'let's just assume things' ones:
        '4:xxx-foo-bar-fie-naja' - '3:foo-bar' = '0:fie-naja'
        '3:foo-bar-fie-naja' - '4:xxx-foo-bar' = '0:fie-naja'
        
        """
        if not isinstance(child, WidgetPath):
            child = type(self)(child)

        self_path = self.path
        child_path = child.path

        if (self.levels is None) != (child.levels is None):
            raise ValueError("Can not subtract relative path from absolute or absolute from relative: %s - %s" % (self, child))

        if self.levels is not None:
            if self.levels > child.levels:
                self_path = self_path[self.levels - child.levels:]
            elif self.levels < child.levels:
                child_path = child_path[child.levels - self.levels:]

        # self and child paths are now rooted at the same place
        prefix_len = len(common_prefix(self_path, child_path))
        path = self_path[prefix_len:]
        levels = len(child_path) - prefix_len
        return type(self)(path, levels)
    
    def __radd__(self, child):
        return type(self)(child) + self
    def __rsub__(self, child):
        return type(self)(child) - self

    def __iter__(self):
        if self.levels:
            raise TypeError('Unable to iterate over a relative path with non-zero levels')
        return iter(self.path)

    def __unicode__(self):
        levels = 'root'
        if self.levels is not None:
            levels = self.levels
        return "%s:%s" % (levels, u'-'.join([
            item.replace('\\', '\\\\').replace('-', '\\.')
            for item in self.path]))

    def __str__(self):
        return str(unicode(self))

def path_to_id(path):
    """Converts a widget path to a string suitable for use in a HTML
    id attribute"""
    return unicode(WidgetPath(path, None))

def id_to_path(id):
    """Convert a string previously created using L{path_to_id} back into
    a widget path."""
    return WidgetPath(id, path_as_list=True)
