import cgi, os.path

class Home(object):
    class logo(object):
        content = cgi.FieldStorage()
        content.filename = "Logo.png"
        content.type = "image/png"
        content.file = open(os.path.join(os.path.split(__file__)[0],
                                         "../../../Docs/Logo.png"))
        content.file.seek(0)

