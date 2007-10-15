import Webwidgets

class Dynamic(object):
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
