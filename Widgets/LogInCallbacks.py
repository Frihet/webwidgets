import Webwidgets

class LogIn(object):
    __attributes__ = Webwidgets.HtmlWidget.__attributes__ + ('globalSession', 'userInfo')
    globalSession = True
    userInfo = None
    
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
                
    def authenticate(self, username, password):
        raise Exception("You must override the authenticate() method of this widget!")

    def userInfoChanged(self, path, value):
        if self.globalSession:
            self.session.logIn = self
        if self.userInfo is None:
            self['application'] = Webwidgets.HtmlWidget(self.session, self.winId)
            self['logIn'].visible = True
        else:
            self['application'] = self.Application(self.session, self.winId)
            self['logIn'].visible = False

class LogOut(object):
    debug = True
    __attributes__ = Webwidgets.DialogWidget.__attributes__ + ('logIn',)
    logIn = None
    
    def selected(self, path, value):
        if self.logIn is None:
            logIn = self.session.logIn
        elif isinstance(self.logIn, Webwidgets.Widget):
            logIn = self.logIn
        else:
            logIn = self + self.logIn
        logIn.userInfo = None
            
