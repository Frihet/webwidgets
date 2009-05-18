#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework

# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007-2009 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

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
Redback Webwidgets web developement framework
=============================================

Webwidgets is a framework for writing Web applications as if they
where desktop applications. It employs the same programming paradigm
as Gtk, Qt etc with a tree of widgets with callbacks for events such
as a button press. It encapsulates page loads, session data, form
handling etc into widgets with their own state.

Webwidgets is focused on code reuse and rapid prototyping and
separation between graphic design, interaction design and application
logic. Webwidgets is implemented in the Python programming language
and uses the Webware application server framework.

  - L{Installing Webwidgets<Webwidgets.DocSource.Installation>}

  - L{Install and/or writing webwidgets applications<Webwidgets.Demo>}

  - L{Architecture overview<Webwidgets.DocSource.Architecture>}

  - L{Wwml user interface definition language<Webwidgets.Wwml>}

  - L{Internationalization and
    localization<Webwidgets.DocSource.Internationalization>}

  - L{Access control<Webwidgets.AccessManagerMod>}

  - L{Standard widgets<Webwidgets.Widgets>}

@copyright: 2008-2009 FreeCode AS, Claes Nasten <claes.nasten@freecode.no>
@copyright: 2008-2009 FreeCode AS, Axel Liljencrantz <axel.liljencrantz@freecode.no>
@copyright: 2007-2009 FreeCode AS, Egil Moeller <egil.moller@freecode.no>
@copyright: 2007-2009 Egil Moeller <redhog@redhog.org>
@copyright: 2006 uAnywhere, Egil Moeller <redhog@redhog.org>

@license:
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


"""

# This check is here because Webware might erraneously import us with
# the wrong name first, when loading an index.py-file from the Demo
# directory. Doing so makes us have copies of some classes, which
# fucks up isinstance()-calls.
if __name__ == "Webwidgets":
    # Note: These two are a tiny itsy bitsy bit magical and modifies
    # your entire world when loaded... So make sure they're loaded
    # FIRST!
    import Webwidgets.Compatibility
    import Webwidgets.Wwml
    
    from Webwidgets.Constants import *

    from Webwidgets.BaseObjectMod import *
    from Webwidgets.FilterMod.Base import *
    from Webwidgets.FilterMod.StandardFilters import *
    from Webwidgets.ObjectMod import *

    from Webwidgets.ProgramMod import *
    from Webwidgets.AccessManagerMod import *

    from Webwidgets.Widgets.Base import *

    from Webwidgets.Widgets.RowsMod import *

    from Webwidgets.Widgets.FormattingMod.BaseFormatting import *
    from Webwidgets.Widgets.FormattingMod.ListMod import *

    from Webwidgets.Widgets.InputMod.BaseInput import *

    from Webwidgets.Widgets.RearrangeMod.DialogMod import *
    from Webwidgets.Widgets.RearrangeMod.SwitchingMod import *
    from Webwidgets.Widgets.RearrangeMod.MainMenu import *
    from Webwidgets.Widgets.RearrangeMod.Tree import *
    from Webwidgets.Widgets.RearrangeMod.BaseTableMod import *
    from Webwidgets.Widgets.RearrangeMod.TableMod import *

    from Webwidgets.Widgets.InputMod.LanguageMod import *
    from Webwidgets.Widgets.InputMod.DateInput import *
    from Webwidgets.Widgets.InputMod.HtmlInput import *

    from Webwidgets.Widgets.InputMod.FileEditorMod.TextFileEditor import *
    from Webwidgets.Widgets.InputMod.FileEditorMod.CssFileEditor import *
    from Webwidgets.Widgets.InputMod.FileEditorMod.HtmlFileEditor import *
    from Webwidgets.Widgets.InputMod.FileEditorMod.GenericFileEditor import *
    from Webwidgets.Widgets.InputMod.FileEditorList import *

    from Webwidgets.Widgets.InputMod.LocationInput import *
    from Webwidgets.Widgets.InputMod.AddressMod import *

    from Webwidgets.Widgets.DotGraphMod import *
    from Webwidgets.Widgets.Progress import *

    from Webwidgets.Widgets.ApplicationMod.LogIn import *
    from Webwidgets.Widgets.ApplicationMod.WindowMod import *
    from Webwidgets.Widgets.ApplicationMod.ApplicationWindow import *
