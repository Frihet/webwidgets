#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moller@freecode.no>
# Copyright (C) 2007 FreeCode AS, Axel Liljencrantz <axel.liljencrantz@freecode.no>

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

"""Widgets for user input.
"""

import types, math
import Webwidgets.Utils
import Webwidgets.Constants
import Webwidgets.Widgets.Base

class TreeModelNode(object):
    def __init__(self, tree, parent = None, name = 'Unknown', value = None):
        self.tree = tree
        self.parent = parent

        self.name = name
        self.value = None

        self.expanded = False

    class Leaf(object):
        def __get__(self, instance, owner):
            return instance.value is not None
    leaf = Leaf()
    
    class SubNodes(object):
        def __get__(self, instance, owner):
            return {}
    sub_nodes = SubNodes()

    class Expandable(object):
        def __get__(self, instance, owner):
            return len(instance.sub_nodes) > 0
    expandable = Expandable()

def prefix_to_string(prefix):
    res = []
    prefix = list(prefix)
    if len(prefix[-1]) > 1:
        res.append("[%s - %s]" % prefix[-1])
        del prefix[-1]
    prefix.reverse()
    if len(prefix):
        res[0:0] = [""]
        for item in prefix:
            if len(item) == 1:
                res[0] += item
    return ' + '.join(res)

class TreeModelGroupingWrapperNode(TreeModelNode):
    Node = TreeModelNode
    limit = 10
    
    def __init__(self, tree, parent = None, wrapped = None, prefix = ()):
        assert prefix is not None
        self.wrapped = wrapped or self.Node(tree)
        self.prefix = prefix
        name = self.wrapped.name
        if prefix:
            name = "Starting with %s" % (prefix_to_string(prefix),)
        self.old_result = {}
        self.new_result = {}
        TreeModelNode.__init__(self, tree, parent, name = name)

    class Value(object):
        def __get__(self, instance, owner):
            if instance.prefix:
                return None
            return instance.wrapped.value
        def __set__(self, instance, value):
            pass
    value = Value()

    class Leaf(object):
        def __get__(self, instance, owner):
            if instance.prefix:
                return False
            return instance.wrapped.leaf
    leaf = Leaf()

    class SubNodes(object):
        def get_node(self, node, key, wrapped = None, prefix = ()):
            key = unicode(key)
            if (    key in node.old_result
                and (   (    wrapped is None
                         and prefix is None)
                     or (    node.old_result[key].wrapped is wrapped
                         and node.old_result[key].prefix == prefix))):
                res = node.old_result[key]
            else:
                res = type(node)(
                    node.tree, node, wrapped, prefix)
            node.new_result[key] = res
            return res

        def match_prefix(self, prefix, data):
            p_pos = d_pos = 0
            while p_pos < len(prefix) and d_pos < len(data):
                p_node = prefix[p_pos]
                d_node = data[d_pos]
                if len(p_node) == 1:
                    if d_node != p_node:
                        return False
                    p_pos += 1
                    d_pos += 1
                else:
                    if not (ord(p_node[0]) <= ord(d_node) <= ord(p_node[1])):
                        return False
                    p_pos += 1
                    # Do not increment d_pos!
            if d_pos >= len(data):
                return False
            return (data[:d_pos], data[d_pos:])

        def extend_prefix(self, prefix, datas):
            new_prefixlen = len(prefix) + 1
            return set([prefix + tuple(tail[:1])
                        for (head, tail) in
                        [self.match_prefix(prefix, data)
                         for data in datas]])

        def __get__(self, instance, owner):
            sub_nodes = instance.wrapped.sub_nodes
            keys = [key for key in sub_nodes.keys()
                    if self.match_prefix(instance.prefix, key) is not False]
            instance.old_result = instance.new_result
            instance.new_result = Webwidgets.Utils.OrderedDict()
            if len(keys) > instance.limit:
                prefixlen = len(instance.prefix)
                new_prefixes = set([instance.prefix])
                while len(new_prefixes) == 1:
                    new_prefixes = self.extend_prefix(new_prefixes.pop(), keys)
                if len(new_prefixes) > instance.limit:
                    common_new_prefix = iter(new_prefixes).next()[:-1]
                    new_prefixes = [new_prefix[-1] for new_prefix in new_prefixes]
                    new_prefixes.sort(lambda x,y: cmp(ord(x), ord(y)))
                    new_prefixes = [new_prefixes[pos * instance.limit:
                                                 pos * instance.limit + instance.limit]
                                    for pos
                                    in xrange(0, int(math.ceil(float(len(new_prefixes))
                                                              / instance.limit)))]
                    for new_prefix in new_prefixes:
                        new_prefix = (new_prefix[0], new_prefix[-1])
                        self.get_node(
                            instance, new_prefix, instance.wrapped,
                            common_new_prefix + (new_prefix,))
                else:
                    for new_prefix in new_prefixes:
                        if len(new_prefix) > prefixlen:
                            self.get_node(
                                instance, new_prefix, instance.wrapped, new_prefix)
                        else:
                            self.get_node(
                                instance, new_prefix, sub_nodes[new_prefix])
            else:
                for key in keys:
                    self.get_node(
                        instance, key, sub_nodes[key])
            return instance.new_result
    sub_nodes = SubNodes()

class TreeModel(object):
    Node = TreeModelNode

    def __init__(self, root_node = None):
        self.root_node = root_node or self.Node(self)

    def _(self, message, output_options):
        return unicode(message)

    def get_node(self, path):
        node = self.root_node
        for item in path:
            node = node.sub_nodes[item]
        return node

    def expand(self, path):
        self.get_node(path).expanded = True

    def collapse(self, path):
        self.get_node(path).expanded = False

    def toggle_expanded(self, path):
        node = self.get_node(path)
        node.expanded = not node.expanded
        
    def traverse_tree(self, traverse_entry, traverse_sub_entries, res, *args, **kw):
        def traverse_tree_entries(path, node, sub_node_nr, res, *args, **kw):
            (nres, nargs, nkw) = traverse_entry(path, node, sub_node_nr, res, *args, **kw)
            if traverse_sub_entries(path, node, res, *args, **kw):
                sub_nodes = node.sub_nodes
                for sub_node_nr, (name, sub_node) in enumerate(sub_nodes.iteritems()):
                    nres = traverse_tree_entries(
                        path + [name], sub_node, sub_node_nr, nres, *nargs, **nkw)
            return nres
        return traverse_tree_entries([], self.root_node, 0, res, *args, **kw)

    def render_tree(self, render_entry, *args, **kw):
        def traverse_entry(path, node, *arg, **kw):
            return render_entry(path, node, *arg, **kw)
        def render_sub_entries(path, node, *arg, **kw):
            return node.expanded
        return self.traverse_tree(traverse_entry, render_sub_entries, '', *args, **kw)

    def render_tree_to_text(self, output_options):
        pict_icon = (('[=]', '[=]'),
                     ('\\_\\', '\\_/'))            
        pict_expander = ((('|--', '`--'),
                          ('|--', '`--')),
                         (('|-+', '`-+'),
                          ('|-.', '`-.')))
        def render_entry(path, node, sibling, res, indent=''):
            siblings = node.parent and len(node.parent.sub_nodes) or 1
            res += indent
            res += pict_expander[node.expandable][node.expanded][sibling == siblings - 1]
            res += pict_icon[node.expandable][node.expanded]
            res += self._(node.name, output_options)
            res += "\n"
            return (res,
                    (indent + ['|  ', '   '][sibling == siblings - 1],),
                    {})

        return self.render_tree(render_entry)


class Tree(Webwidgets.Widgets.Base.ActionInput, Webwidgets.Widgets.Base.DirectoryServer):
    """Expandable tree widget similar to the tree-view in Nautilus or
    Windows Explorer. The tree must support the render_tree() protocol."""

    TreeModel = TreeModel

    pict_pattern = 'grime.%(name)s.png'
    pict_icon = ((('doc', '[=]'),
                 ('doc', '[=]')),
                (('dir', '\\_\\'),
                 ('dir.open', '\\_/')))  
    pict_expander = (((('middle', '|--'),
                      ('end', '`--')),
                     (('middle', '|--'),
                      ('end', '`--'))),
                    ((('middle.expandable', '|-+'),
                      ('end.expandable', '`-+')),
                     (('middle.expanded', '|--'),
                      ('end.expanded', '`--'))))

    pict_indent = (('vertical', '|&nbsp;&nbsp;'),
                  ('empty', '&nbsp;&nbsp;&nbsp;'))

    def __init__(self, session, win_id, **attrs):
        Webwidgets.Widgets.Base.Input.__init__(self, session, win_id, **attrs)
        if not hasattr(self, 'tree'):
            self.tree = self.TreeModel()

    def draw(self, output_options):
        widget_path = self.path

        def get_picture(**params):
            #return '/junk/Tree.scripts/' + self.pict_pattern % params
            return self.calculate_url(
                {'widget_class': 'Webwidgets.Tree',
                 'location': [self.pict_pattern % params]},
                {})
        
        def render_entry(path, node, sibling, res, indent=''):
            siblings = node.parent and len(node.parent.sub_nodes) or 1

            res = (res or '') + '<div class="Tree-Row">' + indent
            res += '<span class="%s">' % ['Tree-ShadedNode', 'Tree-Node'][node.leaf]

            node_path = widget_path + ['node'] + path
            
            expander_img, expander_alt = self.pict_expander[node.expandable
                                                            ][node.expanded
                                                              ][sibling == siblings - 1]
            expand_params = {'src': get_picture(name = expander_img),
                             'alt': expander_alt,
                             'html_id': Webwidgets.Utils.path_to_id(node_path + ['expand']),
                             'path': node_path + ['expand']}
            if node.expandable:
                self.register_input(expand_params['path'])
                res += '<input type="image" name="%(html_id)s" value="%(html_id)s" src="%(src)s" alt="%(alt)s" id="%(html_id)s" />' % expand_params
            else:
                res += '<img src="%(src)s" alt="%(alt)s" id="%(html_id)s" />' % expand_params

            select_img, select_alt = self.pict_icon[node.expandable][node.expanded]
            select_params = {'img_path': node_path + ['select_img'],
                            'img_id': Webwidgets.Utils.path_to_id(node_path + ['select_img']),
                            'img_src': get_picture(name = select_img),
                            'img_alt': select_alt,
                            'label_path': node_path + ['select_label'],
                            'label_id': Webwidgets.Utils.path_to_id(node_path + ['select_label'])}
            select_params['label_text'] = self.tree._(node.name, output_options)
                
            if node.leaf:
                self.register_input(select_params['img_path'])
                self.register_input(select_params['label_path'])
                res += ('<input type="image" name="%(img_id)s" value="%(img_id)s" src="%(img_src)s" alt="%(img_alt)s" id="%(img_id)s" />' +
                        """<button type="submit" name="%(label_id)s" value="%(label_text)s" title="%(label_text)s" id="%(label_id)s"><span class='button-text'>%(label_text)s</span></button>""") % select_params
            else:
                res += '<img src="%(img_src)s" alt="%(img_alt)s" id="%(img_id)s" />%(label_text)s' % select_params

            res += "</span></div>\n"

            indent_img, indent_alt = self.pict_indent[sibling == siblings - 1]
            sub_indent = ' ' + indent + '<img src="%(img_src)s" alt="%(img_alt)s" />' % {
                'img_src': get_picture(name = indent_img),
                'img_alt': indent_alt}

            return (res, (sub_indent,), {})

        return '<div %(html_attributes)s>%(tree)s\n</div>\n' % {
            'html_attributes': self.html_attributes,
            'tree': self.tree.render_tree(render_entry, '    ')}

    def field_input(self, path, string_value):
        if string_value == '': return
        sub_path = path[path.index('node')+1:-1]
        action = path[-1]
        
        if action == 'expand':
            self.tree.toggle_expanded(sub_path)
        elif action in ('select_label', 'select_img'):
            self.notify('selected', self.tree.get_node(sub_path).value)

    def field_output(self, path):
        return []

#     def selected(self, path, item):
#         print '%s.selected(%s, %s)' % ('.'.join([str(x) for x in self.path]),
#                                        '.'.join(path),
#                                        item)
