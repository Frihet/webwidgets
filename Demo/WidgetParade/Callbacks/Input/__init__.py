class Input(object):
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

