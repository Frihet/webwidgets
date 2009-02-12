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
Instantiation and initialization
================================

    When a session is created a C{Window} widget is instantiated and
    with it any number of child widgets. This child widget
    instantiation can be done either automatically or manually from
    the initialization method of the parent widget.

    If the child widget does not need any special parameters for its
    initialization method, it can be instantiated automatically and
    nothing special is required except for the child widget class to
    be a member of the parent widget class.

    If the child widget class is a class member of the parent widget
    class while it is not desired for it to be instantiated
    automatically, it has to set a special class member variable.
    Whenever manual instantiation is used for child widgets they
    should be initialized in the parents initialization function. The
    parents initialization function should also give those children as
    parameters to the initialization function of its superclass.

    It is practical to encapsulate child widget classes within the
    parent widget class as this makes the widget more portable and
    parts of it more overrideable. The automatic instantiation solves
    the problem nine times out of ten in practice.

Models and filters
==================

    More complex widgets usually interacts with more complex data
    models - database mapped objects, complex middle-ware. The API
    between such a model and the widget is part of the definition of
    the widget, and quite naturally can become rather complex too.

    When subclassing such widgets, the widget-model API might need
    changing too. There might be a need to add more callbacks on the
    model object, or even remove some existing ones replacing them
    with more specific ones.

    Sometimes however the API needs no change, but the data needs to
    be mangled, presented in a different way.

    For this purpose Webwidgets provides filters. Filters sit between
    the model object and the widget, and can be stacked. Each of them
    can transform the data, or the API in some way. Subclasses can
    insert filters anywhere in the stack (usually at predefined
    places, specified by the superclass however).

    When a widget is instantiated, the model class (C{WwModel}) and
    the filter classes (C{WwFilters}) are also instantiated (into
    C{ww_model} and C{ww_filter}) and connected up to each other.

Output
======

    Output to the web browser can come from one of two sources - a
    widget class or a widget instance depending on the presence of
    C{_widget} or C{_widget_class} among the output parameters. In the
    former case, C{class_output(output_options)} is called on the
    class, and in the latter C{output(output_options)} is called on
    the instance.

    The default case is that output comes from the top level widget,
    that is from the window instance. The C{output(output_options)}
    method of the window instance then constructs the output by
    calling C{draw(output_options)}, which recurses to
    C{draw(output_options)} on its child widgets whom in their turn
    may call this function on their children.

    In-page HTML output
    -------------------
    
        The C{draw} method is called on a widget to draw the HTML of
        that widget to be incorporated in the output of draw of its
        parent widget. This method can also optionally register input
        fields and URL arguments.

        The C{Composite} widget is the base class for all widgets that
        have children and provides methods for recursing over the
        C{draw} methods of its children including handling visibility
        of children.

    Raw data output
    ---------------

        For a widget to include raw data, e.g. an image, CSS file that
        is to be referenced by a link in the HTML, it needs to provide
        this data using one of the C{output()} and C{class_output()}
        methods. The widget can construct the URL using the
        C{calculate_url()} method.
"""
