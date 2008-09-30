from __future__ import with_statement
import locale, threading, contextlib

lock = threading.Lock()

@contextlib.contextmanager
def locale_set(**locale_spec):
    lock.acquire()
    saved_locale = {}
    for (cat, name) in locale_spec.iteritems():
        name = locale.normalize(name)
        cat = getattr(locale, cat)
        saved_locale[cat] = locale.getlocale(cat)
        locale.setlocale(cat, name)
    try:
        yield
    finally:
        for (cat, name) in saved_locale.iteritems():
            locale.setlocale(cat, name)
        lock.release()


def format(locale_spec,	*arg, **kw):
    with locale_set(**locale_spec):
        return locale.format(*arg, **kw)

def format_string(locale_spec,*arg, **kw):
    with locale_set(**locale_spec):
        return locale.format_string(*arg, **kw)

def currency(locale_spec, *arg, **kw):
    with locale_set(**locale_spec):
        return locale.currency(*arg, **kw)

def str(locale_spec, *arg, **kw):
    with locale_set(**locale_spec):
        return locale.str(*arg, **kw)

def atof(locale_spec, *arg, **kw):
    with locale_set(**locale_spec):
        return locale.atof(*arg, **kw)

def atoi(locale_spec, *arg, **kw):
    with locale_set(**locale_spec):
        return locale.atoi(*arg, **kw)


