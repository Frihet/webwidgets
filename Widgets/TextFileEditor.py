import Input, cgi

class TextFileEditor(Input.StringInput):
    __attributes__  = Input.StringInput.__attributes__ + ('mimeType',)
    
    cols = 40
    rows = 15

    value = None
    mimeType = 'text/plain'

    def fieldInput(self, path, stringValue):
        if self.value is None:
            self.value = cgi.FieldStorage()
            self.value.filename = '%s file' % (self.mimeType,)
        if hasattr(self.value, 'original'):
            del self.value.original
        self.value.type = self.mimeType
        if self.value.file is None:
            self.value.file = self.value.make_file()
        self.value.file.seek(0)
        self.value.file.write(stringValue)
        self.value.file.truncate()
        self.value.file.seek(0)

    def fieldOutput(self, path):
        res = ''
        if self.value is not None:
            self.value.file.seek(0)
            res = self.value.file.read()
        return [res]
