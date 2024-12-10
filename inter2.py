#!/usr/bin/env python3
import sys
import os
import json
import re
from copy import deepcopy
import cmd2
import jmespath

class JsonWalk:
  """ spaziergang durch json objekte """
  def __init__(self, js):
    self.cl=[]
    self.js=js
  
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

  def _convert_to_json(self, v):
    """ try to convert value to json
    if it doesn't work return 'v'"""
    try:
      js=json.loads(v)
    except json.JSONDecodeError:
      return v
    return js

  def _handle_object_ref(self, s=None, set_val=False, v=None):
    """ return reference to part of js 
    described with s
    """
    if not s:
      return self._js
    if set_val:
      v=self._convert_to_json(v)
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
        self.build_completion_list()
      o=o[idx_or_key]
    return o

  def set_value(self, s="", v=None):
    """ set value """
    self._handle_object_ref(s, True, v)
    
    
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
    return json.dumps(o, indent=4)    
    

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

  def json_choice_provider(self):
    return self.jcl

  ############# open ##########################
  def do_open(self, s):
    """ öffnet json/yaml datei
    usage:
      open <file>
    """
    self.poutput("sim sim öffne %s ..." % s)
    try:
      js=JsonWalk.load(s)
    except Exception as _exc:
      self.perror("laden der json nicht möglich %s:" % _exc)
    else:
      self.jsw=JsonWalk(js)
      self.jcl=self.jsw.cl
      self.psuccess("json geladen")
      
  def complete_open(self, text, line, begidx, endidx):
    """path completion für open"""
    return self.path_complete(text, line, begidx, endidx)

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
      self.pwarning("bitte erstmal eine datei öffnen")

  def complete_print(self, text, line, begidx, endidx):
    """ completion für print """
    return self.delimiter_complete(text, line, begidx, endidx, match_against=self.jcl, delimiter=":")

  ###################### set_val ########################
  set_parser=cmd2.Cmd2ArgumentParser()
  set_parser.add_argument('elements', help='json element(s)', nargs='+', choices_provider=json_choice_provider)
  set_parser.add_argument('-v', '--value', nargs=1, help='value of json element')

  
  @cmd2.with_argparser(set_parser)
  def do_set_val(self, args):
    """ set value of json element """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    for e in args.elements:
      self.poutput("setting %s to %s" % (e, args.value[0]))
      self.jsw.set_value(e,args.value[0])


  
if __name__ == '__main__':
  c = App()
  sys.exit(c.cmdloop())
