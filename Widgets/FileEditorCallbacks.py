import traceback

class Value(object):
    def __get__(self, instance, owner):
        if not hasattr(instance, 'parent'):
            return None
        return instance.parent.parent.value
    def __set__(self, instance, value):
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

            def fieldInput(self, path, fieldValue):
                if path == self.path:
                    if fieldValue != '':
                        if fieldValue is not None:
                            mimeType = fieldValue.type.replace("/", "__").replace("-", "_")
                            if mimeType not in self.parent.parent['editors'].children:
                                self.error = 'Unrecognized file-type: %s' % fieldValue.type
                                return
                            elif not self.parent.parent['editors'][mimeType].visible:
                                self.error = 'Unallowed file-type: %s' % fieldValue.type
                                return
                        self.value = fieldValue
                elif path == self.path + ['_', 'clear']:
                    if fieldValue != '':
                        self.value = None
