import os

# Work around a brain-dead "fix" in Webwar e: Try doing Popen and ask
# it to chdir in the new process before exec and see what happens w
# their so-called fix in place... Did I say BORKED BEYOUND
# IMAGINATION?

try:
    os.chdir('.')
except:
    broken_chdir = os.chdir
    def chdir(dir):
        return broken_chdir(dir, force = True)
    os.chdir = chdir
