"""
modul for handling json,yaml objects
- editing objects (delete,append,set values to elements)
- build completion list for object elements
"""
import re
from copy import deepcopy
from collections import deque
import cmd2
import jmespath
from obed.utils import convert_to_json
from obed.yavault import YamlVault

class ObjWalk(cmd2.Cmd):
  """ class to walk through (json,yaml) objects 
  and 
    - editing object elements
    - build completion lists for existing elemets
    - getting values ob object elements
  """
  def __init__(self, obj=None):
    super().__init__()
    self.coml_list=[]
    self.obj=obj
    self.obj_hist=deque([], 50)
  
  @property
  def obj(self):
    return self._obj

  @obj.setter
  def obj(self, obj):
    self._obj=obj
    self.build_completion_list()

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
    """ build completion  list for object paths
    (opath parameters by many functions)
    ['a[0]', 'a[1]', "b", "c", "c:o1", "c:o2", d]
  
    """
    self.compl_list=self._rec_compl_build(self._obj, "", [])

  def get_value(self, opath=""):
    """ return value of element path (opath)
    """
    if not opath:
      return self._obj
    opath_search=self._prepare_search_string(opath)
    return jmespath.search(opath_search, self.obj)

  def _prepare_obj_for_action(self, opath, only_ref=False):
    """ preparing objects for next processing 
    (append, delete, setting values ) 
    params:
      opath: str  -> object element path string (Ex: 'a:b[0]')
      only_ref: bool -> if true get element of object 
                          which described by opath
                        if false return element ob obejct which 
                          will be edited
      return: tuppel -> (object element, index_or_key of element)
    
    """
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

  def copy_element(self, ele, dest):
    """ copy object element to dest.
    """
    obj_ele,idx_or_key_ele=self._prepare_obj_for_action(ele) 
    obj_dest,idx_or_key_dest=self._prepare_obj_for_action(dest) 
    #self.poutput("ele : obj=%s idx_or_key=%s" % (obj_ele, idx_or_key_ele))
    #self.poutput("dest: obj=%s idx_or_key=%s" % (obj_dest, idx_or_key_dest))
    obj_src_dc=deepcopy(obj_ele[idx_or_key_ele])
    if dest:
      if not isinstance(obj_dest[idx_or_key_dest], (list, dict)):
        #self.poutput("dest type is not list,dict. setting")
        obj_dest[idx_or_key_dest]=obj_src_dc
      elif isinstance(obj_dest[idx_or_key_dest], (list)):
        #self.poutput("dest type is list. appending")
        obj_dest[idx_or_key_dest].append(obj_src_dc)
      elif isinstance(obj_dest[idx_or_key_dest], (dict)):
        if isinstance(obj_ele[idx_or_key_ele], (dict)):
          #self.poutput("dest and src type is dict. updating")
          obj_dest[idx_or_key_dest].update(obj_src_dc)
        else:
          #self.poutput("dest type is dict. src type is not dict. setting")
          obj_dest[idx_or_key_dest]=obj_src_dc
      else:
        self.perror("unknown dest type. copy not possible")
    else:
      self.pwarning("copy to root of object not implemeted yet. please use 'setval' or 'append'")
    self.build_completion_list()

  def set_value_vault(self, opath, value, vault_id):
    """ setting value as vault value
    """
    if not isinstance(value, (YamlVault)):
      if not vault_id:
        raise ValueError("vault_id not provided") 
      value=YamlVault(plain_text=value, vault_id=vault_id[0])
    obj,idx_or_key=self._prepare_obj_for_action(opath) 
    obj[idx_or_key]=value
    self.build_completion_list()

  def append_value_vault(self, opath, value, vault_id):
    """ appending vault values to list
    """
    if not isinstance(value, (YamlVault)):
      if not vault_id:
        raise ValueError("vault_id not provided") 
      value=YamlVault(plain_text=value, vault_id=vault_id[0])
    if type(self._get_object_ref(opath)) != list:
      raise TypeError("object path is not a list. only appending to lists ist possible!")
    obj,idx_or_key=self._prepare_obj_for_action(opath)
    if opath:
      obj[idx_or_key].append(value)
    else:
      self.obj.append(value)
    self.build_completion_list()
          
  def set_value(self, opath ="", value=None):
    """ setting value of object or object element
    params:
      opath: str  -> object element path string (Ex: 'a:b[0]')
      value: json -> value to be set
    return: -
    """
    if opath:
      value=convert_to_json(value)
    else:
      # also check if value is list or dict
      value=convert_to_json(value, True)
    obj,idx_or_key=self._prepare_obj_for_action(opath) 
    if opath:
      obj[idx_or_key]=value
      self.build_completion_list()
    else:
      self.obj=value

  def append_value(self, opath="", value=None):
    """ append value to list in object
    described by opath
    """
    value=convert_to_json(value)
    if type(self._get_object_ref(opath)) != list:
      raise TypeError("object path is not a list. only appending to lists ist possible!")
    obj,idx_or_key=self._prepare_obj_for_action(opath)
    if opath:
      obj[idx_or_key].append(value)
    else:
      self.obj.append(value)
    self.build_completion_list()

  def delete_element(self, opath=""):
    """ delete object element
    described by opath
    """
    if opath:
      try:
        self._get_object_ref(opath)
      except (KeyError,IndexError) as exc:
        raise ValueError("element path %s doesn't exist. exception: %s" % (opath, exc))
    obj,idx_or_key=self._prepare_obj_for_action(opath)
    if opath:
      del obj[idx_or_key]
      self.build_completion_list()
    else:
      self.obj={}

  def _rec_compl_build(self, o, s="", l=[]):
    """
    recursiv build of completion list. 
    walk through object and check if lements are lists
    or dicts. 
    by dicts append ':' to dict key (ex.: book:id)
    by lists append '[]' with index (ex.: [1][45])
    by others go to next element. example:
    object: { "book": {"id": 123, "authors": ["kira", "juraj]}}"}
    complition list: ["book:", "book:id", "book:authors[0]", "book:authors[1]"]
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
      #self.pwarning("")
      pass
    return l

