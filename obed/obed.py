#!/usr/bin/env python3
import sys
import re
import os
import yaml
import cmd2
from obed.objwalk import ObjWalk
from obed.utils import obj_dumps, convert_to_json, load_json, dump_json
from obed.argparsers import ObedArgParsers
from obed.decors import *
from obed.secrets import ObedVault
from obed.yavault import get_loader,get_dumper,VaultData

class Obed(ObjWalk, ObedArgParsers, ObedVault):

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
    self.vault_data=VaultData.vault_data
    self.yaml_json=None

  def _reset(self):
    self.obj_hist.clear()
    #self.hcl=[]
    self.wrk_file=None
    self.obj=None
    self.changed=False
    self.yaml_json=None  
    

  def hist_choice_provider(self):
    l=len(self.obj_hist)
    return [str(x) for x in range(l)]

  def object_choice_provider(self):
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
      self.yaml_json="json"
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
      self.yaml_json="json"
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
        self.poutput(cmd2.ansi.style("hist Nr. %s -> "%c, fg=cmd2.Fg["LIGHT_BLUE"] ))
        self.poutput("%s" % obj_dumps(self.obj_hist[int(c)]))
    else: 
      for c,e in enumerate(self.obj_hist):
        self.poutput(cmd2.ansi.style("hist Nr. %s -> "%c, fg=cmd2.Fg["LIGHT_BLUE"] ))
        self.poutput("%s" % obj_dumps(e))

  def complete_showhist(self, text, line, begidx, endidx):
    """ completion für print """
    return self.basic_complete(text, line, begidx, endidx, match_against=self.hist_choice_provider())

  ##################### close #####################
  @open_at_first
  def _close(self, args):
    """ close editing json objects """
    #if len(self.obj_hist):
    if self.changed and not args.no_save:
      i=self.read_input("save object before closing? ", 
                        completion_mode=cmd2.CompletionMode.CUSTOM, 
                        choices=["yes", "no"])
      if re.match("yes|ja|y|j", i, re.I):
        i=self.read_input("saving object to: ", 
                          completion_mode=cmd2.CompletionMode.CUSTOM, 
                          completer=cmd2.Cmd.path_complete)
        self.do_save(i)
      elif re.match("no|nein|n", i, re.I):
        self.poutput("don't saving any changes")
      else:
        self.perror("ambiguously answer. please call close again")
        return 
    self._reset()

  @cmd2.with_argparser(ObedArgParsers.close_parser)
  def do_close(self, args):
    """ close editing json objects """
    #self.poutput("close args %s" % args)
    self._close( args)

  ##################### print #####################
  @cmd2.with_argument_list
  @open_at_first
  def do_print(self, args):
    """ zeige geladenes json """
    #self.poutput("print compl list: %s" % self.jsw.cl)
    if not args:
      self.poutput(obj_dumps(self.obj, self.yaml_json))
    else:
      for e in args:
        self.poutput(cmd2.ansi.style("%s -> "%e, fg=cmd2.Fg["LIGHT_BLUE"] ))
        self.poutput("%s" % obj_dumps(self.get_value(e), self.yaml_json))

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
    

  @open_at_first
  def _set_val(self, args):
    """ set value of object element """
    value=self.get_args_value(args)
    if args.elements:
      for ele in args.elements:
        self.set_value(ele,value)
    else:
      self.set_value("", value)
    self.changed=True

  @cmd2.with_argparser(ObedArgParsers.set_parser)
  def do_setval(self, args):
    """ set value of object element """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    self._set_val(args)
  
  ###################### append to list ########################

  @open_at_first
  def _append(self, args):
    """ append value of object element """
    values=self.get_args_values(args)
    if args.elements:
      for ele in args.elements:
        for value in values:
          self.append_value(ele, value)
    else:
      for value in values:
        self.append_value("", value)
    self.changed=True
  
  @cmd2.with_argparser(ObedArgParsers.append_parser)
  def do_append(self, args):
    """ append value of object element """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    self._append(args)

  ###################### copy elements ########################

  @open_at_first
  def _copy(self, args):
    """ copy obj elements to other obj elements  """
    for ele in args.elements:
      for dest in args.dest:
        #self.poutput("copy element %s to dest %s" % (ele, dest))
        self.copy_element(ele, dest)
    self.changed=True

  @cmd2.with_argparser(ObedArgParsers.copy_parser)
  def do_copy(self, args):
    """ copy obj elements to other obj elements  """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    #if not args.dest:
    #  args.dest=[""]
    self._copy(args)

  ###################### copy elements ########################
  @close_at_first
  def _open_yaml(self, args):
    with open(args.yaml_file[0]) as f:
      y=yaml.load(f, Loader=get_loader())
    self.yaml_json="yaml"
    self.wrk_file=args.yaml_file[0]
    self.obj=y

    

  @cmd2.with_argparser(ObedArgParsers.open_yaml_parser)
  def do_open_yaml(self, args):
    """ open yaml file
    """
    self._open_yaml(args)


def run():
  c = Obed()
  sys.exit(c.cmdloop())

if __name__ == '__main__':
  run()
