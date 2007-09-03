import Webwidgets, traceback

class LogIn(object):
    __attributes__ = Webwidgets.Html.__attributes__ + ('globalSession', 'userInfo')
    globalSession = True
    userInfo = None
    debugLogIn = False
    debugErrors = False
    
    class logIn(object):
        def selected(self, path, value):
            fields = self.getWidgetsByAttribute('fieldName')

            if self.parent.debugLogIn: print "Log in attempt:", fields['username'].value, fields['password'].value

            try:
                self.parent.userInfo = self.parent.authenticate(
                    fields['username'].value,
                    fields['password'].value)
            except Exception, e:
                if self.parent.debugErrors: traceback.print_exc()
                fields['username'].error = unicode(e)
                
            else:
                if self.parent.debugLogIn: print "User logged in:", self.parent.userInfo
                
    def authenticate(self, username, password):
        raise Exception("You must override the authenticate() method of this widget!")

    def userInfoChanged(self, path, value):
        if self.globalSession:
            self.session.logIn = self
        if self.userInfo is None:
            self['application'] = Webwidgets.Html(self.session, self.winId)
            self['logIn'].visible = True
        else:
            self['application'] = self.Application(self.session, self.winId)
            self['logIn'].visible = False

class LogOut(object):
    debug = True
    __attributes__ = Webwidgets.Dialog.__attributes__ + ('logIn',)
    logIn = None
    
    def selected(self, path, value):
        if self.logIn is None:
            logIn = self.session.logIn
        elif isinstance(self.logIn, Webwidgets.Widget):
            logIn = self.logIn
        else:
            logIn = self + self.logIn
        logIn.userInfo = None
            
