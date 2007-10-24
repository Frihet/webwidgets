#! /usr/bin/python

import Webwidgets, types, datetime, sys

class Dummy(object):
    def dummy():
        pass
MethodWrapperType = type(Dummy.dummy.__call__)
BuiltinFunctionOrMethod = type(reduce)

excluded_types = set([id(MethodWrapperType), id(BuiltinFunctionOrMethod)])
excluded_names = set(['__dict__', 'func_code', 'co_code'])

def collect_recurse(obj, name, pool, res, level, mod):
    if (   id(obj) in pool
        or id(type(obj)) in excluded_types):
        return
    pool.add(id(obj))

    #print (" " * level) + name

    if isinstance(obj, types.ModuleType):
        mod = getattr(obj, '__name__', None)
        if mod not in res:
            res[mod] = {'module': obj,
                        'strings': set()}

    if isinstance(obj, (str, unicode)):
        res[mod]['strings'].add(obj)
    elif isinstance(obj, list):
        for name, sub_obj in enumerate(obj):
            collect_recurse(sub_obj, str(name), pool, res, level + 1, mod)
    elif isinstance(obj, dict):
        for name, sub_obj in obj.items():
            collect_recurse(sub_obj, str(name), pool, res, level + 1, mod)
    else:
        for name in dir(obj):
            if name in excluded_names: continue
            sub_obj = getattr(obj, name)
            collect_recurse(sub_obj, name, pool, res, level + 1, mod)
    
def collect(obj):
    pool = set()
    pool.add(id(pool))
    res = {None: {'strings': set()}}
    pool.add(id(res))

    mod = None
    mod = getattr(obj, '__module__', None)
    
    collect_recurse(obj, '_', pool, res, 0, mod)
    return res

header = """# SOME DESCRIPTIVE TITLE.
# Copyright (C) AUTHOR AND YEAR
#
msgid ""
msgstr ""
"Project-Id-Version: 0.1\\n"
"POT-Creation-Date: %(date)s\\n"
"PO-Revision-Date: DATEANDTIME\\n"
"Last-Translator: EMAIL\\n"
"Language-Team: EMAIL\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"

"""


dateformat = "%a %b %d %H:%M:%S %Y"

def escape(s):
    return s.replace('\\', '\\\\').replace('\"', '\\"').replace('\t', '\\t').replace('\r', '\\r').replace('\n', '\\n')

def output(strs):
    res = [header % {'date': datetime.datetime.now().strftime(dateformat)}]
    for s in strs:
        res.append("msgid ")
        parts = s.split('\n')
        for part in parts[:-1]:
            res.append('"%s\\n"\n' % (escape(part),))
        if parts[-1]:
            res.append('"%s"\n' % (escape(parts[-1]),))
        res.append("msgstr ""\n\n")
    return ''.join(res)

if __name__ == "__main__":
    mod_name = sys.argv[1]
    res = collect(Webwidgets.Utils.load_class(mod_name))
    print output(res[mod_name]['strings'])
