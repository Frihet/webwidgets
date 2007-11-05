import Base, Formatting, cgi

class CssFileEditor(Base.ValueInput):
    original_value = value = None

    class input(object):
        class Value(object):
            def __get__(self, instance, owner):
                if instance is None or instance.parent is None:
                    return None
                return instance.parent.value
            def __set__(self, instance, value):
                instance.parent.value = value
        value = Value()

    class preview(object):
        types = dict(Formatting.Media.types)
        types['default'] = dict(types['default'])
        types['default']['width'] = None
        types['default']['height'] = None

        class Content(object):
            def __get__(self, instance, owner):
                if instance is None or instance.parent is None:
                    return None
                return instance.parent.value
        content = Content()
