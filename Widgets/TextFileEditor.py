import Input

class TextFileEditor(Input.FieldStorageInput, Input.StringInput):
    cols = 40
    rows = 15
    mime_type = 'text/plain'
