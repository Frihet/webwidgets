#! /usr/bin/python

import Webwidgets, types, datetime, sys, os, os.path

class Dummy(object):
    def dummy():
        pass
MethodWrapperType = type(Dummy.dummy.__call__)
BuiltinFunctionOrMethod = type(reduce)

excluded_types = set([id(MethodWrapperType), id(BuiltinFunctionOrMethod)])
excluded_names = set(['ww_classes', 'ww_class_path',
                      '__dict__', '__builtins__', '__file__', '__path__', '__doc__', '__module__', '__name__',
                      'func_dict', 'func_doc', 'func_globals', 'func_name', 'func_code',
                      'co_code'])

def collect_recurse(obj, name, pool, res, level, mod, **options):
    if (   id(obj) in pool
        or id(type(obj)) in excluded_types):
        return
    pool.add(id(obj))

    new_mod_name = False
    if isinstance(obj, types.ModuleType):
        new_mod_name = getattr(obj, '__name__', None)
        new_mod = obj
    if hasattr(obj, '__module__'):
        if obj.__module__ != mod:
            new_mod_name = obj.__module__
            new_mod = sys.modules.get(new_mod_name, None)
    if new_mod_name:
        if 'single-module' in options and mod is not None:
            return res
        mod = new_mod_name
        if mod not in res:
            res[mod] = {'module': new_mod,
                        'strings': set()}

    if 'verbose-collection' in options:
        sys.stderr.write((" " * level) + name + '\n')

    if isinstance(obj, (str, unicode)):
        if 'debug' in options:
            obj = name + ': ' + obj
        res[mod]['strings'].add(obj)
    elif isinstance(obj, list):
        for name, sub_obj in enumerate(obj):
            collect_recurse(sub_obj, str(name), pool, res, level + 1, mod, **options)
    elif isinstance(obj, dict):
        for name, sub_obj in obj.items():
            collect_recurse(sub_obj, str(name), pool, res, level + 1, mod, **options)
    else:
        if hasattr(obj, '__bases__') and hasattr(obj, '__dict__'):
            for sub_obj in obj.__bases__:
                collect_recurse(sub_obj, getattr(sub_obj, '__name__', 'base'), pool, res, level + 1, mod, **options)
            
            for name, sub_obj in obj.__dict__.iteritems():
                if name in excluded_names: continue
                collect_recurse(sub_obj, name, pool, res, level + 1, mod, **options)
        else:
            for name in dir(obj):
                if name in excluded_names: continue
                sub_obj = getattr(obj, name)
                collect_recurse(sub_obj, name, pool, res, level + 1, mod, **options)

    
def collect(objs, **options):
    pool = set()
    pool.add(id(pool))
    res = {None: {'strings': set()}}
    pool.add(id(res))

    for obj in objs:
        collect_recurse(obj, '_', pool, res, 0, getattr(obj, '__module__', None), **options)
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
    strs = list(strs)
    strs.sort()
    for s in strs:
        res.append("msgid ")
        parts = s.split('\n')
        for part in parts[:-1]:
            res.append('"%s\\n"\n' % (escape(part),))
        if parts[-1]:
            res.append('"%s"\n' % (escape(parts[-1]),))
        res.append("msgstr \"\"\n\n")
    return ''.join(res)

if __name__ == "__main__":
    options = {}
    args = list(sys.argv[1:])
    for pos in xrange(len(args) - 1, -1, -1):
        if args[pos].startswith('--'):
            option = args[pos][2:]
            del args[pos]
            value = True
            if '=' in option:
                option, value = option.split('=', 1)
            options[option] = value

    if 'help' in options:

        print """

xgettext-ish program for python that uses introspection and thus works
on code loaded from non .py-files, e.g. wwml-files.

Usage: wwgettext.py [OPTIONS] modulename [modulename ...]
Where the available options are:

    --decorate=all

        For each mmodule reached, create a directory
        module.translations (wherever the module resides), and within
        it a Webwidgets.pot file with the collected strings. Does not
        print collected strings on the screen.
        
    --decorate=modulename

        Like --decorate=all except only modules whose names begin with
        modulename are decorated.

    --verbose-output
    --verbose-collection
        
        """
        sys.exit(0)
    
    res = collect([Webwidgets.Utils.load_class(mod_name)
                   for mod_name in args],
                  **options)
    if 'decorate' in options:
        for name, module in res.iteritems():
            if not 'module' in module or not hasattr(module['module'], '__file__'): continue
            if options['decorate'] != 'all':
                if not name.startswith(options['decorate']): continue
                
            if 'verbose-output' in options:
                sys.stderr.write("Updating .pot-file for %s\n" % (name,))
            translations_dir = os.path.splitext(module['module'].__file__)[0] + os.path.extsep + 'translations'
            if not os.access(translations_dir, os.F_OK):
                os.mkdir(translations_dir)
            file = open(os.path.join(translations_dir, 'Webwidgets.pot'), 'w')
            file.write(output(res[name]['strings']))
            file.close()
    else:
        print output(res[args[0]]['strings'])
