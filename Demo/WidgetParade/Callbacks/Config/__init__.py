import Webwidgets

class Config(object):
    class language(object):
        class sel(object):
            def draw(self, output_options):
                self.register_submit_action(self.path, "change")
                return Webwidgets.LanguageSelector.draw(self, output_options)

        class language(object):
            def draw(self, output_options):
                return ', '.join(self.get_languages(output_options))
