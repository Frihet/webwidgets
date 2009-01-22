# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

"""
This module contains demonstration Webwidgets applications.

A Webwidgets application consist of some python modules and a Webware
context linking it to the Webware application server.

To install a Webwidgets application, say
L{Webwidgets.Demo.WidgetParade}, you need to set up its Webware
context. Add the following to the end of the file
C{$WEBWAREDIR/Configs/Application.config} (note the trailing /Webware
in the path, that is where the webware context resides within the
application)::

    Contexts['WidgetParade'] = '/usr/lib/python$PYTHONVERSION/site-packages/Webwidgets/Demo/WidgetParade/Webware'

Then start your AppServer and direct your browser to C{http://localhost:8080/WidgetParade}.

For more information on how to build your own Webwidgets application, see L{Webwidgets.Demo.WidgetParade}.
"""
