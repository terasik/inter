
#!/usr/bin/env python3
import sys
import re
import os
import cmd2
from obed.objwalk import ObjWalk
from obed.utils import obj_dumps, convert_to_json, load_json, dump_json
from obed.argparsers import ObedArgParsers
from obed.decors import *

class Obed(ObjWalk, ObedArgParsers):

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
    self.wrk_file=None
    self.changed=False

  def _reset(self):
    self.obj_hist.clear()
    #self.hcl=[]
    self.wrk_file=None
    self.obj=None
    self.changed=False

  def hist_choice_provider(self):
    l=len(self.obj_hist)
    return [str(x) for x in range(l)]

  def json_choice_provider(self):
    return self.compl_list

  def warn(self, warn_msg=""):
    self.pwarning(warn_msg)


  ############# new ##########################
  @cmd2.with_argument_list
  @close_at_first
  def do_new(self, args):
    """  create new object """
    js={}
    if len(args) > 1:
      self.pwarning("loading only first arg. other args will be ignored")
    try:
      if args:
        js=convert_to_json(args[0], True, True)
    except Exception as _exc:
      self.perror("not possible to load argument as json obj: %s" % _exc)
    else:
      #self.wrk_file=s
      self.obj=js
      self.changed=True
      #self.psuccess("json geladen")
    
  ############# open ##########################
  @close_at_first
  def do_open(self, arg):
    """ öffnet json/yaml datei
    usage:
      open <file>
    """
    #self.poutput("sim sim öffne %s ..." % s)
    try:
      js=load_json(arg)
    except Exception as _exc:
      self.perror("not possible to load json file: %s" % _exc)
    else:
      self.wrk_file=arg
      self.obj=js
      #self.psuccess("json geladen")
      
  def complete_open(self, text, line, begidx, endidx):
    """path completion für open"""
    return self.path_complete(text, line, begidx, endidx)

  ############### save ########################
  @open_at_first
  def do_save(self, arg):
    """ save to file s
    if s is not provided or empty,none
    save to wrk_file """
    if arg:
      self.poutput("saving to %s" % arg)
      dump_json(self.obj, arg)
    else:
      self.poutput("saving to current working file")
      dump_json(self.obj, self.wrk_file)
    self.changed=False

  def complete_save(self, text, line, begidx, endidx):
    """path completion for save/write"""
    return self.path_complete(text, line, begidx, endidx)

  ##################### show hist ###################
  @cmd2.with_argument_list
  def do_showhist(self, args):
    """ show hist entries """
    if args:
      for c in args:
        self.poutput("hist Nr. %s:\n%s" % (c, obj_dumps(self.obj_hist[int(c)])))
    else: 
      for c,e in enumerate(self.obj_hist):
        self.poutput("hist Nr. %s:\n%s" % (c, obj_dumps(e)))

  def complete_showhist(self, text, line, begidx, endidx):
    """ completion für print """
    return self.basic_complete(text, line, begidx, endidx, match_against=self.hist_choice_provider())

  ##################### close #####################
  @open_at_first
  def do_close(self, arg):
    """ close editing json objects """
    #if len(self.obj_hist):
    if self.changed:
      i=self.read_input("save object before closing? ", 
                        completion_mode=cmd2.CompletionMode.CUSTOM, 
                        choices=["yes", "no"])
      if re.match("yes|ja|y|j", i, re.I):
        i=self.read_input("saving object to: ", 
                          completion_mode=cmd2.CompletionMode.CUSTOM, 
                          completer=cmd2.Cmd.path_complete)
        self.do_save(i)
    self._reset()

  ##################### print #####################
  @cmd2.with_argument_list
  @open_at_first
  def do_print(self, args):
    """ zeige geladenes json """
    #self.poutput("print compl list: %s" % self.jsw.cl)
    if not args:
      self.poutput(obj_dumps(self.obj))
    else:
      for e in args:
        self.poutput("%s -> \n%s" % (e, obj_dumps(self.get_value(e))))

  def complete_print(self, text, line, begidx, endidx):
    """ completion für print """
    return self.delimiter_complete(text, line, begidx, endidx, match_against=self.compl_list, delimiter=":")

  ##################### delete #####################
  @cmd2.with_argument_list
  @open_at_first
  def do_delete(self, args):
    """ delete elements fromd object """
    #self.poutput("print compl list: %s" % self.jsw.cl)
    if not args:
      self.pwarning("deleting whole object..")
      self.delete_element()
    else:
      for e in args:
        self.poutput("deleting element %s" % e)
        self.delete_element(e)
    self.changed=True
    
  def complete_delete(self, text, line, begidx, endidx):
    """ completion für print """
    return self.delimiter_complete(text, line, begidx, endidx, match_against=self.compl_list, delimiter=":")

  ###################### set_val ########################
  
  @cmd2.with_argparser(ObedArgParsers.set_parser)
  @open_at_first
  def do_set_val(self, args):
    """ set value of json element """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    if args.elements:
      for e in args.elements:
        self.poutput("setting element %s to %s" % (e, args.value[0]))
        self.set_value(e,args.value[0])
    else:
      self.poutput("setting whole object to %s" % (args.value[0]))
      self.set_value("", args.value[0])
    self.changed=True
  
  ###################### append to list ########################
  
  @cmd2.with_argparser(ObedArgParsers.append_parser)
  @open_at_first
  def do_append(self, args):
    """ set value of json element """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    if args.elements:
      for ele in args.elements:
        for value in args.values:
          self.poutput("append %s to element %s" % (value, ele))
          self.append_value(ele, value)
    else:
      for value in args.values:
        self.poutput("append %s to whole object" % (value))
        self.append_value("", value)
    self.changed=True




def run():
  c = Obed()
  sys.exit(c.cmdloop())

if __name__ == '__main__':
  run()
