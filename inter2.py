#!/usr/bin/env python3
import sys
import os
import json
import re
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
    self._get_object_ref(s)
    s=self._prepare_search_string(s)
    return jmespath.search(s, self._js)

  def _get_object_ref(self, s=""):
    """ return reference to part of js 
    described with s
    """
    if not s:
      return self._js
    o=self._js
    s=self._prepare_search_string(s)
    for e in s.split('|'):
      l=re.match(r"\[(\d+)\]", e)
      d=re.match(r"\"(.+?)\"", e)
      print("l: ", l)
      print("d: ", d)
      if l:
        idx=int(l.group(1))
        o=o[idx]
      else:
        o=o[d.group(1)]
    print("o: ", o)
    
    
  def _rec_compl_build(self, o, s="", l=[]):
    """
    recursives bilden der completion liste 
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

    open  <file>              -> open json/yaml file
    print <e> .. <e>          -> print values of elements
    update <e> -k <key> -v <value>  -> combine element with {key: value}
    set <e> -v <value>           -> set value
    

  """

  def __init__(self):
    super().__init__()
    self.prompt="> "
    #self.complete_open=self.path_complete
    self.jsw=None

  #def do_show

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
          self.poutput("arg: %s erg: %s" % (e, self.jsw.get_value(e)))
    else:
      self.pwarning("bitte erstmal eine datei öffnen")

  def complete_print(self, text, line, begidx, endidx):
    """ completion für print """
    if self.jsw:
      cl=self.jsw.cl
    else:
      cl=[]
    return self.delimiter_complete(text, line, begidx, endidx, match_against=cl, delimiter=":")

  def do_pager_jsw(self, s):
    """ zeige geladenes json """
    self.poutput(JsonWalk.dumps(self.jsw.js), paged=True)


if __name__ == '__main__':
  c = App()
  sys.exit(c.cmdloop())
