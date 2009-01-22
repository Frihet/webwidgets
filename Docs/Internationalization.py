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
Internationalization and localization
=====================================

The standard for translation of user interfaces in the Free Software
world is U{GNU gettext<http://www.gnu.org/software/gettext/>}.
Webwidgets uses GNU gettext in conjunction with some additional tools
and automation features.

Translations in Webwidgets are widget specific, so that "File" can be
translated into e.g. Swedish into either "Arkiv" or "Fil" depending on
if it denotes the "File" menu or a file on the harddisk. Translations
are of course inherited when subclassing a widget. Translations into
the language 'en' for a widget in a file C{foo/bar.py} are located in
the file C{foo/bar.translations/en/LC_MESSAGES/Webwidgets.mo}. The
tool C{compiletranslations.sh} can be used to compile all C{.po}-files
into corresponding C{.mo}-files for all widgets.

Traditionally gettext translation have been done manually by
calling a special function, often called C{_()} on every
string to translate. This function loads the translation from a
gettext library. A tool logically called C{gettext} is used to
extract all string constants surrounded by C{_()} from the
source code to be used as basis for translation. However, this model
cannot handle strings from external sources such as an XML-file,
e.g. the Wwml sources in Webwidgets.

Webwidgets automatically translates all HTML format strings and
all attribute values when drawing widgets. In practice this means
that you never have to call C{_()} yourself (but you can call
it yourself, as a method on the widget object, if need be).
Translatable strings for each widget can be gathered and put into
C{.pot}-files using the tool C{wwgettext} that loads the
python modules and gathers all class level attribute strings using
introspection. Translatable strings for a file C{foo/bar.py}
are placed in C{foo/bar.translations/Webwidgets.pot}.

It is sometimes useful to work with all translations in a single
file, as if Webwidgets did not localize translations to each widget.
This can be achieved using the two tools
C{collecttranslationtemplates.sh} and
C{distributetranslations.sh} that collects and merges
C{.pot}-files and splits and distributes C{.po}-files,
respectively.
"""
