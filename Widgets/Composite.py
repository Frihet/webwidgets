# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <redhog@redhog.org>

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
            
        def __init__(self, session, winId, buttons):
            super(Dialog.Buttons, self).__init__(
                session, winId,
                **dict([(str(value), Dialog.Buttons.Button(session, winId, title=title, value=value))
                        for title, value in buttons.iteritems()]))
        
    def __init__(self, session, winId, **attrs):
        super(Formatting.Html, self).__init__(
            session, winId,
            buttons=self.Buttons(session, winId, self.buttons),
            **attrs)

    def selected(self, path, value):
        if path != self.path(): return
        self.visible = False

class Tree(Base.Input):
    """Expandable tree widget similar to the tree-view in Nautilus or
    Windows Explorer. The tree must support the renderTree() protocol."""
    
    __attributes__ = Base.StaticComposite.__attributes__ + ('tree', 'pictIcon', 'pictExpander', 'pictIndent')
    def __init__(self, session, winId, **attrs):
        Base.Widget.__init__(self, session, winId, **attrs)

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

    def draw(self, outputOptions):
        path = self.path()
        
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
                            'attr_html_id': Webwidgets.Utils.pathToId(nodePath + ['expand']),
                            'path': nodePath + ['expand']}
            if subNodes or not node.updated:
                self.registerInput(expandParams[path])
                res += '<input type="image" name="%(attr_html_id)s" value="%(attr_html_id)s" src="%(src)s" alt="%(alt)s" id="%(attr_html_id)s" />' % expandParams
            else:
                res += '<img src="%(src)s" alt="%(alt)s" id="%(attr_html_id)s" />' % expandParams

            selectImg, selectAlt = self.pictIcon[subNodes > 0][node.expanded]
            selectParams = {'imgPath': nodePath + ['selectImg'],
                            'imgId': Webwidgets.Utils.pathToId(nodePath + ['selectImg']),
                            'imgSrc': self.pictUrl + self.pictPattern % {'name':selectImg},
                            'imgAlt': selectAlt,
                            'labelPath': nodePath + ['selectLabel'],
                            'labelId': Webwidgets.Utils.pathToId(nodePath + ['selectLabel'])}
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
            Webwidgets.Utils.pathToId(path),
            self.tree.renderTree(renderEntry, '    '))

    def valueChanged(self, path, value):
        if path != self.path(): return
        if value is '': return
        subPath = path[path.index('node')+1:-1]
        action = path[-1]
        
        if action == 'expand':
            self.tree.expandPath(subPath, 1)
        elif action in ('selectLabel', 'selectImg'):
            self.notify('selected', subPath)

    def selected(self, path, item):
        print '%s.selected(%s, %s)' % ('.'.join([str(x) for x in self.path()]), '.'.join(path), '.'.join(item))

class TabbedView(Base.Input, Base.StaticComposite):
    """Provides a set of overlapping 'pages' with tabs, each tab
    holding some other widget, through wich a user can browse using
    the tabs."""
    __attributes__ = Base.StaticComposite.__attributes__ + ('page', 'argumentName')
    argumentName = None
    page = None

    def fieldInput(self, path, stringValue):
        if stringValue != '':
            self.page = stringValue

    def fieldOutput(self, path):
        return [unicode(self.page)]

    def getActive(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        return self.active and self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.winId, path)

    def pageChanged(self, path, page):
        """Notification that the user has changed page."""
        if path != self.path(): return

    def draw(self, outputOptions):
        active = self.registerInput(self.path(), self.argumentName)

        widgetId = Webwidgets.Utils.pathToId(self.path())
        tabs = '\n'.join(["""
                          <li><button
                               type="submit"
                               %(disabled)s
                               id="%(attr_html_id)s_%(page)s"
                               name="%(attr_html_id)s"
                               value="%(page)s" />%(caption)s</button></li>
                          """ % {'disabled': ['', 'disabled="true"'][page == self.page or not active],
                                 'attr_html_id': widgetId,
                                 'page':page,
                                 'caption':child.getTitle(self.path() + [page])}
                          for page, child in self.getChildren()
                          #### fixme ####
                          # name = "Child must be widget"
                          # description = """If child is not a widget
                          # but a string, this fails..."""
                          #### end ####
                          if child.getVisible(child.path())])
        return """
               <div %(attr_htmlAttributes)s>
                <ul class="tabs">
                 %(tabs)s
                </ul>
                <div class="page">
                 %(page)s
                </div>
               </div>
               """ % {'attr_htmlAttributes': self.drawHtmlAttributes(self.path()),
                      'page': self.drawChild(self.path() + [self.page], self.getChild(self.page), outputOptions, True),
                      'tabs': tabs}
