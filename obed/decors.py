# decorators

__all__ = ["open_at_first", "close_at_first"]

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
