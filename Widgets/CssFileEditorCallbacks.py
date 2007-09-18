import Formatting, cgi

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
                cssEditor = instance.parent
                if cssEditor.value is None:
                    cssEditor.value = cgi.FieldStorage()
                cssEditor.value.type ='text/css'
                cssEditor.value.filename = 'CSS-file'
                if cssEditor.value.file is None:
                    cssEditor.value.file = cssEditor.value.make_file()
                cssEditor.value.file.seek(0)
                cssEditor.value.file.write(value)
                cssEditor.value.file.truncate()
                cssEditor.value.file.seek(0)
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
