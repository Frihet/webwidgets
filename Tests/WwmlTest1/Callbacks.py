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

import Webwidgets

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

        class language(object):
            def draw(self, output_options):
                return ', '.join(self.get_languages(output_options))
            
        class pwdclear(object):
            def clicked(self, path):
                self.parent['newpwd']['field'].value = ''

        class pwdset(object):
            def clicked(self, path):
                if self.parent['newpwd']['field'].value is not None:
                    self.parent['lastpwd'].html = self.parent['newpwd']['field'].value

        class SelectDate(object):
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
                print "XXX", value

        class ShowDialog(object):
            def clicked(self, path):
                print "SHOW DIALOG CLICKED"
                self.parent['SomeDialog'].visible = True

        class Dirlisting(object):
            class Listing(object):
                __explicit_load__ = True
                class Entry(object):
                    __explicit_load__ = True
                    def __init__(self, session, win_id, type, name, dates):
                        Webwidgets.Html.__init__(
                            self,
                            session, win_id,
                            type = Webwidgets.Text(session, win_id, html = type),
                            name = Webwidgets.Text(session, win_id, html = name),
                            dates = Webwidgets.ListInput(session, win_id, **dict([(str(nr), Webwidgets.Text(session, win_id, html = date))
                                                                                  for nr, date in enumerate(dates)])))

                    class actions(object):
                         class check(object):
                             def value_changed(self, path, value):
                                 Webwidgets.Checkbox.value_changed(self, path, value)
                                 print "FOO", value


                def __init__(self, session, win_id, files):
                    Webwidgets.List.__init__(
                        self, session, win_id,
                        pre='', sep='\n', post='',
                        **dict([(str(nr), self.Entry(session, win_id, *file))
                                for nr, file in enumerate(files)]))

            class UpdateFiles(object):
                def clicked(self, path):
                    print path
                    import time
                    self.parent['Listing'][time.strftime('%s')] = self.parent.Listing.Entry(self.session, self.win_id, 'bar', 'foo', ('2007', '2008'))

            def __init__(self, session, win_id):
                Webwidgets.Html.__init__(self, session, win_id, Listing = self.Listing(
                    session, win_id, [('doc', 'foo', ('2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10')),
                                      ('gif', 'bar', ('2006-06-20 10:11:12 +10',)),
                                      ('jpg', 'muahehe', ('2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10')),
                                      ('doc', 'gnaga', ('2006-06-20 10:11:12 +10',)),
                                      ('xslt', 'apsfnana', ('2006-06-20 10:11:12 +10','2006-04-10 10:11:12 +10')),
                                      ]))
