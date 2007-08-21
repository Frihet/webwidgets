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

import Webwidgets

class MyWindow(object):
#    class location(object):
#        def valueChanged(self, path, value):
#            Webwidgets.ArgumentInputWidget.valueChanged(self, path, value)
#            print "Location changed", path, value
#    class extra(object):
#        def valueChanged(self, path, value):
#            Webwidgets.ArgumentInputWidget.valueChanged(self, path, value)
#            print "Extra arguments changed", path, value
            
    class body(object):
        class pwdclear(object):
            def clicked(self, path):
                self.parent['newpwd'].notify('valueChanged', path, '')

        class pwdset(object):
            def clicked(self, path):
                self.parent['lastpwd'].html = self.parent['newpwd'].value

        class SelectDate(object):
            def __init__(self, session, winId):
                Webwidgets.ListInputWidget.__init__(
                    self, session, winId,
                    one='2006-06-20 10:11:12 +10',
                    two='2006-06-15 10:11:12 +10',
                    three='2006-06-15 10:11:12 +10',
                    four='2006-06-01 10:11:12 +10',
                    five='2006-05-01 23:45:00 +10',
                    six='2006-04-13 12:00:00 +10',
                    )
            def valueChanged(self, path, value):
                Webwidgets.ListInputWidget.valueChanged(self, path, value)
                print "XXX", value

        class ShowDialog(object):
            def clicked(self, path):
                self.parent['SomeDialog'].visible = True

        class Dirlisting(object):
            class Listing(object):
                __explicit_load__ = True
                class Entry(object):
                    __explicit_load__ = True
                    def __init__(self, session, winId, type, name, dates):
                        Webwidgets.HtmlWidget.__init__(
                            self,
                            session, winId, type=type, name=name,
                            dates = Webwidgets.ListInputWidget(session, winId, **dict([(str(nr), date)
                                                                                       for nr, date in enumerate(dates)])))

                    class actions(object):
                         class check(object):
                             def valueChanged(self, path, value):
                                 Webwidgets.CheckboxInputWidget.valueChanged(self, path, value)
                                 print "FOO", value


                def __init__(self, session, winId, files):
                    Webwidgets.ListWidget.__init__(
                        self, session, winId,
                        pre='', sep='\n', post='',
                        **dict([(str(nr), self.Entry(session, winId, *file))
                                for nr, file in enumerate(files)]))

            class UpdateFiles(object):
                def clicked(self, path):
                    print path
                    import time
                    self.parent['Listing'][time.strftime('%s')] = self.parent.Listing.Entry(self.session, self.winId, 'bar', 'foo', ('2007', '2008'))

            def __init__(self, session, winId):
                Webwidgets.HtmlWidget.__init__(self, session, winId, Listing = self.Listing(
                    session, winId, [('doc', 'foo', ('2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10')),
                                     ('gif', 'bar', ('2006-06-20 10:11:12 +10',)),
                                     ('jpg', 'muahehe', ('2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10','2006-06-20 10:11:12 +10')),
                                     ('doc', 'gnaga', ('2006-06-20 10:11:12 +10',)),
                                     ('xslt', 'apsfnana', ('2006-06-20 10:11:12 +10','2006-04-10 10:11:12 +10')),
                                     ]))
