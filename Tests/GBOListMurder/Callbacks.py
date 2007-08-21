import Webwidgets

import datetime

class MyWindow(object):
    class body(object):

        class GreencycleList(object):
            def function(self, path, function, row):
                if function == 'delete':
                    del self.rows[row]

            def getPages(self):
                return 1
            
            def getRows(self):
                return self.rows

            def valueChanged(self, path, value):
                print "Change %s: %s" % (path, value)
                self.changed = True
                Webwidgets.MemoryGBOList.valueChanged(self, path, value)
            
        class Add(object):
            def clicked(self, path):
                print "XXXX"
                kg=Webwidgets.HtmlWidget(self.session, self.winId, html="kg")
                count=Webwidgets.HtmlWidget(self.session, self.winId, html="count")
                
                newRow = {"id": None,
                          "currency" : Webwidgets.StringInputWidget(self.session, self.winId, value=""),
                          "name": Webwidgets.StringInputWidget(self.session, self.winId, value=""),
                          "value": Webwidgets.StringInputWidget(self.session,
                                                                self.winId,
                                                                value="1"),
                          "last": "Mon 12 February, 2007",
                          "until": Webwidgets.ButtonInputWidget(self.session,
                                                                self.winId,
                                                                title="Next week")}


#                                                    "value": Webwidgets.ListInputWidget(self.session,
#                                                             self.winId,
#                                                             value="kg",
#                                                             kg=kg,
#                                                             count=count)}

                self.parent['GreencycleList'].rows.append(newRow)
