#!/usr/bin/env python3

o1={
    "a": ["l1", "l2"],
    "b": "s1",
    "c": {"o1": "v1","o2": "v2", "o3": [1, {"r":"t"}, "trtv"]},
    "d": "s2",
    "e": ["lo1", {"lo2": []}],
    "f": {}
}

o2=[ {"a":"b"}, 23 , ["g", "d"]]



def rec_build(o, s="", l=[]):
  #print(f"depth: {d} s: {s}")
  if type(o)==list:
    if not o:
      l.append(f"{s}")
    for c,v in enumerate(o):
      if type(v) == list:
        rec_build(v,f"{s}[{c}]", l)
      elif type(v) == dict:
        rec_build(v,f"{s}[{c}].", l)
      else:
        l.append(f"{s}[{c}]")
  elif type(o)==dict:
    if not o:
      l.append(f"{s}")
    for k,v in o.items():
      if type(v) == list:
        rec_build(v,f"{s}{k}", l)
      elif type(v) == dict:
        rec_build(v,f"{s}{k}.", l)
      else:
        l.append(f"{s}{k}")
  else:
    print("ERROR: übergebenes objekt ist weder list noch dict")
  return l

         
l1=rec_build(o1, "", [])
print("fertige liste 1: ", l1)
l2=rec_build(o2, "", [])
print("fertige liste 2: ", l2)


