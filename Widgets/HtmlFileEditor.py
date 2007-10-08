import Input
import HtmlInput as HtmlInputModule

class HtmlFileEditor(Input.FieldStorageInput, HtmlInputModule.HtmlInput):
    mime_type = 'text/html'
