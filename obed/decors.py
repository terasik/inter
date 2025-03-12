# decorators

__all__ = ["open_at_first", "close_at_first", "expand_user"]

import os

def open_at_first(f):
  def inner(*args):
    inst=args[0]
    if inst.obj is not None:
      return f(*args)
    inst.warn("open/create new object at first")
    return
  return inner

def close_at_first(f):
  def inner(*args):
    inst=args[0]
    if inst.obj is None:
      return f(*args)
    inst.warn("close your current object at first")
    return
  return inner

def expand_user(f):
  def inner(*args):
    #print("len args %s" % len(args))
    new_args=list(args)
    try:
      #print(new_args)
      new_args[-1]=os.path.expanduser(args[-1])
    except:
      pass
    return f(*new_args)
  return inner
