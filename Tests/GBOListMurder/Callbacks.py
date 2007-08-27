import Webwidgets
import datetime

Webwidgets.Program.Session.debugFields = False
Webwidgets.Program.Session.debugSendNotification = False

class MyWindow(object):
    class body(object):

        class GreencycleList(object):
            nextId = 0

            def getPages(self):
                return 1
            
            def getRows(self):
                return self.rows

            def valueChanged(self, path, value):
                #print "Change %s: %s" % (path, repr(value))
                self.changed = True
                Webwidgets.GBOList.valueChanged(self, path, value)
            
        class Add(object):
            def clicked(self, path):
                kg=Webwidgets.Html(self.session, self.winId, html="kg")
                count=Webwidgets.Html(self.session, self.winId, html="count")

                self.parent['GreencycleList'].nextId += 1
                newRow = {"idd": self.parent['GreencycleList'].nextId,
                          "currency" : Webwidgets.StringInput(self.session, self.winId, value=""),
                          "name": Webwidgets.StringInput(self.session, self.winId, value="")}
                self.parent['GreencycleList'].rows.append(newRow)
