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

import datetime

class Timings(object):
    debug_timer_start = False
    debug_timer_stop = False
    debug_timer_measure = False
   
    class Timing(object):
        def __init__(self, timings, name):
            self.timings = timings
            self.name = name
            self.total = datetime.timedelta()
            self.begin = []
            self.params = []
                            
        def start(self):
            if self.timings.debug_timer_start:
                print "Timings start %s(%s, %s)" % ((self.name,) + self.params[-1])
            self.begin.append(datetime.datetime.now())

        def stop(self):
            if self.timings.debug_timer_stop:
                print "Timings stop %s(%s, %s)" % ((self.name,) + self.params[-1])
            delta = datetime.datetime.now() - self.begin.pop()
            self.measure(self.params.pop(), delta)
            for tm in self.begin:
                tm += delta

        def measure(self, params, delta):
            if self.timings.debug_timer_measure:
                print "Timings measure %s(%s, %s): %s" % ((self.name,) + params + (delta,))
            self.total += delta
            self.timings.measure(self.name, params, delta)

        def __enter__(self): self.start()
        def __exit__(self, exc_type, exc_value, traceback): self.stop()
            
    def __init__(self):
        self.timings = {}

    def __getitem__(self, name):
        return self(name)
        
    def __getattr__(self, name):
        return getattr(self.timings, name)

    def __call__(self, name, *arg, **kw):
        if name not in self.timings:
            timing = self.Timing(self, name)
            self.timings[name] = timing
        else:
            timing = self.timings[name]

        timing.params.append((arg, kw))
        return timing

    def measure(self, name, params, time):
        if params[0]:
            Performance.add(name, params[0][0], float(time.seconds) + 0.000001 * time.microseconds)

