import Webwidgets

class Value(object):
    empty = ''
    def __get__(self, instance, owner):
        if not instance or instance.file_editor is None:
            return None
        if instance.file_editor.value is None:
            return self.empty
        if not hasattr(instance.file_editor.value, self.attribute):
            setattr(instance.file_editor.value, self.attribute, '')
        return getattr(instance.file_editor.value, self.attribute)
    def __set__(self, instance, value):
        if instance.file_editor.value is not None :
            setattr(instance.file_editor.value, self.attribute, value)

class FileEditorList(object):
    class NameInput(Webwidgets.StringInput):
        ww_explicit_load = True
        file_editor = None
        
        class NameValue(Value):
            attribute = 'filename'
            empty = '&lt;No file&gt'
        value = NameValue()

    class DescriptionInput(Webwidgets.StringInput):
        ww_explicit_load = True
        file_editor = None
        cols = 40
        rows_expanded = 10
        rows_collapsed = 1

        class Rows(object):
            def __get__(self, instance, owner):
                if not instance or instance.file_editor is None:
                    return None
                return [instance.rows_collapsed, instance.rows_expanded][instance.file_editor.expanded]
        rows = Rows()
        
        class DescriptionValue(Value):
            attribute = 'description'
        value = DescriptionValue()

    def add_row(self, file = None):
        file_editor = self.FileEditor(self.session, self.win_id, value = file)
        self.rows.append({
            'name': self.NameInput(self.session, self.win_id, file_editor = file_editor),
            'description': self.DescriptionInput(self.session, self.win_id, file_editor = file_editor),
            'file': file_editor
            })

    def group_function(self, path, function):
        if path != self.path: return
        if function == 'add':
            self.add_row()
            self.rows[-1]['file'].expanded = True

    def function(self, path, function, row):
        if path != self.path: return
        if function == 'delete':
            del self.rows[row]
        if function == 'edit':
            self.rows[row]['file'].expanded = not self.rows[row]['file'].expanded

    class FileListValue(object):
        def __get__(self, instance, owner):
            if not instance or instance.rows is None:
                return None
            return [row['file'].value
                    for row in instance.rows
                    if row['file'].value is not None]
        def __set__(self, instance, value):
            if instance.rows is not None:
                del instance.rows[:]
                for file in value:
                    if file is not None:
                        instance.add_row(file)
    value = FileListValue()

    def reset(self):
        del self.rows[:]
