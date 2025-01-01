#!/usr/bin/env python

def _make_it_sense(f):
  def inner(*args):
    inst=args[0]
    if inst.v:
      return f(*args)
    inst.pwarn()
    return
  return inner

class ama:
  
  def __init__(self, v=None):
    self.v=v

  def pwarn(self):
    print("WARNING: it makes no sense")

  @staticmethod
  def make_it_sense(f):
    def inner(*args):
      inst=args[0]
      if inst.v:
        return f(*args)
      inst.pwarn()
      return
    return inner
       
  @make_it_sense
  def set(self, opath="spath", value="123"):
    print(f"set {opath}: {value}")
    self.v=value

  @make_it_sense
  def delete(self, opath="dpath"):
    print(f"delete {opath}")
    self.v=None
