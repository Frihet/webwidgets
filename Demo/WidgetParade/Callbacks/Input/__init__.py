class Input(object):
    class Data(object):
        class UpdatePwd(object):
            class Field(object):
                class PwdClear(object):
                    def clicked(self, path):
                        self.parent.parent.parent['NewPwd']['Field'].value = ''

                class PwdSet(object):
                    def clicked(self, path):
                        newpwd = self.parent.parent.parent['NewPwd']['Field']
                        lastpwd = self.parent.parent.parent['LastPwd']['Field']
                        if newpwd.value is not None:
                            lastpwd.html = newpwd.value

