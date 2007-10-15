
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

import Webwidgets, cgi, os.path

class MyWindow(object):
    def __init__(self, session, win_id, *arg, **kw):
        Webwidgets.HtmlWindow.__init__(self, session, win_id, *arg, **kw)
        print "XXYZZY"

#    class location(object):
#        def value_changed(self, path, value):
#            Webwidgets.ArgumentInput.value_changed(self, path, value)
#            print "Location changed", path, value
#    class extra(object):
#        def value_changed(self, path, value):
#            Webwidgets.ArgumentInput.value_changed(self, path, value)
#            print "Extra arguments changed", path, value
            
    class body(object):
        class tabs(object):
            class home(object):
                class logo(object):
                    content = cgi.FieldStorage()
                    content.filename = "Logo.png"
                    content.type = "image/png"
                    content.file = open(os.path.join(os.path.split(__file__)[0],
                                                     "../../../Docs/Logo.png"))
                    content.file.seek(0)

            class input(object):
                class data(object):
                    class updatepwd(object):
                        class field(object):
                            class pwdclear(object):
                                def clicked(self, path):
                                    self.parent.parent.parent['newpwd']['field'].value = ''

                            class pwdset(object):
                                def clicked(self, path):
                                    newpwd = self.parent.parent.parent['newpwd']['field']
                                    lastpwd = self.parent.parent.parent['lastpwd']['field']
                                    if newpwd.value is not None:
                                        lastpwd.html = newpwd.value

            class composite(object):
                class dialog(object):
                    class ShowDialog(object):
                        def clicked(self, path):
                            print "SHOW DIALOG CLICKED"
                            self.parent.parent.parent.parent['SomeDialog'].visible = True

                class logIn(object):
                    def authenticate(self, username, password):
                        if username != password:
                            raise Exception("For this demo, the correct password is the same as the username!")
                        return True

            class config(object):
                class language(object):
                    class sel(object):
                        def draw(self, output_options):
                            self.register_submit_action(self.path, "change")
                            return Webwidgets.LanguageSelector.draw(self, output_options)
                            
                    class language(object):
                        def draw(self, output_options):
                            return ', '.join(self.get_languages(output_options))

            class dynamic(object):
                class filelist(object):
                    class Listing(object):
                        ww_explicit_load = True
                        class Entry(object):
                            ww_explicit_load = True
                            def __init__(self, session, win_id, type, name, dates):
                                Webwidgets.Html.__init__(
                                    self,
                                    session, win_id,
                                    children = Webwidgets.Utils.OrderedDict(
                                    [('type', Webwidgets.Text(session, win_id, html = type)),
                                     ('name', Webwidgets.Text(session, win_id, html = name)),
                                     ('dates', Webwidgets.ListInput(
                                         session, win_id,
                                         children = Webwidgets.Utils.OrderedDict(
                                             [(str(nr), Webwidgets.Text(session, win_id, html = date))
                                              for nr, date in enumerate(dates)])))]))

                            class actions(object):
                                 class check(object):
                                     def value_changed(self, path, value):
                                         Webwidgets.Checkbox.value_changed(self, path, value)
                                         print "FOO", value


                        def __init__(self, session, win_id, files):
                            Webwidgets.List.__init__(
                                self, session, win_id,
                                pre='', sep='\n', post='',
                                children=Webwidgets.Utils.OrderedDict(
                                    [(str(nr), self.Entry(session, win_id, *file))
                                     for nr, file in enumerate(files)]))

                    class UpdateFiles(object):
                        def clicked(self, path):
                            print path
                            import time
                            self.parent['Listing'][time.strftime('%s')] = self.parent.Listing.Entry(self.session, self.win_id, 'bar', 'foo', ('2007', '2008'))

                    def __init__(self, session, win_id):
                        Webwidgets.Html.__init__(
                            self, session, win_id,
                            children = {'Listing': self.Listing(
                                session, win_id,
                                [('doc', 'foo', ('2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10')),
                                 ('gif', 'bar', ('2006-06-20 10:11:12 +10',)),
                                 ('jpg', 'muahehe', ('2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10')),
                                 ('doc', 'gnaga', ('2006-06-20 10:11:12 +10',)),
                                 ('xslt', 'apsfnana', ('2006-06-20 10:11:12 +10','2006-04-10 10:11:12 +10')),
                                 ])})
