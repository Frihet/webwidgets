class Value(object):
    def __get__(self, instance, owner):
        if not hasattr(instance, 'parent'):
            return None
        return instance.parent.parent.value
    def __set__(self, instance, value):
        if value is None:
            instance.parent.parent.value = value
        else:
            mimeType = value.type.replace("/", "__").replace("-", "_")
            if mimeType not in instance.parent.parent['editors'].children:
                instance.error = 'Unrecognized file-type: %s' % value.type
            elif not instance.parent.parent['editors'][mimeType].visible:
                instance.error = 'Unallowed file-type: %s' % value.type
            else:
                instance.parent.parent.value = value

class FileEditor(object):
    value = None
    error = None

    class editors(object):
        class text__css(object):
            value = Value()
            
    class upload(object):
        class file(object):
            value = Value()
            
