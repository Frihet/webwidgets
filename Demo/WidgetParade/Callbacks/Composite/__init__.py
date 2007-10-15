class Composite(object):
    class dialog(object):
        class ShowDialog(object):
            def clicked(self, path):
                print "SHOW DIALOG CLICKED"
                self.parent.parent.parent.parent['SomeDialog'].visible = True

    class logIn(object):
        def authenticate(self, username, password):
            if username != password:
                raise Exception("For this demo, the correct password is the same as the username!")
            return True
