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
    
    def getChildren(self):
        return self.languages.iteritems()

class LanguageSelector(LanguageInput):
    class Value(object):
        def __get__(self, instance, owner):
            if not hasattr(instance, 'session'):
                return None
            if instance.session.languages is None:
                return instance.getLanguages({})[0]
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
    __children__ = Formatting.Html.__children__ + ('head', 'body')
    buttons = {'Cancel': '0', 'Ok': '1'}
    html = """
    <div %(attr_htmlAttributes)s>
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
    
    __attributes__ = Base.StaticComposite.__attributes__ + ('tree', 'pictIcon', 'pictExpander', 'pictIndent')
    def __init__(self, session, win_id, **attrs):
        Base.Widget.__init__(self, session, win_id, **attrs)

    # FIXME: Hardcoded URL!
    pictUrl = 'pictures/'
    pictPattern = 'grime.%(name)s.png'
    pictIcon = ((('doc', '[=]'),
                 ('doc', '[=]')),
                (('dir', '\\_\\'),
                 ('dir.open', '\\_/')))            
    pictExpander = (((('middle', '|--'),
                      ('end', '`--')),
                     (('middle', '|--'),
                      ('end', '`--'))),
                    ((('middle.expandable', '|-+'),
                      ('end.expandable', '`-+')),
                     (('middle.expanded', '|--'),
                      ('end.expanded', '`--'))))

    pictIndent = (('vertical', '|&nbsp;&nbsp;'),
                  ('empty', '&nbsp;&nbsp;&nbsp;'))

    def draw(self, output_options):
        path = self.path
        
        def renderEntry(node, sibling, res, indent=''):
            siblings = node.parent and len(node.parent.subNodes) or 1
            subNodes = len(node.subNodes)

            res = (res or '') + '<div class="Tree-Row">' + indent
            res += '<span class="%s">' % ['Tree-ShadedNode', 'Tree-Node'][node.leaf]

            nodePath = path + ['node'] + node.path
            
            expanderImg, expanderAlt = self.pictExpander[subNodes > 0 or not node.updated
                                                         ][node.expanded
                                                           ][sibling == siblings - 1]
            expandParams = {'src': self.pictUrl + self.pictPattern % {'name':expanderImg},
                            'alt': expanderAlt,
                            'attr_html_id': Webwidgets.Utils.path_to_id(nodePath + ['expand']),
                            'path': nodePath + ['expand']}
            if subNodes or not node.updated:
                self.registerInput(expandParams[path])
                res += '<input type="image" name="%(attr_html_id)s" value="%(attr_html_id)s" src="%(src)s" alt="%(alt)s" id="%(attr_html_id)s" />' % expandParams
            else:
                res += '<img src="%(src)s" alt="%(alt)s" id="%(attr_html_id)s" />' % expandParams

            selectImg, selectAlt = self.pictIcon[subNodes > 0][node.expanded]
            selectParams = {'imgPath': nodePath + ['selectImg'],
                            'imgId': Webwidgets.Utils.path_to_id(nodePath + ['selectImg']),
                            'imgSrc': self.pictUrl + self.pictPattern % {'name':selectImg},
                            'imgAlt': selectAlt,
                            'labelPath': nodePath + ['selectLabel'],
                            'labelId': Webwidgets.Utils.path_to_id(nodePath + ['selectLabel'])}
            if node.translation is not None:
                selectParams['labelText'] = str(unicode(node.translation))
            elif node.path:
                selectParams['labelText'] = str(unicode(node.path[-1]))
            else:
                selectParams['labelText'] = str(unicode(getattr(self.tree, 'rootName', 'Root')))
                
            if node.leaf:
                self.registerInput(selectParams['imgPath'])
                self.registerInput(selectParams['labelPath'])
                res += ('<input type="image" name="%(imgId)s" value="%(imgId)s" src="%(imgSrc)s" alt="%(imgAlt)s" id="%(imgId)s" />' +
                        '<input type="submit" name="%(labelId)s" value="%(labelText)s" id="%(labelId)s" />') % selectParams
            else:
                res += '<img src="%(imgSrc)s" alt="%(imgAlt)s" id="%(imgId)s" />%(labelText)s' % selectParams

            res += "</span></div>\n"

            indentImg, indentAlt = self.pictIndent[sibling == siblings - 1]
            subIndent = ' ' + indent + '<img src="%(imgSrc)s" alt="%(imgAlt)s" />' % {
                'imgSrc': self.pictUrl + self.pictPattern % {'name':indentImg},
                'imgAlt': indentAlt}

            return (res, (subIndent,), {})

        return '<div class="Tree" id="%s">%s\n</div>\n' % (
            Webwidgets.Utils.path_to_id(path),
            self.tree.renderTree(renderEntry, '    '))

    def valueChanged(self, path, value):
        if path != self.path: return
        if value is '': return
        subPath = path[path.index('node')+1:-1]
        action = path[-1]
        
        if action == 'expand':
            self.tree.expandPath(subPath, 1)
        elif action in ('selectLabel', 'selectImg'):
            self.notify('selected', subPath)

    def selected(self, path, item):
        print '%s.selected(%s, %s)' % ('.'.join([str(x) for x in self.path]), '.'.join(path), '.'.join(item))

class Tabset(Base.StaticComposite):
    def getPages(self, path = []):
        tabs = Webwidgets.Utils.OrderedDict()
        for name, child in self.getChildren():
            #### fixme ####
            # name = "Child must be widget"
            # description = """If child is not a widget
            # but a string, this fails..."""
            #### end ####
            if not child.getVisible(child.path): continue

            page = path + [name]

            if isinstance(child, Tabset):
                tabs[name] = (page, child, child.getPages(page))
            else:
                tabs[name] = (page, child, None)
        return tabs

    def drawPageTitles(self, output_options):
        def drawPageTitles(pages):
            if pages is None: return None
            res = Webwidgets.Utils.OrderedDict()
            for name, (page, widget, children) in pages.iteritems():
                res[name] = (page,
                             widget._(widget.getTitle(widget.path), output_options),
                             drawPageTitles(children))
            return res
        return drawPageTitles(self.getPages())

class TabbedView(Base.ActionInput, Tabset):
    """Provides a set of overlapping 'pages' with tabs, each tab
    holding some other widget, through wich a user can browse using
    the tabs."""
    __attributes__ = Base.StaticComposite.__attributes__ + ('page', 'argumentName')
    argumentName = None
    oldPage = None
    page = None

    def field_input(self, path, stringValue):
        if stringValue != '':
            self.page = Webwidgets.Utils.id_to_path(stringValue, True)

    def field_output(self, path):
        return [unicode(Webwidgets.Utils.path_to_id(self.page, True))]

    def get_active(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        return self.active and self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.win_id, path)

    def pageChanged(self, path, page):
        """Notification that the user has changed page."""
        if path != self.path: return
        if self.oldPage is not None:
            self.getWidgetByPath(self.oldPage).notify('tabBlur')
        if self.page is not None:
            self.getWidgetByPath(self.page).notify('tabFocus')
        self.oldPage = self.page

    def drawTabs(self, output_options):
        active = self.registerInput(self.path, self.argumentName)
        widgetId = Webwidgets.Utils.path_to_id(self.path)

        def drawTabs(pages):
            tabs = []
            for name, (page, title, children) in pages.iteritems():
                info = {'disabled': ['', 'disabled="disabled"'][page == self.page or not active],
                        'attr_html_id': widgetId,
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
                    info['children'] = drawTabs(children)
                    tabs.append("<li><span>%(caption)s</span>%(children)s</li>" % info)
            return """
                    <ul class="tabs">
                     %(tabs)s
                    </ul>
                   """ % {'tabs': '\n'.join(tabs)}
        return drawTabs(self.drawPageTitles(output_options))
        
    def draw(self, output_options):
        return """
               <div %(attr_htmlAttributes)s>
                %(tabs)s
                <div class="page">
                 %(page)s
                </div>
               </div>
               """ % {'attr_htmlAttributes': self.drawHtmlAttributes(self.path),
                      'page': self.drawChild(self.getWidgetByPath(self.page).path, self.getWidgetByPath(self.page), output_options, True),
                      'tabs': self.drawTabs(output_options)}

class Hide(Base.StaticComposite):
    """
    A hide/show widget

    Change the value of the title variable to change the text in the button.

    TODO:
    Implement an alternative javascript implementation for faster update at the expense of longer reloads
    """

    class hideButton(Input.ToggleButton):
        trueTitle = "Hide"
        falseTitle = "Show"

    def draw(self, path):
        self['child'].visible = self['hideButton'].value
        children = self.drawChildren(path, invisibleAsEmpty=True, includeAttributes=True)
        return """<div %(attr_htmlAttributes)s>%(hideButton)s %(child)s</div>""" % children
 
