import Webwidgets

class Value(object):
    empty = ''
    def __get__(self, instance, owner):
        if not instance or instance.fileEditor is None:
            return None
        return getattr(instance.fileEditor.value, self.attribute, self.empty)
    def __set__(self, instance, value):
        if instance.fileEditor.value is not None :
            setattr(instance.fileEditor.value, 'filename', value)

class FileEditorList(object):
    class NameInput(Webwidgets.StringInput):
        __attributes__ = Webwidgets.StringInput.__attributes__ + ('fileEditor',)
        __explicit_load__ = True
        fileEditor = None
        
        class NameValue(Value):
            attribute = 'filename'
            empty = '&lt;No file&gt'
        value = NameValue()

    class DescriptionInput(Webwidgets.StringInput):
        __attributes__ = Webwidgets.StringInput.__attributes__ + ('fileEditor',)
        __explicit_load__ = True
        fileEditor = None
        cols = 40
        rows = 2
        
        class DescriptionValue(Value):
            attribute = 'description'
        value = DescriptionValue()

    def addRow(self, file = None):
        fileEditor = self.FileEditor(self.session, self.winId, value = file)
        self.rows.append({
            'name': self.NameInput(self.session, self.winId, fileEditor = fileEditor),
            'description': self.DescriptionInput(self.session, self.winId, fileEditor = fileEditor),
            'file': fileEditor
            })

    def groupFunction(self, path, function):
        if path != self.path: return
        if function == 'add':
            self.addRow()

    def function(self, path, function, row):
        if path != self.path: return
        if function == 'delete':
            del self.rows[row]

    class FileListValue(object):
        def __get__(self, instance, owner):
            if not instance or instance.rows is None:
                return None
            return [row['file'].value for row in instance.rows]
        def __set__(self, instance, value):
            if instance.rows is not None :
                for file in value:
                    instance.addRow(file)
    value = FileListValue()
