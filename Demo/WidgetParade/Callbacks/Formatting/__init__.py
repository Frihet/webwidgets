import Webwidgets

class Formatting(object):
    class Tables(object):
        class ListTest(object):
            def __init__(self, *arg, **kw):
                Webwidgets.Table.__init__(self, *arg, **kw)
                self.rows = [{"foo":"47", "bar":"11", "fie":"56", "x":"X", "y":"Y", "z":"Z"},
                             {"foo":"47", "bar":"11", "fie":"56", "x":"X", "y":"Y", "z":"Z"},
                             {"foo":"47", "bar":"11", "fie":"56", "x":"X", "y":"Y", "z":"Z",
                              "ww_functions": [],
                              "ww_class": ["FOO"],
                              "ww_expanded": Webwidgets.Html(
                                  self.session, self.win_id,
                                  html = """Sed ut perspiciatis, unde omnis iste natus error sit voluptatem
                                            accusantium doloremque
                                            laudantium, totam rem
                                            aperiam eaque ipsa, quae
                                            ab illo inventore
                                            veritatis et quasi
                                            architecto beatae vitae
                                            dicta sunt, explicabo.
                                            Nemo enim ipsam
                                            voluptatem, quia voluptas
                                            sit, aspernatur aut odit
                                            aut fugit, sed quia
                                            consequuntur magni dolores
                                            eos, qui ratione
                                            voluptatem sequi nesciunt,
                                            neque porro quisquam est,
                                            qui dolorem ipsum, quia
                                            dolor sit, amet,
                                            consectetur, adipisci
                                            velit, sed quia non
                                            numquam eius modi tempora
                                            incidunt, ut labore et
                                            dolore magnam aliquam
                                            quaerat voluptatem.""")},
                             {"foo":"47", "bar":"12", "fie":"56", "x":"X", "y":"Y", "z":"Z"},
                             {"foo":"47", "bar":"11", "fie":"56", "x":"X", "y":"Y", "z":"Z"},
                             {"foo":"47", "bar":"11", "fie":"57", "x":"X", "y":"Y", "z":"Z"},
                             {"foo":"48", "bar":"11", "fie":"57", "x":"X", "y":"Y", "z":"Z"},
                             {"foo":"48", "bar":"11", "fie":"52", "x":"X", "y":"Y", "z":"Z"},
                             {"foo":"Bertil", "bar":"Bengtsson", "fie":"57", "x":"X", "y":"Y", "z":"Z"}]

            
