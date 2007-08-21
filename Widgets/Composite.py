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



class LabelWidget(Base.StaticCompositeWidget):
    """Renders a label for an input field. The input field can be
    specified either as the widget itself, or a
    L{Webwidgets.Utils.RelativePath} to the widget"""
    
    __attributes__ = Base.StaticCompositeWidget.__attributes__ + ('target',)
    __children__ = ('label',)

    target = []
    """The widget this widget is a label for. This is either the
    actual widget, or a L{Webwidgets.Utils.RelativePath} referencing
    the widget.
    """

    def draw(self, path):
        if isinstance(self.target, Base.Widget):
            target = self.target
        else:
            target = self + self.target
        targetPath = target.path()
        res = self.drawChildren(path)
        res['error'] = ''
        if target.error is not None:
           res['error'] = """<span class="error">(%s)</span>""" % (target.error,)
        res['id'] = Webwidgets.Utils.pathToId(path)
        res['attr_classesStr'] = self.classesStr
        res['target'] = Webwidgets.Utils.pathToId(targetPath)
        return """<label class="%(attr_classesStr)s" for="%(target)s">
        %(label)s
        %(error)s
        </label>""" % res

class FieldWidget(LabelWidget):
    __no_classes_name__ = True
    __wwml_html_override__ = False
    __children__ = LabelWidget.__children__ + ('field',)
    
    def draw(self, path):
        if isinstance(self.target, Base.Widget):
            target = self.target
        else:
            target = self + ['field'] + self.target
        targetPath = target.path()
        res = self.drawChildren(path)
        res['error'] = ''
        if target.error is not None:
           res['error'] = """<span class="error">(%s)</span>""" % (target.error,)
        res['id'] = Webwidgets.Utils.pathToId(path)
        res['attr_classesStr'] = self.classesStr
        res['target'] = Webwidgets.Utils.pathToId(targetPath)
        return """<div id='%(id)s' class='%(attr_classesStr)s'>
                   <label for="%(target)s">
                    %(label)s%(error)s:
                   </label>
                   <span class="field">
                    %(field)s
                   </span>
                  </div>
                  """ % res

class FieldgroupWidget(Formatting.ListWidget):
    class pre(Base.Widget):
        def draw(self, path):
            return """<div id="%(id)s" classes="%(attr_classesStr)s">""" % {
                'id': Webwidgets.Utils.pathToId(self.parent.path()),
                'attr_classesStr': self.parent.classesStr}
    post = "</div>\n"


class DialogWidget(Formatting.HtmlWidget):
    """Dialogs provides an easy way to let the user select one of a
    few different options, while providing the user with some longer
    explanation/description of the options. Options are described
    using a dictionary of description-value pairs."""
    __wwml_html_override__ = False
    __attributes__ = Formatting.HtmlWidget.__attributes__ + ('buttons',)
    __children__ = Formatting.HtmlWidget.__children__ + ('head', 'body')
    buttons = {'Cancel': '0', 'Ok': '1'}
    html = """
    <div class="dialog" id="%(id)s">
     <div class="dialog-head" id="%(id)s-head">
      %(head)s
     </div>
     <div class="dialog-body" id="%(id)s-body">
      %(body)s
     </div>
     <div class="dialog-buttons" id="%(id)s-buttons">
      %(buttons)s
     </div>
    </div>
    """

    class Buttons(Formatting.ListWidget):
        __explicit_load__ = True

        class Button(Input.ButtonInputWidget):
            __explicit_load__ = True
            __attributes__ = Input.ButtonInputWidget.__attributes__ + ('value',)
            def clicked(self, path):
                self.parent.parent.notify('selected', self.value)
                return True
            
        def __init__(self, session, winId, buttons):
            super(DialogWidget.Buttons, self).__init__(
                session, winId,
                **dict([(str(value), DialogWidget.Buttons.Button(session, winId, title=title, value=value))
                        for title, value in buttons.iteritems()]))
        
    def __init__(self, session, winId, **attrs):
        super(Formatting.HtmlWidget, self).__init__(
            session, winId,
            buttons=self.Buttons(session, winId, self.buttons),
            **attrs)

    def selected(self, path, value):
        if path != self.path(): return
        self.visible = False

class TreeWidget(Base.InputWidget):
    """Expandable tree widget similar to the tree-view in Nautilus or
    Windows Explorer. The tree must support the renderTree() protocol."""
    
    __attributes__ = Base.StaticCompositeWidget.__attributes__ + ('tree', 'pictIcon', 'pictExpander', 'pictIndent')
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

    def draw(self, path):
        def renderEntry(node, sibling, res, indent=''):
            siblings = node.parent and len(node.parent.subNodes) or 1
            subNodes = len(node.subNodes)

            res = (res or '') + '<div class="TreeWidget-Row">' + indent
            res += '<span class="%s">' % ['TreeWidget-ShadedNode', 'TreeWidget-Node'][node.leaf]

            nodePath = path + ['node'] + node.path
            
            expanderImg, expanderAlt = self.pictExpander[subNodes > 0 or not node.updated
                                                         ][node.expanded
                                                           ][sibling == siblings - 1]
            expandParams = {'src': self.pictUrl + self.pictPattern % {'name':expanderImg},
                            'alt': expanderAlt,
                            'id': Webwidgets.Utils.pathToId(nodePath + ['expand']),
                            'path': nodePath + ['expand']}
            if subNodes or not node.updated:
                self.registerInput(expandParams[path])
                res += '<input type="image" name="%(id)s" value="%(id)s" src="%(src)s" alt="%(alt)s" id="%(id)s" />' % expandParams
            else:
                res += '<img src="%(src)s" alt="%(alt)s" id="%(id)s" />' % expandParams

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

        return '<div class="TreeWidget" id="%s">%s\n</div>\n' % (
            Webwidgets.Utils.pathToId(path),
            self.tree.renderTree(renderEntry, '    '))

    def getValue(self, path):
        return Webwidgets.Utils.pathToId(path) + 'unselected'

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

class TabbedViewWidget(Base.InputWidget, Base.StaticCompositeWidget):
    """Provides a set of overlapping 'pages' with tabs, each tab
    holding some other widget, through wich a user can browse using
    the tabs."""
    __attributes__ = Base.StaticCompositeWidget.__attributes__ + ('page', 'argumentName')
    argumentName = None
    page = None

    def getValue(self, path):
        return self.page

    def valueChanged(self, path, value):
        if path != self.path(): return
        if value is '': return
        self.notify('repaged', value)

    def getActive(self, path):
        """@return: Whether the widget is allowing input from the user
        or not.
        """
        return self.active and self.session.AccessManager(Webwidgets.Constants.REARRANGE, self.winId, path)

    def repaged(self, path, page):
        """Notification that the user has changed page."""
        if path != self.path(): return
        self.page = page

    def draw(self, path):
        active = self.registerInput(path, self.argumentName)

        widgetId = Webwidgets.Utils.pathToId(path)
        tabs = '\n'.join(["""
                          <li><button
                               type="submit"
                               %(disabled)s
                               id="%(id)s_%(page)s"
                               name="%(id)s"
                               value="%(page)s" />%(caption)s</button></li>
                          """ % {'disabled': ['', 'disabled="true"'][page == self.page or not active],
                                 'id': widgetId,
                                 'page':page,
                                 'caption':child.getTitle(path + [page])}
                          for page, child in self.getChildren()
                          #### fixme ####
                          # name = "Child must be widget"
                          # description = """If child is not a widget
                          # but a string, this fails..."""
                          #### end ####
                          if child.getVisible(child.path())])
        return """
               <div id="%(id)s" class="%(classes)s">
                <ul class="tabs">
                 %(tabs)s
                </ul>
                <div class="page">
                 %(page)s
                </div>
               </div>
               """ % {'id': widgetId,
                      'classes': self.classesStr,
                      'page': self.drawChild(self.page, self.getChild(self.page), path, True),
                      'tabs': tabs}
