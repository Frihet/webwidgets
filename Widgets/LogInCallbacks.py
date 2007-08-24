import Webwidgets

class LogIn(object):
    class logIn(object):
        debug = True

        def selected(self, path, value):
            fields = self.getWidgetsByAttribute('fieldName')

            if self.debug: print "Log in attempt:", fields['username'].value, fields['password'].value

            try:
                self.parent.userInfo = self.parent.authenticate(
                    fields['username'].value,
                    fields['password'].value)
            except Exception, e:
                fields['username'].error = unicode(e)
                
            else:
                if self.debug: print "User logged in:", self.parent.userInfo
                
                Webwidgets.DialogWidget.selected(self, path, value)                
                self.parent['application'] = self.parent.Application(self.session, self.winId)
                
    def authenticate(self, username, password):
        raise Exception("You must override the authenticate() method of this widget!")

    def userInfoChanged(self, path, value):
        self.session.userInfo = self.userInfo
            
