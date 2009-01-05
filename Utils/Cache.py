# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# RowsComposite provides a common model and filter engine for
# row-based widgets (tables, lists, etc)
# Copyright (C) 2008 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

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

import threading
import Webwidgets.Utils.Performance

bucket_count = 10

class NoBucket(object):
    pass

def cache_bucket_get(bucket_list, param):
    for pos in xrange(len(bucket_list)-1, -1, -1):
        if bucket_list[pos][0] == param:
            res = bucket_list[pos]
            del bucket_list[pos]
            bucket_list.append(res)
            return res[1]
    return NoBucket

def cache_bucket_set(bucket_list, param, value):
    bucket_list.append((param,value))
    if len(bucket_list) > bucket_count:
        del bucket_list[0]

def cache_per_class(bucket_object):
    def cache_per_class(function):
        function_id = str(id(function))
        def result_function(self, *arg, **kw):
            if not hasattr(bucket_object, 'buckets'):
                bucket_object.buckets = {}
            bucket_key = (id(type(self)), function_id)
            if bucket_key not in bucket_object.buckets:
                bucket_object.buckets[bucket_key] = []
            param = (self, arg, kw)
            bucket_list = bucket_object.buckets[bucket_key]
            value = cache_bucket_get(bucket_list, param)
            if value is NoBucket:
                try:
                    value = function(self, *arg, **kw)
                except Exception, e:
                    value = e
                cache_bucket_set(bucket_list, param, value)
                Webwidgets.Utils.Performance.add_miss()
            else:
                Webwidgets.Utils.Performance.add_hit()

            if isinstance(value, Exception):
                raise value
            return value
        return result_function
    return cache_per_class

buckets = {'request_part': threading.local(),
           'request': threading.local(),
           'thread': threading.local()}

cache_functions = {'request_part': {'class': cache_per_class(buckets['request_part'])},
                   'request': {'class': cache_per_class(buckets['request'])},
                   'thread': {'class': cache_per_class(buckets['request'])}}

def clear_cache(time = "request"):
    buckets[time].buckets = {}

def cache(time = "request", context="class"):
    if (    time in cache_functions
        and context in cache_functions[time]):
        return cache_functions[time][context]
    raise NotImplementedError

