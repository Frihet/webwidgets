#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <redhog@redhog.org>
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

import types
import Webwidgets.Utils, Webwidgets.Constants
import Base, Input, Formatting

class LanguageInput(Input.ListInput):
    __attributes__ = Input.ListInput.__attributes__ + ('languages',)
    languages = {'en':u'English', 'sv':u'Svenska', 'no':u'Norsk'}
    
    def get_children(self):
        return self.languages.iteritems()

class LanguageSelector(LanguageInput):
    class Value(object):
        def __get__(self, instance, owner):
            if not hasattr(instance, 'session'):
                return None
            if instance.session.languages is None:
                return instance.get_languages({})[0]
            return instance.session.languages[0]
        def __set__(self, instance, value):
            instance.session.languages = (value,)
    value = Value()

class Dialog(Formatting.Html):
    """Dialogs provides an easy way to let the user select one of a
    few different options, while providing the user with some longer
    explanation/description of the options. Options are described
    using a dictionary of description-value pairs."""
    __wwml_html_override__ = False
    __attributes__ = Formatting.Html.__attributes__ + ('buttons',)
    buttons = {'Cancel': '0', 'Ok': '1'}
    html = """
    <div %(attr_html_attributes)s>
     <div class="dialog-head" id="%(attr_html_id)s-head">
      %(head)s
     </div>
     <div class="dialog-body" id="%(attr_html_id)s-body">
      %(body)s
     </div>
     <div class="dialog-buttons" id="%(attr_html_id)s-buttons">
      %(buttons)s
     </div>
    </div>
    """

    class Buttons(Formatting.List):
        __explicit_load__ = True

        class Button(Input.Button):
            __explicit_load__ = True
            __attributes__ = Input.Button.__attributes__ + ('value',)
            def clicked(self, path):
                self.parent.parent.notify('selected', self.value)
                return True
            
        def __init__(self, session, win_id, buttons):
            super(Dialog.Buttons, self).__init__(
                session, win_id,
                **dict([(str(value), Dialog.Buttons.Button(session, win_id, title=title, value=value))
                        for title, value in buttons.iteritems()]))
        
    def __init__(self, session, win_id, **attrs):
        super(Formatting.Html, self).__init__(
            session, win_id,
            buttons=self.Buttons(session, win_id, self.buttons),
            **attrs)

    def selected(self, path, value):
        if path != self.path: return
        self.visible = False

class Tree(Base.Input):
    """Expandable tree widget similar to the tree-view in Nautilus or
    Windows Explorer. The tree must support the renderTree() protocol."""
    
    __attributes__ = Base.StaticComposite.__attributes__ + ('tree', 'pictIcon', 'pict_expander', 'pict_indent')
    def __init__(self, session, win_id, **attrs):
        Base.Widget.__init__(self, session, win_id, **attrs)

    # FIXME: Hardcoded URL!
    pict_url = 'pictures/'
    pict_pattern = 'grime.%(name)s.png'
    pictIcon = ((('doc', '[=]'),
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

    def draw(self, output_options):
        path = self.path
        
        def renderEntry(node, sibling, res, indent=''):
            siblings = node.parent and len(node.parent.subNodes) or 1
            subNodes = len(node.subNodes)

            res = (res or '') + '<div class="Tree-Row">' + indent
            res += '<span class="%s">' % ['Tree-ShadedNode', 'Tree-Node'][node.leaf]

            node_path = path + ['node'] + node.path
            
            expander_img, expander_alt = self.pict_expander[subNodes > 0 or not node.updated
                                                         ][node.expanded
                                                           ][sibling == siblings - 1]
            expand_params = {'src': self.pict_url + self.pict_pattern % {'name':expander_img},
                            'alt': expander_alt,
                            'attr_html_id': Webwidgets.Utils.path_to_id(node_path + ['expand']),
                            'path': node_path + ['expand']}
            if subNodes or not node.updated:
                self.register_input(expand_params[path])
                res += '<input type="image" name="%(attr_html_id)s" value="%(attr_html_id)s" src="%(src)s" alt="%(alt)s" id="%(attr_html_id)s" />' % expand_params
            else:
                res += '<img src="%(src)s" alt="%(alt)s" id="%(attr_html_id)s" />' % expand_params

            select_img, select_alt = self.pictIcon[subNodes > 0][node.expanded]
            select_params = {'img_path': node_path + ['select_img'],
                            'img_id': Webwidgets.Utils.path_to_id(node_path + ['select_img']),
                            'img_src': self.pict_url + self.pict_pattern % {'name':select_img},
                            'img_alt': select_alt,
                            'label_path': node_path + ['selectLabel'],
                            'label_id': Webwidgets.Utils.path_to_id(node_path + ['selectLabel'])}
            if node.translation is not None:
                select_params['label_text'] = str(unicode(node.translation))
            elif node.path:
                select_params['label_text'] = str(unicode(node.path[-1]))
            else:
                select_params['label_text'] = str(unicode(getattr(self.tree, 'rootName', 'Root')))
                
            if node.leaf:
                self.register_input(select_params['img_path'])
                self.register_input(select_params['label_path'])
                res += ('<input type="image" name="%(img_id)s" value="%(img_id)s" src="%(img_src)s" alt="%(img_alt)s" id="%(img_id)s" />' +
                        '<input type="submit" name="%(label_id)s" value="%(label_text)s" id="%(label_id)s" />') % select_params
            else:
                res += '<img src="%(img_src)s" alt="%(img_alt)s" id="%(img_id)s" />%(label_text)s' % select_params

            res += "</span></div>\n"

            indent_img, indent_alt = self.pict_indent[sibling == siblings - 1]
            sub_indent = ' ' + indent + '<img src="%(img_src)s" alt="%(img_alt)s" />' % {
                'img_src': self.pict_url + self.pict_pattern % {'name':indent_img},
                'img_alt': indent_alt}

            return (res, (sub_indent,), {})

        return '<div class="Tree" id="%s">%s\n</div>\n' % (
            Webwidgets.Utils.path_to_id(path),
            self.tree.renderTree(renderEntry, '    '))

    def value_changed(self, path, value):
        if path != self.path: return
        if value is '': return
        subPath = path[path.index('node')+1:-1]
        action = path[-1]
        
        if action == 'expand':
            self.tree.expandPath(subPath, 1)
        elif action in ('selectLabel', 'select_img'):
            self.notify('selected', subPath)

    def selected(self, path, item):
        print '%s.selected(%s, %s)' % ('.'.join([str(x) for x in self.path]), '.'.join(path), '.'.join(item))

class Tabset(Base.StaticComposite):
    def get_pages(self, path = []):
        tabs = Webwidgets.Utils.OrderedDict()
        for name, child in self.get_children():
            #### fixme ####
            # name = "Child must be widget"
            # description = """If child is not a widget
            # but a string, this fails..."""
            #### end ####
            if not child.get_visible(child.path): continue

            page = path + [name]

            if isinstance(child, Tabset):
                tabs[name] = (page, child, child.get_pages(page))
            else:
                tabs[name] = (page, child, None)
        return tabs

    def draw_page_titles(self, output_options):
        def draw_page_titles(pages):
            if pages is None: return None
            res = Webwidgets.Utils.OrderedDict()
            for name, (page, widget, children) in pages.iteritems():
                res[name] = (page,
                             widget._(widget.get_title(widget.path), output_options),
                             draw_page_titles(children))
            return res
        return draw_page_titles(self.get_pages())

class TabbedView(Base.ActionInput, Tabset):
    """Provides a set of overlapping 'pages' with tabs, each tab
    holding some other widget, through wich a user can browse using
    the tabs."""
    __attributes__ = Base.StaticComposite.__attributes__ + ('page', 'argument_name')
    argument_name = None
    oldPage = None
    page = None

    def field_input(self, path, string_value):
        if string_value != '':
            self.page = Webwidgets.Utils.id_to_path(string_value, True)

    def field_output(self, path):
        return [unicode(Webwidgets.Utils.path_to_id(self.page, True))]

    def get_active(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        return self.active and self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, path)

    def page_changed(self, path, page):
        """Notification that the user has changed page."""
        if path != self.path: return
        if self.oldPage is not None:
            self.get_widget_by_path(self.oldPage).notify('tabBlur')
        if self.page is not None:
            self.get_widget_by_path(self.page).notify('tabFocus')
        self.oldPage = self.page

    def draw_tabs(self, output_options):
        active = self.register_input(self.path, self.argument_name)
        widget_id = Webwidgets.Utils.path_to_id(self.path)

        def draw_tabs(pages):
            tabs = []
            for name, (page, title, children) in pages.iteritems():
                info = {'disabled': ['', 'disabled="disabled"'][page == self.page or not active],
                        'attr_html_id': widget_id,
                        'page': Webwidgets.Utils.path_to_id(page),
                        'caption': title}
                if children is None:
                    tabs.append("""
                                 <li><button
                                      type="submit"
                                      %(disabled)s
                                      id="%(attr_html_id)s-_-%(page)s"
                                      name="%(attr_html_id)s"
                                      value="%(page)s">%(caption)s</button></li>
                                """ % info)
                else:
                    info['children'] = draw_tabs(children)
                    tabs.append("<li><span>%(caption)s</span>%(children)s</li>" % info)
            return """
                    <ul class="tabs">
                     %(tabs)s
                    </ul>
                   """ % {'tabs': '\n'.join(tabs)}
        return draw_tabs(self.draw_page_titles(output_options))
        
    def draw(self, output_options):
        return """
               <div %(attr_html_attributes)s>
                %(tabs)s
                <div class="page">
                 %(page)s
                </div>
               </div>
               """ % {'attr_html_attributes': self.draw_html_attributes(self.path),
                      'page': self.draw_child(self.get_widget_by_path(self.page).path, self.get_widget_by_path(self.page), output_options, True),
                      'tabs': self.draw_tabs(output_options)}

class Hide(Base.StaticComposite):
    """
    A hide/show widget

    Change the value of the title variable to change the text in the button.

    TODO:
    Implement an alternative javascript implementation for faster update at the expense of longer reloads
    """

    class hideButton(Input.ToggleButton):
        true_title = "Hide"
        false_title = "Show"

    def draw(self, path):
        self['child'].visible = self['hideButton'].value
        children = self.draw_children(path, invisible_as_empty=True, include_attributes=True)
        return """<div %(attr_html_attributes)s>%(hideButton)s %(child)s</div>""" % children
 
