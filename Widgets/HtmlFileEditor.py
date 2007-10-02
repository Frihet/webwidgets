import Input
import HtmlInput as HtmlInputModule

class HtmlFileEditor(Input.FieldStorageInput, HtmlInputModule.HtmlInput):
    mimeType = 'text/html'
