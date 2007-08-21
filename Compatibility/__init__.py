import __builtin__


if not hasattr(__builtin__, 'set'):
    import sets
    __builtin__.set = sets.Set
