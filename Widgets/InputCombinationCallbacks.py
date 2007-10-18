import Base

class ApplicationWindow(object):
    class Body(object):
        class LogIn(object):
            class Application(object):
                class Title(object):
                    def __get__(self, instance, owner):
                        if (   instance is None
                            or instance.parent is None
                            or instance.parent.parent is None
                            or instance.parent.parent.parent is None):
                            return None
                        return instance.parent.parent.parent.title
                title = Title()

    def add_dialog(self, dialog, name = None):
        if name is None: name = str(len(self['Body']['Dialogs'].children))
        self['Body']['Dialogs'][name] = dialog
