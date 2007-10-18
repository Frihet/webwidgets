class Composite(object):
    class Dialog(object):
        class SomeDialog(object):
            def selected(self, path, value):
                if path != self.path: return
                del self.parent[self.name]
            
        class ShowDialog(object):
            def clicked(self, path):
                self.window.add_dialog(self.parent.SomeDialog(self.session, self.win_id))
