"""
modul for handling json,yaml objects
- editing objects (delete,append,set values to elements)
- build completion list for object elements
"""

import sys
import os
import json
import re
from copy import deepcopy
from collections import deque
import cmd2
import jmespath

class ObjWalk:
  """ spaziergang durch json objekte """
  def __init__(self, obj):
    self.cl=[]
    self.obj=obj
    self.obj_hist=deque([], 10)
  
  @property
  def obj(self):
    return self._obj

  @obj.setter
  def obj(self, o):
    self._obj=o
    self.cl=self.build_completion_list()

  def _prepare_search_string(self, opath=""):
    """ convert opath to jmespath query string
    params: 
      opath: str -> path to object element (ex.: book[0]:id )
    return:
      opath_search: str -> jmespath query string (ex.: "book"|[0]|"id")
    """
    opath=re.sub(r"(\[\d+\])|:", r"|\1", opath)
    opath_search="|".join([f'"{x}"' if not x.startswith('[') else x for x in opath.split('|') if x])
    return opath_search

  def build_completion_list(self):
    """ bildet completion liste vom gesamten js objekt 
    ['a[0]', 'a[1]', "b", "c", "c:o1", "c:o2", d]
  
    """
    return self._rec_compl_build(self._obj, "", [])

  def get_value(self, s=""):
    """ 
    liefert objekt anhand des suchstrings 
    """
    if not s:
      return self._obj
    s=self._prepare_search_string(s)
    return jmespath.search(s, self._obj)

  def _prepare_obj_for_action(self, opath, only_ref=False):
    """ preparing objects for next processing 
    (append, delete, setting values ) """
    if not only_ref:
      self.obj_hist.append(deepcopy(self.obj))
    obj=self.obj
    idx_or_key=None
    opath_search=self._prepare_search_string(opath)
    opath_split=[x for x in opath_search.split('|') if x]
    for cnt,ele in enumerate(opath_split):
      l=re.match(r"\[(\d+)\]", ele)
      d=re.match(r"\"(.+?)\"", ele)
      if l:
        idx_or_key=int(l.group(1))
      else:
        idx_or_key=d.group(1)
      if (cnt < (len(opath_split)-1)) or only_ref:
        obj=obj[idx_or_key]
    return (obj, idx_or_key)
  

  def _get_object_ref(self, opath=""):
    """ return reference to object or object element 
    params:
      opath: str  -> object element path string (Ex: 'a:b[0]')
    return:
      obj: json   -> reference to object or obj element
    """
    r=self._prepare_obj_for_action(opath, True)
    return r[0]


  def set_object(self, opath ="", value=None):
    """ setting value of object or object element
    params:
      opath: str  -> object element path string (Ex: 'a:b[0]')
      value: json -> value to be set
    return:
    """
    if opath:
      value=JsonWalk.convert_to_json(value)
    else:
      # also check if value is list or dict
      value=JsonWalk.convert_to_json(value, True)
    obj,idx_or_key=self._prepare_obj_for_action(opath) 
    if opath:
      obj[idx_or_key]=value
      self.cl=self.build_completion_list()
    else:
      self.obj=value
    return self.cl

  def set_value(self, s="", v=None):
    """ set value """
    #self._handle_object_ref(s, True, v)
    return self.set_object(s, v)

  def append_value(self, opath="", value=None):
    """ append value to list """
    value=JsonWalk.convert_to_json(value)
    if type(self._get_object_ref(opath)) != list:
      raise TypeError("object path is not a list")
    obj,idx_or_key=self._prepare_obj_for_action(opath)
    if opath:
      obj[idx_or_key].append(value)
    else:
      self.obj.append(value)
    self.cl=self.build_completion_list()
    return self.cl 

  def delete_element(self, opath=""):
    """ delete element ob object """
    if opath:
      try:
        self._get_object_ref(opath)
      except (KeyError,IndexError) as exc:
        raise ValueError("element path %s doesn't exist. exception: %s" % (opath, exc))
    obj,idx_or_key=self._prepare_obj_for_action(opath)
    if opath:
      del obj[idx_or_key]
      self.cl=self.build_completion_list()
    else:
      self.obj={}
    return self.cl 

  def _rec_compl_build(self, o, s="", l=[]):
    """
    recursiv build of completion list
    """
    if type(o)==list:
      if not o:
        l.append(f"{s}")
      for c,v in enumerate(o):
        if type(v) == list:
          self._rec_compl_build(v,f"{s}[{c}]", l)
        elif type(v) == dict:
          self._rec_compl_build(v,f"{s}[{c}]:", l)
        else:
          l.append(f"{s}[{c}]")
    elif type(o)==dict:
      if not o:
        l.append(f"{s}")
      for k,v in o.items():
        if type(v) == list:
          self._rec_compl_build(v,f"{s}{k}", l)
        elif type(v) == dict:
          self._rec_compl_build(v,f"{s}{k}:", l)
        else:
          l.append(f"{s}{k}")
    else:
      print("ERROR: übergebenes objekt ist weder list noch dict")
    return l

    

