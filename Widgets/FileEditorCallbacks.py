import Webwidgets, cgi, traceback

def mimeTypeToMethod(mimeType):
    return mimeType.replace("/", "__").replace("-", "_")

def methodToMimeType(mimeType):
    return mimeType.replace("__", "/").replace("_", "-")

class Value(object):
    def __get__(self, instance, owner):
        if not hasattr(instance, 'parent'):
            return None
        return instance.parent.parent.value
    def __set__(self, instance, value):
        instance.parent.parent.value = value
        
class FileEditor(object):
    __attributes__ = Webwidgets.Html.__attributes__ + ('value', 'error')

    value = None
    error = None

    def mimeTypeToMethod(self, mimeType):
        return mimeTypeToMethod(mimeType)
    
    def methodToMimeType(self, mimeType):
        return methodToMimeType(mimeType)

    class name(object):
        class field(object):
            class Value(object):
                def __get__(self, instance, owner):
                    if not hasattr(instance, 'parent'):
                        return None
                    return getattr(instance.parent.parent.value, 'filename', '&lt;No file&gt;')
                def __set__(self, instance, value):
                    if instance.parent.parent.value is not None:
                        instance.parent.parent.value.filename = value
            value = Value()

    class hide(object):
        def valueChanged(self, path, value):
            self.parent['editors'].visible = self.parent['upload'].visible = value

    class editors(object):
        class text__css(object):
            value = Value()
        class text__plain(object):
            value = Value()
        class text__html(object):
            value = Value()
        class default(object):
            content = Value()
        def pageChanged(self, path, page):
            Webwidgets.TabbedView.pageChanged(self, path, page)
            if page not in (None, 'default'):
                if page == 'none':
                    self.parent.value = None
                else:
                    mimeType = methodToMimeType(page)
                    value = self.parent.value
                    if value is None or mimeType != value.type:
                        if value is None:
                            value = cgi.FieldStorage()
                        value.type = mimeType
                        if value.file is None:
                            value.file = value.make_file()
                        value.file.seek(0)
                        value.file.truncate()
                        value.filename = "new %s file" % mimeType
                        self.parent.value = value
            
    class upload(object):
        class action(object):
            def clicked(self, path):
                value = self.parent['file'].value
                editors = self.parent.parent['editors']
                if value is not None:
                    editor = mimeTypeToMethod(value.type)
                    if editor not in editors.children:
                        if editors.children['default'].visible:
                            editor = 'default'
                        else:
                            self.parent['file'].error = 'Unrecognized file-type: %s' % value.type
                            return
                    elif not editors[editor].visible:
                        self.parent['file'].error = 'Unallowed file-type: %s' % value.type
                        return
                self.parent.parent.value = value

    def valueChanged(self, path, value):
        if path != self.path: return
        editor = mimeTypeToMethod(getattr(value, 'type', 'none'))
        if editor not in self['editors'].children:
            editor = 'default'
        self['editors'].page = editor
        
