# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework

# Copyright (C) 2009 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

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

"""
Webwidgets depends on the Python library
U{Webware<http://www.webwareforpython.org>}, and you must install it
in order to be able to install Webwidgets.

Although installing Webware is more than half of the work of setting
up Webwidgets, guiding you through that installation process is out of
the scope of this documentation. Please read the relevant Webware
documentation for information on how to do that.

Install Webware and prepare a Webware working directory at
C{/var/www/WebWare}, accessible using Apache and mod_webkit at
C{http://yourhostname.com/WKMod} and directly at
C{http://yourhostname.com:8080}.

Webwidgets needs ExtraPathInfo to be enabled in Webware. To enable
that, edit the file C{$WEBWAREDIR/Configs/Application.config} and set:

    ExtraPathInfo = True

Python modules must be installed in a directory in the python
path. By default, only the directory
C{/usr/lib/python$#PYTONVERSION/site-packages} is in the
python path. Additional directories can be added using the
C{PYTHONPATH} environment variable

Unpack C{Webwidgets.$VERSION.tgz} under
C{/usr/lib/python$#PYTONVERSION/site-packages}, or anywhere else in
the python path.


Security
========

  By default all Webwidgets applications run as the same user, usually
  the"webkit" user. This chapter describes how to improve this situation.


  A webwidgets application does not normally run as the "apache" user
  (as would e.g. most PHP applications). However, it does run as
  whatever user the Webware AppServer it is installed under is run as,
  and in most default setups that would be the"webkit" user, for all
  Webwidgets applications. Sometimes, the AppServer even runs as
  "root"(!).

  Having your Webwidgets applications separate from the webserver
  gives some extra security, but not much. Ideally, each Webwidgets
  application should run as a separate user as to contain a possible
  break-in to the smallest access possible. Such a setup is possible,
  elthough a bit cumbersome, since each such user has to be allocated
  a TCP port on localhost, and have a few lines in the apache config
  added for it. However, B{this approach is strongly recommended.}.
  Also note that this is applicable to any Webware application, not
  just to Webwidgets applications.

  To set up such a system, create a user for each application. Set up
  a Webware work-dir inside the home-directory of each of these.
  Configure each to use a separate port (C{AdapterPort = PORT} in
  C{Configs/AppServer.config}) and configure apache to connect to that
  port for some URLs (C{WKServer localhost PORT} and C{SetHandler
  webkit-handler in httpd.conf}). Then install each application into
  one of these work-dirs (C{Configs/Application.config}).

"""
