"""
Webwidgets web developement framework

 - Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>

 - Copyright (C) 2007 FreeCode AS, Egil Moeller <redhog@redhog.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

A webwidgets application consists of a subclass of
L{Webwidgets.Program.Program}, in a file named as the subclass, in a
Webware context, and an interface defined using subclasses of the
various widgets from L{Webwidgets.Widgets}.

Example application (in test.py):

 >>> import Webwidgets
 ...
 >>> class MyWindow(Webwidgets.Window):
 ...    #some widgets goes here
 ... 
 >>> class test(Webwidgets.Program):
 ...    class Session(Webwidgets.Program.Session):
 ...        def newWindow(self, winId):
 ...            return MyWindow(self, winId)

"""

import Compatibility
import Wwml
from Constants import *
from Program import *
from AccessManager import *

from Widgets.Base import *
from Widgets.Formatting import *
from Widgets.Input import *
from Widgets.Composite import *
from Widgets.GBOList import *
from Widgets.InputCombinations import *
