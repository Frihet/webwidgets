#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework example file
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

"""An example Webwidgets application that does not use Wwml, only pure
Python code."""

import Webwidgets
       
class pytest(Webwidgets.Program):
    """The most important part of a Webwidgets application is a
    Webware page. That is a file in a Webware context containing a
    classwith the same name as the file, that inherits from
    L{Webwidgets.Program} (which in turn inherits from
    L{WebKit.Page.Page}."""

    class Session(Webwidgets.Program.Session):
        """The Session member of a Webwidgets program is instantiated
        once for each user session, and should be a subclass of
        L{Webwidgets.Program.Session}.

        It should define a method called L{new_window}.
        """
        
        class MyWindow(Webwidgets.HtmlWindow):
            """The window holds all the actual user interface parts."""
            
            headers={'Content-Type': 'text/html; charset=UTF-8',
                     'Status': '202 Page loaded'}
            """The headers to send to the client unless a callback has
            overridden them. This is here more for example than
            anything else - the default values should be OK."""

            title = 'RedBack WebWidgets demo application'
            """The title of the application, shown in the title bar of
            the webbrowser."""

            class head(Webwidgets.StyleLink):
                """Any content that should go """
                style = '../../Widgets.css'

            class body(Webwidgets.Html):
                html = """<div id="%(id)s-header">
                           Upload: %(upload)s
                           <span id="%(id)s-header-search">Search: %(Search)s</span>
                           <span id="%(id)s-header-dir">%(CurrentDirectory)s</span>
                           <span id="%(id)s-header-right">
                            <span id="%(id)s-header-date">Date: %(SelectDate)s</span>
                            %(Filter)s
                           </span>
                          </div>
                          <div id="%(id)s-body">
                          %(ShowDialog)s<br />
                          %(SomeDialog)s<br />

                          %(table)s<br />

                          Last password: %(lastpwd)s<br />
                          %(newpwd)s<br />
                          %(pwdclear)s %(pwdset)s<br />

                          %(Dirlisting)s
                          </div>
                          <div id="%(id)s-footer">
                          xxx
                          </div>
                          """
                          
                class upload(Webwidgets.FileInput): pass

                class table(Webwidgets.Table):
                    hiddenCols = set((1,))
                    class cell_0_0_1_1(Webwidgets.Html): html='Foo'
                    class cell_1_0_1_1(Webwidgets.Html): html='Bar'
                    class cell_0_1_2_1(Webwidgets.Html): html='Fie'
                    class cell_0_2_1_1(Webwidgets.Html): html='Ma'
                    class cell_1_2_1_1(Webwidgets.Html): html='Ba'
                    class cell_2_0_1_3(Webwidgets.Html): html='Foo'

                class lastpwd(Webwidgets.Html):
                    html = ''

                class newpwd(Webwidgets.NewPasswordInput):
                    value = 'foo'

                class pwdclear(Webwidgets.Button):
                    title = 'Clear new password'
                    def clicked(self, path):
                        self.parent.children['newpwd'].notify('value_changed', '')

                class pwdset(Webwidgets.Button):
                    title = 'Set new password'
                    def clicked(self, path):
                        self.parent.children['lastpwd'].html = self.parent.children['newpwd'].value

                class CurrentDirectory(Webwidgets.Html): html = '/foo/bar/fie'
                class Search(Webwidgets.StringInput): value = '/foo/bar/fie'
                class SelectDate(Webwidgets.ListInput):
                    def __init__(self, session, win_id):
                        Webwidgets.ListInput.__init__(
                            self, session, win_id,
                            one='2006-06-20 10:11:12 +10',
                            two='2006-06-15 10:11:12 +10',
                            three='2006-06-15 10:11:12 +10',
                            four='2006-06-01 10:11:12 +10',
                            five='2006-05-01 23:45:00 +10',
                            six='2006-04-13 12:00:00 +10',
                            )
                    def value_changed(self, path, value):
                        Webwidgets.ListInput.value_changed(self, path, value)
                        print "List input changed", value

                class Filter(Webwidgets.Button): title = 'Filter'
                class ShowDialog(Webwidgets.Button):
                    title = 'Show dialog'
                    def clicked(self, path):
                        self.parent.children['SomeDialog'].visible = True

                class SomeDialog(Webwidgets.Dialog):
                    visible = False
                    head = 'My dialog'
                    body = 'Click ok or cancel, please'

                class Dirlisting(Webwidgets.Html):
                    html = """<table id="%(id)s">
                     <tr><th>Type</th><th>Filename</th><th>Dates</th><th>Actions</th></tr>
                     %(Listing)s
                    </table>"""

                    class Listing(Webwidgets.List):
                        __explicit_load__ = True
                        class Entry(Webwidgets.Html):
                            __explicit_load__ = True
                            html = """
                            <tr>
                             <td>
                              %(type)s
                             </td>
                             <td>
                              %(name)s
                             </td>
                             <td>
                              %(dates)s
                             </td>
                             <td>
                              %(actions)s
                             </td>
                            </tr>"""
                            class actions(Webwidgets.Html):
                                html = "%(check)s%(label)s"
                                class label(Webwidgets.Label):
                                    class label(Webwidgets.Html): html = 'Restore'
                                    target = '1/check'
                                class check(Webwidgets.Checkbox):
                                    value = 1
                                    def value_changed(self, path, value):
                                        Webwidgets.Checkbox.value_changed(self, path, value)
                                        if value:
                                            self.error = "XXXXXX"
                                
                            def __init__(self, session, win_id, type, name, dates):
                                Webwidgets.Html.__init__(
                                    self,
                                    session, win_id, type=type, name=name,
                                    dates = Webwidgets.ListInput(session, win_id, **dict([(str(nr), date)
                                                                                               for nr, date in enumerate(dates)])))
                        def __init__(self, session, win_id, files):
                            Webwidgets.List.__init__(
                                self, session, win_id,
                                pre='', sep='\n', post='',
                                **dict([(str(nr), self.Entry(session, win_id, *file))
                                        for nr, file in enumerate(files)]))

                    def __init__(self, session, win_id):
                        Webwidgets.Html.__init__(self, session, win_id, Listing = self.Listing(
                            session, win_id, [('doc', 'foo', ('2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10')),
                                             ('gif', 'bar', ('2006-06-20 10:11:12 +10',)),
                                             ('jpg', 'muahehe', ('2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10')),
                                             ('doc', 'gnaga', ('2006-06-20 10:11:12 +10',)),
                                             ('xslt', 'apsfnana', ('2006-06-20 10:11:12 +10','2006-04-10 10:11:12 +10')),
                                             ]))

        def new_window(self, win_id):
            """This method is called to create new windows for the
            user; that is every time a user enters a new URL that
            contains a new windowId. Using different windowId:s it is
            possible to handle popup-windows and frames.

            @return: an instance of L{Webwidgets.Widgets.Window}."""

            return self.MyWindow(self, win_id)
