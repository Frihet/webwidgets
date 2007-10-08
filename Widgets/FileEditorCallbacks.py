import Webwidgets, cgi, traceback

def mime_type_to_method(mimeType):
    return mimeType.replace("/", "__").replace("-", "_")

def methodToMimeType(mimeType):
    return mimeType.replace("__", "/").replace("_", "-")

class Value(object):
    def __get__(self, instance, owner):
        if instance.parent is None:
            return None
        return instance.parent.parent.value
    def __set__(self, instance, value):
        instance.parent.parent.value = value
        
class FileEditor(object):
    __attributes__ = Webwidgets.Html.__attributes__ + ('expanded', 'value', 'error')

    def __init__(self, session, win_id, **attr):
        Webwidgets.Html.__init__(self, session, win_id, **attr)
        self.value_changed(self.path, self.value)
        self.expanded_changed(self.path, self.expanded)

    value = None
    error = None
    expanded = False

    def mime_type_to_method(self, mimeType):
        return mime_type_to_method(mimeType)
    
    def methodToMimeType(self, mimeType):
        return methodToMimeType(mimeType)

    class downloadLink(object):
        class Content(object):
            def __get__(self, instance, owner):
                if instance.parent is None:
                    return None
                return instance.parent.value
        content = Content()

    class hide(object):
        class Value(object):
            def __get__(self, instance, owner):
                if instance.parent is None:
                    return None
                return instance.parent.expanded
            def __set__(self, instance, value):
                instance.parent.expanded = value
        value = Value()

    def expanded_changed(self, path, value):
        self['infoGroup'].visible = self['editors'].visible = self['upload'].visible = value

    class infoGroup(object):
        class name(object):
            class field(object):
                class Value(object):
                    def __get__(self, instance, owner):
                        if instance.parent is None:
                            return None
                        return getattr(instance.parent.parent.parent.value, 'filename', '&lt;No file&gt;')
                    def __set__(self, instance, value):
                        if instance.parent.parent.parent.value is not None:
                            instance.parent.parent.parent.value.filename = value
                value = Value()

    class editors(object):
        class text__css(object):
            value = Value()
        class text__plain(object):
            value = Value()
        class text__html(object):
            value = Value()
        class default(object):
            content = Value()
        def page_changed(self, path, page):
            Webwidgets.TabbedView.page_changed(self, path, page)
            if page not in (None, ['default']):
                if page == ['none']:
                    self.parent.value = None
                else:
                    mimeType = methodToMimeType(page[0])
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
                    editor = mime_type_to_method(value.type)
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

    def value_changed(self, path, value):
        if path != self.path: return
        editor = mime_type_to_method(getattr(value, 'type', 'none'))
        if editor not in self['editors'].children:
            editor = 'default'
        self['editors'].page = [editor]
        
