class Composite(object):
    class dialog(object):
        class SomeDialog(object):
            def selected(self, path, value):
                if path != self.path: return
                del self.parent[self.name]
            
        class ShowDialog(object):
            def clicked(self, path):
                dialogs = self.window['body']['dialogs']
                dialogs[str(len(dialogs.children))] = self.parent.SomeDialog(self.session, self.win_id)
