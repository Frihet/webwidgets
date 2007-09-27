import Input

class TextFileEditor(Input.FileInput, Input.StringInput):
    __attributes__  = Input.StringInput.__attributes__ + ('mimeType',)
    
    cols = 40
    rows = 15

    mimeType = 'text/plain'
