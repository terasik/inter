# decorators

__all__ = ["open_at_first", "close_at_first", "expand_user"]

import os
from functools import wraps
from inspect import signature

def open_at_first(f):
    """ used to warn user, that new obejct
    have to be created/opened
    """
    @wraps(f)
    def inner(*args, **kwargs):
        inst=args[0]
        if inst.obj is not None:
            return f(*args, **kwargs)
        inst.warn("open/create new object at first")
        return
    return inner

def close_at_first(f):
    """ used to warn user, that current obejct 
    have to be closed
    """
    @wraps(f)
    def inner(*args, **kwargs):
        inst=args[0]
        if inst.obj is None:
            return f(*args, **kwargs)
        inst.warn("close your current object at first")
        return
    return inner

def expand_user_s(f):
    """ used to expand ~ in path strings 
    """
    def inner(*args, **kwargs):
        new_args=list(args)
        try:
            new_args[-1]=os.path.expanduser(args[-1])
        except:
            pass
        return f(*new_args, **kwargs)
    return inner

def expand_user(path_arg="path"):
    def decor(f):
        @wraps(f)
        def inner(*args, **kwargs):
            sign=signature(f)
            bind=sign.bind(*args, **kwargs)
            if path_arg in bind.arguments:
                bind.arguments[path_arg]=os.path.expanduser(bind.arguments[path_arg])
            if path_arg in bind.kwargs:
                bind.arguments['kwargs'][path_arg]=os.path.expanduser(bind.arguments['kwargs'][path_arg])
            return f(*bind.args, **bind.kwargs)
        return inner
    return decor
