#!/usr/bin/env python3
import sys
import re
import os
import yaml
import cmd2
from obed.objwalk import ObjWalk
from obed.utils import obj_dumps, convert_to_json, load_json, dump_json, dump_yaml
from obed.argparsers import ObedArgParsers
from obed.decors import *
from obed.secrets import ObedVault
from obed.yavault import get_loader,VaultData

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
    self.obj_type=None

  def _reset(self):
    """ reset after closing object
    """ 
    self.obj_hist.clear()
    self.wrk_file=None
    self.obj=None
    self.changed=False
    self.obj_type=None  
    

  def hist_choice_provider(self):
    """ showhist choice provider
    used for tab completion
    return numbers of object history array
    """
    l=len(self.obj_hist)
    return [str(x) for x in range(l)]

  def object_choice_provider(self):
    """ returns elements path of object
    """
    return self.compl_list

  def warn(self, warn_msg=""):
    """ wrapper for pwarning function of cmd2
    """
    self.pwarning(warn_msg)

  ############# version ##########################
  def do_version(self, _):
    """ show version of obed package
    usage:
      version
    """
    from importlib.metadata import version
    self.poutput(version('obed'))


  ############# new ##########################
  @cmd2.with_argument_list
  @close_at_first
  def do_new(self, args):
    """  create new json object 
    usage:
      new               - new empty '{}' json object
      new [json_string] - new json object from string
    """
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
      self.obj_type="json"
      self.obj=js
      self.changed=True
      #self.psuccess("json loaded")
   
 
  ############# new yaml ##########################
  @cmd2.with_argument_list
  @close_at_first
  def do_new_yaml(self, args):
    """  create new yaml object 
    usage:
      new               - new empty '{}' yaml object
      new [json_string] - new yaml object from string
    """
    y={}
    if len(args) > 1:
      self.pwarning("loading only first arg. other args will be ignored")
    try:
      if args:
        y=yaml.load(args[0], Loader=get_loader())
    except Exception as _exc:
      self.perror("not possible to load argument as yaml obj: %s" % _exc)
    else:
      #self.wrk_file=s
      self.obj_type="yaml"
      self.obj=y
      self.changed=True
      #self.psuccess("json geladen")
    

  ############# open ##########################
  @close_at_first
  def do_open(self, arg):
    """ load json from file
    usage:
      open file     - load file as json
    """
    #self.poutput("sim sim öffne %s ..." % s)
    try:
      js=load_json(arg)
    except Exception as _exc:
      self.perror("not possible to load json file: %s" % _exc)
    else:
      self.obj_type="json"
      self.wrk_file=arg
      self.obj=js
      #self.psuccess("json geladen")
      
  def complete_open(self, text, line, begidx, endidx):
    """path completion for open"""
    return self.path_complete(text, line, begidx, endidx)

  ############### save ########################
  @open_at_first
  def do_save(self, arg):
    """ save object as json to file 
    usage:
      save          - save object to loaded file 
      save [file]   - save object to file
    """
    if arg:
      self.poutput("saving obj as json to %s" % arg)
      dump_json(self.obj, arg)
    else:
      self.poutput("saving obj as json to loaded file")
      dump_json(self.obj, self.wrk_file)
    self.changed=False

  def complete_save(self, text, line, begidx, endidx):
    """path completion for save/write"""
    return self.path_complete(text, line, begidx, endidx)

  ##################### show hist ###################
  @cmd2.with_argument_list
  def do_showhist(self, args):
    """ show object history entries 
    usage:
      showhist              - show all object history entries
      showhist [nr [nr..]]  - show certain object history entries
    """
    if args:
      for c in args:
        self.poutput(cmd2.ansi.style("hist Nr. %s -> "%c, fg=cmd2.Fg["LIGHT_BLUE"] ))
        self.poutput("%s" % obj_dumps(self.obj_hist[int(c)], self.obj_type))
    else: 
      for c,e in enumerate(self.obj_hist):
        self.poutput(cmd2.ansi.style("hist Nr. %s -> "%c, fg=cmd2.Fg["LIGHT_BLUE"] ))
        self.poutput("%s" % obj_dumps(e, self.obj_type))

  def complete_showhist(self, text, line, begidx, endidx):
    """ completion for print 
    """
    return self.basic_complete(text, line, begidx, endidx, match_against=self.hist_choice_provider())

  ##################### close #####################
  @open_at_first
  def _close_with_deco(self, args):
    """ wrapper for close with decorator
    """
    self._close(args)

  def _close(self, args):
    """ close objects 
    """
    #if len(self.obj_hist):
    if self.changed and not args.no_save:
      i=self.read_input("save object before closing? ", 
                        completion_mode=cmd2.CompletionMode.CUSTOM, 
                        choices=["yes", "no"])
      if re.match("yes|ja|y|j", i, re.I):
        i=self.read_input("saving object to: ", 
                          completion_mode=cmd2.CompletionMode.CUSTOM, 
                          completer=cmd2.Cmd.path_complete)
        if self.obj_type=="yaml":
          self.do_save_yaml(i)
        else:
          self.do_save(i)
      elif re.match("no|nein|n", i, re.I):
        self.poutput("don't saving any changes")
      else:
        self.perror("ambiguously answer. please call close again")
        return 
    self._reset()

  @cmd2.with_argparser(ObedArgParsers.close_parser)
  def do_close(self, args):
    """ close objects 
    usage:
      close [-s]    - close with saving changes
      close -n      - close wthout saving
    """
    #self.poutput("close args %s" % args)
    self._close_with_deco( args)

  ##################### quit,exit #####################
  @cmd2.with_argparser(ObedArgParsers.close_parser)
  def do_quit(self, args):
    """ override built in quit command
    usage:
      quit [-s]     - exit. if you have unsaved changes, you will be asked to save it
      quit -n       - exit without saving changes
      quit -h       - print help for quit/exit command
    """
    self._close(args)
    return True

  do_exit=do_quit
    
  ##################### print #####################
  @cmd2.with_argument_list
  @open_at_first
  def do_print(self, args):
    """print object to stdout 
    usage:
      print                   - print whole object
      print [path [path ..]]  - print one or more object elements described by path
    """
    #self.poutput("print compl list: %s" % self.jsw.cl)
    if not args:
      self.poutput(obj_dumps(self.obj, self.obj_type))
    else:
      for e in args:
        #self.poutput("get_value %s : %s" % (e, self.get_value(e)))
        self.poutput(cmd2.ansi.style("%s -> "%e, fg=cmd2.Fg["LIGHT_BLUE"] ))
        self.poutput("%s" % obj_dumps(self.get_value(e), self.obj_type))

  def complete_print(self, text, line, begidx, endidx):
    """ completion for print """
    return self.delimiter_complete(text, line, begidx, endidx, match_against=self.compl_list, delimiter=":")


  ##################### delete #####################
  @cmd2.with_argument_list
  @open_at_first
  def do_delete(self, args):
    """ delete elements from object 
    usage:
      delete path [path ..]  - delete one or more object elements described by path
    """
    #self.poutput("print compl list: %s" % self.jsw.cl)
    if not args:
      self.pwarning("deleting whole object..")
      self.delete_element()
    else:
      for e in args:
        #self.poutput("deleting element %s" % e)
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
    """ set value of json  object element(s)
    usage:
      setval [path [path ...]] -v value     - set value of whole object, one or more elements desribed by path
      setval -h                             - show help for setval command
    """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    self._set_val(args)
  

  ###################### set_vault_val ########################
  @open_at_first
  def _set_val_vault(self, args):
    """ set value of object element """
    value=self.get_args_value(args)
    #value=args.value[0]
    for ele in args.elements:
      self.set_value_vault(ele,value,args.vault_id)
    self.obj_type="yaml"
    self.changed=True

  @cmd2.with_argparser(ObedArgParsers.set_vault_parser)
  def do_setval_vault(self, args):
    """ set value of object element as vault
    """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    self._set_val_vault(args)

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

  ###################### append vault to list ########################
  @open_at_first
  def _append_vault(self, args):
    """ append vault value of object element """
    #values=args.value
    values=self.get_args_values(args)
    if args.elements:
      for ele in args.elements:
        for value in values:
          self.append_value_vault(ele, value, args.vault_id)
    else:
      for value in values:
        self.append_value_vault("", value, args.vault_id)
    self.obj_type="yaml"
    self.changed=True
  
  @cmd2.with_argparser(ObedArgParsers.append_vault_parser)
  def do_append_vault(self, args):
    """ append vault value of object element """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    self._append_vault(args)

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


  ###################### vault ########################
  @cmd2.with_argparser(ObedArgParsers.vault_parser)
  def do_vault(self, args):
    """ handling of vault data
    """
    #self.poutput("vault args: %s" % (args))
    self.handle_vault_ids_args(args)
    if args.print is not None:
      self.vault_data_print(args.print)


  ###################### yaml ########################
  @close_at_first
  def _open_yaml(self, args):
    with open(args.yaml_file[0]) as f:
      y=yaml.load(f, Loader=get_loader())
    self.obj_type="yaml"
    self.wrk_file=args.yaml_file[0]
    self.obj=y

  @cmd2.with_argparser(ObedArgParsers.open_yaml_parser)
  def do_open_yaml(self, args):
    """ open yaml file
    """
    self._open_yaml(args)

  @open_at_first
  def do_save_yaml(self, arg):
    """ save yaml to file s
    if s is not provided or empty,none
    save to wrk_file """
    if arg:
      self.poutput("saving as yaml to %s" % arg)
      dump_yaml(self.obj, arg)
    else:
      self.poutput("saving as yaml to current working file")
      dump_yaml(self.obj, self.wrk_file)
    self.changed=False

  def complete_save_yaml(self, text, line, begidx, endidx):
    """path completion for save/write of yaml"""
    return self.path_complete(text, line, begidx, endidx)


def run():
  c = Obed()
  sys.exit(c.cmdloop())

if __name__ == '__main__':
  run()
