#!/usr/bin/env python3
import sys
import os
import json
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
    print(self.cl)

  def build_completion_list(self):
    """ bildet completion liste vom gesamten js objekt 
    ['a[0]', 'a[1]', "b", "c", "c:o1", "c:o2", d]
  
    """
    return self._rec_compl_build(self._js, "", [])

  def get_value(self, s=""):
    """ liefert objekt anhand des suchstrings 
    re.sub(r"(\[\d+\])|:", r"|\1", "a[2]:r:c[2]:t")
    [f'"{x}"' if not x.startswith('[') else x for x in 'a|[2]|r|c|[2]|[10]|t'.split('|') ]

    """
    if not s:
      return self._js
    s=re.sub(r"(\[\d+\])|:", r"|\1", s)
    s="|".join([f'"{x}"' if not x.startswith('[') else x for x in s.split('|') ])
    return s
    
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
  """A simple cmd2 application."""

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
    self.poutput("print compl list: %s" % self.jsw.cl)
    if self.jsw:
      self.poutput(JsonWalk.dumps(self.jsw.js))
    else:
      pass

  def complete_print(self, text, line, begidx, endidx):
    """ completion für print """
    return self.delimiter_complete(text, line, begidx, endidx, match_against=self.jsw.cl, delimiter=":")

  def do_pager_jsw(self, s):
    """ zeige geladenes json """
    self.poutput(JsonWalk.dumps(self.jsw.js), paged=True)

  ########### ctest fuktionen ################# 
  def do_ctest(self, s):
    """ completion test """
    self.poutput("completion test: %s" % s)

  def _complete_ctest(self, text, line, begidx, endidx):
    """ completion für ctest """
    return self.basic_complete(text, line, begidx, endidx, match_against=["gfr", "jhgvfd", "poki uz"])

  def complete_ctest(self, text, line, begidx, endidx):
    """ completion für ctest """
    #mal=['a[0]', 'a[1]', 'b', 'c.o1', 'c.o2', 'c.o3[0]', 'c.o3[1].r', 'c.o3[2]', 'd', 'e[0]', 'e[1].lo2', 'f.']
    mal=["aa.bbb.cc", "z\.t.bab", "zh.re"]
    return self.delimiter_complete(text, line, begidx, endidx, match_against=mal, delimiter=".")



if __name__ == '__main__':
  c = App()
  sys.exit(c.cmdloop())
