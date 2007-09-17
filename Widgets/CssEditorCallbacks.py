import Formatting, StringIO

class CssEditor(object):
    value = ''
    
    class child(object):
        class input(object):
            class Value(object):
                def __get__(self, instance, owner):
                    if not hasattr(instance, 'parent'):
                        return None
                    return instance.parent.parent.value
                def __set__(self, instance, value):
                    instance.parent.parent.value = value
            value = Value()

        class preview(object):
            types = dict(Formatting.Media.types)
            types[None] = dict(types[None])
            types[None]['width'] = None
            types[None]['height'] = None

            class Content(object):
                def __init__(self):
                    class Value(object):
                        pass
                    self.value = Value()
                    self.value.type ='text/css'
                    self.value.filename = 'Preview'
                    self.value.file =  StringIO.StringIO()
                def __get__(self, instance, owner):
                    if not hasattr(instance, 'parent'):
                        return None
                    self.value.file.seek(0)
                    self.value.file.write(instance.parent.parent.value)
                    self.value.file.truncate()
                    self.value.file.seek(0)
                    return self.value
            content = Content()
