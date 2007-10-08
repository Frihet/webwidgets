import Input

class TextFileEditor(Input.FieldStorageInput, Input.StringInput):
    __attributes__  = Input.StringInput.__attributes__ + ('mime_type',)
    
    cols = 40
    rows = 15

    mime_type = 'text/plain'
