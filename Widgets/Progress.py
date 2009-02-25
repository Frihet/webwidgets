# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Output formatting widgets.
"""

import types, StringIO, cgi, sys, os, threading
import Webwidgets.Utils
import Webwidgets.Constants
import Webwidgets.Widgets.WindowMod
import Webwidgets.Widgets.Formatting
import Webwidgets.Widgets.InputMod.BaseInput
import Webwidgets.Widgets.Composite

class ModalProgressPage(Webwidgets.Widgets.Formatting.ProgressMeter, Webwidgets.Widgets.InputMod.BaseInput.PageLoadNotifier):
    frefresh_interval = 1
    title = "Please wait"
    
    def draw(self, output_options):
        if self.progress_position < self.scale_end:
            Webwidgets.Widgets.WindowMod.HtmlWindow.register_header(
                self, 'Refresh',
                '0;URL=%s' % (self.calculate_url({'transaction': output_options['transaction'],
                                                  'widget': Webwidgets.Utils.path_to_id(self.path)}),))
        return Webwidgets.Widgets.InputMod.BaseInput.PageLoadNotifier.draw(self, output_options)

    def page_load(self, path, mode):
        # Note: page_load is only sent when we have normal input
        # processing, that is, not while the modal full-screen wait
        # page is shown. During that time, only progress() is ever
        # sent. This is important if the done() notification happens
        # to do stuff like remove this very widget...
        if path != self.path: return

        if self.progress_position == self.scale_end:
            self.notify('done')

    def input(self, fields, arguments, output_options):
        self.notify('progress')
        
    def output(self, output_options):
        if self.progress_position == self.scale_end:
            destination = self.calculate_url({'transaction': output_options['transaction']})
            status = '302 Task done'
        else:
            destination = self.calculate_url({'transaction': output_options['transaction'],
                                              'widget': Webwidgets.Utils.path_to_id(self.path)})
            status = '200 In progress'
        result = {Webwidgets.Constants.OUTPUT: """
<html>
 <head>
  <title>%(title)s
  <link href='%(style)s' rel='stylesheet' type='text/css' />
 </head>
 <body>
  <div class="%(progress_dialog_class)s">
   <div>%(title)s</div>
   <div>%(progress_bar)s<div>
  </div>
 </body>
</html>
                """ % {'style': self.window.calculate_url_to_directory_server('Webwidgets.HtmlWindow',
                                                                              ['Widgets.css'],
                                                                              output_options),
                       'title': self._(self.title, output_options),
                       'progress_bar': Webwidgets.Widgets.Formatting.ProgressMeter.draw(self, output_options),
                       'progress_dialog_class': Webwidgets.Utils.classes_to_css_classes(self.ww_classes, ['progress_dialog'])
                       },
                'Refresh': "%s;URL=%s" % (self.frefresh_interval, destination),
                'Content-type': "text/html",
                'Status': status,
                }

        return result

class ModalWaitPage(ModalProgressPage):
    step = 1.0

    def progress(self, path):
        self.progress_position += self.step

class ModalThreadProgressPage(ModalProgressPage):
    class Thread(threading.Thread):
        def __init__(self, progress, *arg, **kw):
            self.progress = progress
            threading.Thread.__init__(self, *arg, **kw)

        def run(self, *arg, **kw):
            try:
                try:
                    self.progress.result = self.progress.run(*arg, **kw)
                except Exception, e:
                    self.progress.append_exception()
            finally:
                self.progress.progress_position = 100.0

    def __init__(self, *arg, **kw):
        ModalProgressPage.__init__(self, *arg, **kw)
        self.thread = self.Thread(progress = self)

    def start(self, *arg, **kw):
        self.result = None
        self.thread.start(*arg, **kw)

    def run(self, *arg, **kw):
        raise NotImplementedError

class ModalThreadProgressPageDialog(Webwidgets.Widgets.Composite.InfoDialog, ModalThreadProgressPage):
    buttons = {}
    
    class Head(Webwidgets.Widgets.Formatting.Html):
        html = "Operation in progress"
        
    class Body(Webwidgets.Widgets.Formatting.Html):
        html = "The operation is in progress. Please wait. If this page does not refresh automatically, if it does not, refresh the page manually."

    def __init__(self, *arg, **kw):
        Webwidgets.Widgets.Composite.InfoDialog.__init__(self, *arg, **kw)
        ModalThreadProgressPage.__init__(self, *arg, **kw)
        self.start()

    def done(self, path):
        dialog = self.Done(self.session, self.win_id)
        if self.result is not None:
            dialog['Body'].html = self.result
        Webwidgets.DialogContainer.add_dialog_to_nearest(
            self, dialog)
        self.close()

    def draw(self, output_options):
        return (  Webwidgets.Widgets.Composite.InfoDialog.draw(self, output_options)
                + ModalThreadProgressPage.draw(self, output_options))

    class Done(Webwidgets.Widgets.Composite.InfoDialog):
        class Head(Webwidgets.Widgets.Formatting.Html):
            html = "Done"
        class Body(Webwidgets.Widgets.Formatting.Html):
            html = "The operation completed successfully"
