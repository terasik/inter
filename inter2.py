#!/usr/bin/env python3
import sys
import os
import json
import re
from copy import deepcopy
from collections import deque
import cmd2
import jmespath

class JsonWalk:
  """ spaziergang durch json objekte """
  def __init__(self, js):
    #print("js: %s type: %s" % (js, type(js)))
    self.cl=[]
    self.js=js
    self.js_hist=deque([], 10)
  
  @property
  def js(self):
    return self._js

  @js.setter
  def js(self, o):
    self._js=o
    self.cl=self.build_completion_list()
    #print(self.cl)

  def _prepare_search_string(self, s):
    """ replace ':' with '|'
    make quotes bei keys
    """
    s=re.sub(r"(\[\d+\])|:", r"|\1", s)
    s="|".join([f'"{x}"' if not x.startswith('[') else x for x in s.split('|') if x])
    return s

  def build_completion_list(self):
    """ bildet completion liste vom gesamten js objekt 
    ['a[0]', 'a[1]', "b", "c", "c:o1", "c:o2", d]
  
    """
    return self._rec_compl_build(self._js, "", [])

  def get_value(self, s=""):
    """ 
    liefert objekt anhand des suchstrings 
    """
    if not s:
      return self._js
    s=self._prepare_search_string(s)
    return jmespath.search(s, self._js)

  @staticmethod
  def convert_to_json(v, check_type=False, raise_error=False):
    """ try to convert value to json
    if it doesn't work return 'v'"""
    if check_type: raise_error=True
    try:
      js=json.loads(v)
    except json.JSONDecodeError as _jexc:
      if raise_error:
        raise TypeError("json error: %s" % _jexc) 
      return v
    if check_type and not isinstance(js, (list,dict)):
      raise TypeError("json is not dict or list")
    return js

  def _handle_object_ref(self, s=None, set_val=False, v=None):
    """ return reference to part of js 
    described with s
    """
    if not s and not set_val:
      return self._js
    #js_copy=deepcopy(self._js)
    if set_val:
      self.js_hist.append(deepcopy(self._js))
      v=JsonWalk.convert_to_json(v)
    _js=self._js
    o=self._js
    s=self._prepare_search_string(s)
    s_split=s.split('|')
    for c,e in enumerate(s_split):
      l=re.match(r"\[(\d+)\]", e)
      d=re.match(r"\"(.+?)\"", e)
      if l:
        idx_or_key=int(l.group(1))
      else:
        idx_or_key=d.group(1)
      if set_val and c==(len(s_split)-1):
        o[idx_or_key]=v
        self.js=_js
        #self.build_completion_list()
      o=o[idx_or_key]
    return o

  def set_object(self, opath ="", value=None):
    """ setting value of object or object elements
    params:
      opath: str  -> object element path string (Ex: 'a:b[0]')
      value: json -> value to be set
    return:
    """
    print(f"opath: {opath}, value={value}")
    if opath:
      value=JsonWalk.convert_to_json(value)
    else:
      # also check if value is list or dict
      value=JsonWalk.convert_to_json(value, True)
    self.js_hist.append(deepcopy(self.js))
    obj=self.js
    opath_search=self._prepare_search_string(opath)
    opath_split=[x for x in opath_search.split('|') if x]
    print(f"opath: {opath}, value={value}, opath_search: {opath_search}, opath_split: {opath_split}")
    
    for cnt,ele in enumerate(opath_split):
      l=re.match(r"\[(\d+)\]", ele)
      d=re.match(r"\"(.+?)\"", ele)
      if l:
        idx_or_key=int(l.group(1))
      else:
        idx_or_key=d.group(1)
      if cnt < (len(opath_split)-1):
        obj=obj[idx_or_key]
    if opath:
      print(f"setting obj: {obj}  idx_or_key: {idx_or_key} to {value} type: {type(value)}")
      obj[idx_or_key]=value
      self.build_completion_list()
    else:
      print(f"setting obj: {obj} to {value} type: {type(value)}")
      self.js=value

    


  def set_value(self, s="", v=None):
    """ set value """
    #self._handle_object_ref(s, True, v)
    self.set_object(s, v)    

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

  @staticmethod
  def load(path):
    """ lade json datei """
    with open(path) as _fr:
      js=json.load(_fr)
    return js

  @staticmethod
  def dumps(o):
    """ gibt formatierten json string zurück """
    return json.dumps(o, indent=2)    
    
  @staticmethod
  def dump(o, path):
    """ write object o to path """
    with open(path, 'w') as _fw:
      json.dump(o, _fw, indent=2)
    

class App(cmd2.Cmd):

  """ handle json/yaml interactive
  cmd list:

    open  <file>                    -> open json/yaml file
    print <e> .. <e>                -> print values of elements
    update <e> -k <key> -v <value>  -> combine element with {key: value}
    set <e> -v <value>              -> set value
    new <file>                      -> new file
                                        if file exists 'open' will be used
  """

  def __init__(self):
    super().__init__()
    self.prompt="> "
    #self.complete_open=self.path_complete
    self.jsw=None
    self.jcl=[]
    #self.hcl=[]
    self.wrk_file=None

  def _reset(self):
    self.jsw=None
    self.jcl=[]
    #self.hcl=[]
    self.wrk_file=None

  def hist_choice_provider(self):
    if self.jsw:
      l=len(self.jsw.js_hist)
      return [str(x) for x in range(l)]
    return []

  def json_choice_provider(self):
    return self.jcl

  ############# new ##########################
  @cmd2.with_argument_list
  def do_new(self, s):
    """  create new object """
    js={}
    if len(s) > 1:
      self.pwarning("loading only first arg. other args will be ignored")
    if not self.jsw:
      try:
        if s:
          js=JsonWalk.convert_to_json(s[0], True, True)
      except Exception as _exc:
        self.perror("laden der json nicht möglich: %s" % _exc)
      else:
        #self.wrk_file=s
        self.jsw=JsonWalk(js)
        self.jcl=self.jsw.cl
        self.psuccess("json geladen")
    else:
      self.pwarning("close your working object at first")
    
  ############# open ##########################
  def do_open(self, s):
    """ öffnet json/yaml datei
    usage:
      open <file>
    """
    if not self.jsw:
      #self.poutput("sim sim öffne %s ..." % s)
      try:
        js=JsonWalk.load(s)
      except Exception as _exc:
        self.perror("laden der json nicht möglich %s:" % _exc)
      else:
        self.wrk_file=s
        self.jsw=JsonWalk(js)
        self.jcl=self.jsw.cl
        self.psuccess("json geladen")
    else:
      self.pwarning("close your working object at first")
      
  def complete_open(self, text, line, begidx, endidx):
    """path completion für open"""
    return self.path_complete(text, line, begidx, endidx)

  ############### save ########################

  def do_save(self, s):
    """ save to file s
    if s is not provided or empty,none
    save to wrk_file """
    if s and self.jsw is not None:
      self.poutput("saving to %s" % s)
      JsonWalk.dump(self.jsw.js, s)
    elif not s and self.jsw is not None:
      self.poutput("saving to current working file")
      JsonWalk.dump(self.jsw.js, self.wrk_file)
    else:
      self.pwarning("please open file at first")

  def complete_save(self, text, line, begidx, endidx):
    """path completion for save/write"""
    return self.path_complete(text, line, begidx, endidx)

  ##################### show hist ###################
  @cmd2.with_argument_list
  def do_showhist(self,s):
    """ show hist entries """
    if self.jsw:
      if s:
         for c in s:
          self.poutput("hist Nr. %s:\n%s" % (c, JsonWalk.dumps(self.jsw.js_hist[int(c)])))
      else: 
        for c,e in enumerate(self.jsw.js_hist):
          self.poutput("hist Nr. %s:\n%s" % (c, JsonWalk.dumps(e)))
    else:
      self.pwarning("please open file at first")

  def complete_showhist(self, text, line, begidx, endidx):
    """ completion für print """
    return self.basic_complete(text, line, begidx, endidx, match_against=self.hist_choice_provider())

  ##################### close #####################
  def do_close(self, s):
    """ close editing json objects """
    if self.jsw:
      #if len(self.jsw.js_hist):
      i=self.read_input("save object before closing? ", completion_mode=cmd2.CompletionMode.CUSTOM, choices=["yes", "no"])
      if re.match("yes|ja|y|j", i, re.I):
        i=self.read_input("saving object to: ", completion_mode=cmd2.CompletionMode.CUSTOM, completer=cmd2.Cmd.path_complete)
        self.do_save(i)
      self._reset()
    else:
      self.pwarning("please open file at first")

  ##################### print #####################
  @cmd2.with_argument_list
  def do_print(self, s):
    """ zeige geladenes json """
    #self.poutput("print compl list: %s" % self.jsw.cl)
    if self.jsw:
      if not s:
        self.poutput(JsonWalk.dumps(self.jsw.js))
      else:
        for e in s:
          self.poutput("%s:\n%s" % (e, JsonWalk.dumps(self.jsw.get_value(e))))
    else:
      self.pwarning("please open file at first")

  def complete_print(self, text, line, begidx, endidx):
    """ completion für print """
    return self.delimiter_complete(text, line, begidx, endidx, match_against=self.jcl, delimiter=":")

  ###################### set_val ########################
  set_parser=cmd2.Cmd2ArgumentParser()
  set_parser.add_argument('elements', help='json element(s)', nargs='*', choices_provider=json_choice_provider)
  set_parser.add_argument('-v', '--value', nargs=1, help='value of json element')

  
  @cmd2.with_argparser(set_parser)
  def do_set_val(self, args):
    """ set value of json element """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    if args.elements:
      for e in args.elements:
        self.poutput("setting element %s to %s" % (e, args.value[0]))
        self.jsw.set_value(e,args.value[0])
    else:
      self.poutput("setting whole object to %s" % (args.value[0]))
      self.jsw.set_value("", args.value[0])
    self.jcl=self.jsw.cl
      
  
if __name__ == '__main__':
  c = App()
  sys.exit(c.cmdloop())
