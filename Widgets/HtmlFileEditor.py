import Input, HtmlInput

class HtmlFileEditor(Input.FieldStorageInput, HtmlInput.HtmlInput):
    mimeType = 'text/html'
