#!/usr/bin/env python3

"""
A simple cmd2 application.
{
    "a": [
        "l1",
        "l2"
    ],
    "b": "s1",
    "c": {
        "o1": "v1",
        "o2": "v2"
    },
    "d": "s2"
}

[ {"a":"b"}, 23 , ["g", "d"]]

"""
import sys
import os
import json
import cmd2
import jmespath

class JsonWalk:
  """ spaziergang durch json objekte """
  def __init__(self, js):
    self.js=js
    self.pwd=""
    self.pwd_obj=js
    
  def build_completion_list(self):
    """ bildet completion liste vom gesamten js objekt 
    ['a[0]', 'a[1]', "b", "c", "c.o1", "c.o2", d]
  
    """
    return self.rec

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

  ############# open ##########################
  def do_jopen(self, s):
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
      
  def complete_jopen(self, text, line, begidx, endidx):
    """path completion für open"""
    return self.path_complete(text, line, begidx, endidx)

  ##################### print #####################
  def do_jprint(self, s):
    """ zeige geladenes json """
    self.poutput(JsonWalk.dumps(self.jsw.js))

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
