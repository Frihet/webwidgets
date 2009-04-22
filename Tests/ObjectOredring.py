import Webwidgets.ObjectMod

class PR(Webwidgets.ObjectMod.Object):
    ww_class_orderings = set()
    ww_child_class_orderings = set('x')

class R(Webwidgets.ObjectMod.Object):
    ww_class_orderings = set('x')
    ww_child_class_orderings = set()

def print_class_info(cls):
    print "%s => %s: %s => %s" % (', '.join(pre.__name__ for pre in cls.ww_x_metadata['pre']),
                                  cls.ww_x_metadata['level'],
                                  cls.__name__,
                                  ', '.join(post.__name__ for post in cls.ww_x_metadata['post']))
    print "    %s => %s: %s => %s" % (', '.join(post.__name__ for post in cls.ww_x_metadata['pre_backlink']),
                                      cls.ww_x_metadata['level'],
                                      cls.__name__,
                                      ', '.join(pre.__name__ for pre in cls.ww_x_metadata['post_backlink']))

print "Explicit pre-chaining:"
class A(R): pass
class B(R):
    ww_x_pre = set((A,))
class C(R):
    ww_x_pre = set((B,))

print_class_info(A)
print_class_info(B)
print_class_info(C)
print

print "Member class implicit chaining:"
class PA(PR):
    class CA(R): pass
    class CB(R): pass
    class CC(R): pass

print_class_info(PA.CA)
print_class_info(PA.CB)
print_class_info(PA.CC)
print

print "Member class implicit chaining with explicit reversal of chaining between two members:"
class PB(PR):
    class CA(R): pass
    class CB(R): pass
    CB.add_class_in_ordering('x', post=[CA])
    class CC(R): pass

print_class_info(PB.CA)
print_class_info(PB.CB)
print_class_info(PB.CC)
print


print "Member class implicit chaining with explicit reversal of chaining between two members by superclass:"
class A(R): pass
class B(R): pass
B.add_class_in_ordering('x', post=[A])
class PC(PR):
    class CA(A): pass
    class CB(B): pass
    class CC(R): pass

print_class_info(PC.CA)
print_class_info(PC.CB)
print_class_info(PC.CC)
print


print "Member class implicit chaining with memberchip chaining inheritance from outer class subclassing:"
class PD(PR):
    class CA(R): pass
    class CB(R): pass
    CB.add_class_in_ordering('x', post=[CA])
    class CC(R): pass
class PE(PD):
    class CA(PD.CA): pass
    class CC(PD.CC): pass
    class CX(R): pass
 
print_class_info(PE.CA)
print_class_info(PE.CB)
print_class_info(PE.CC)
print_class_info(PE.CX)
print


print "Multiple inheritance from chain with non-listed intermediate:"
class A(R): pass
class B(R): ww_x_pre = (A,)
class C(R): ww_x_pre = (B,)
class D(A, C): pass

print_class_info(A)
print_class_info(B)
print_class_info(C)
print_class_info(D)
