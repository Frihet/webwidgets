import Formatting, StringIO

class CssFileEditor(object):
    class Value(object):
        pass

    value = None
    
    class input(object):
        class Value(object):
            def __get__(self, instance, owner):
                if not hasattr(instance, 'parent'):
                    return None
                cssEditor = instance.parent
                if cssEditor.value is None:
                    return None
                cssEditor.value.file.seek(0)
                return cssEditor.value.file.read()
            def __set__(self, instance, value):
                fileValue = instance.parent.Value()
                fileValue.type ='text/css'
                fileValue.filename = 'CSS-file'
                fileValue.file = StringIO.StringIO()
                fileValue.file.seek(0)
                fileValue.file.write(value)
                fileValue.file.truncate()
                instance.parent.value = fileValue
        value = Value()

    class preview(object):
        types = dict(Formatting.Media.types)
        types[None] = dict(types[None])
        types[None]['width'] = None
        types[None]['height'] = None

        class Content(object):
            def __get__(self, instance, owner):
                if not hasattr(instance, 'parent'):
                    return None
                return instance.parent.value
        content = Content()
