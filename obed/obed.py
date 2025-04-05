#!/usr/bin/env python3
"""
obed package file with Obed class. 
Obed class implements cmd2 commands to handle yaml or json objects.
to get help type after start of obed script:
> help
or
> help CMD
or (for the most commands)
> CMD --help
"""
import sys
import re
import os
from time import sleep
from copy import deepcopy
import yaml
import cmd2
from obed.objwalk import ObjWalk
from obed.utils import *
from obed.argparsers import ObedArgParsers
from obed.decors import *
from obed.secrets import ObedVault
from obed.yavault import VaultData, get_loader

class Obed(ObjWalk, ObedArgParsers, ObedVault):

  """ Obed class inherits from
  ObjWalk - with methods from cmd2.Cmd class and functions
            to handle with obj tabcompletion and values
  ObedArgParsers - class with cmd2.Cmd2ArgumentParser definitions
            for a lot of implemented commands
  ObedVault - class to handle ansible vault data and vault command 
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
    
#  def hist_choice_provider(self):
#    """ showhist choice provider
#    used for tab completion
#    return numbers of object history array
#    """
#    l=len(self.obj_hist)
#    return [str(x) for x in range(l)]

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
  @close_at_first
  def _new(self, args):
    obj={}
    if args.json:
      if args.obj_str:
        obj=convert_to_json(args.obj_str, True, True)
      self.obj_type="json"
    elif args.yaml:
      if args.obj_str:
        obj=yaml.load(args.obj_str, Loader=get_loader())
      self.obj_type="yaml"
    else:
      self.pwarning("no info about obj type. setting new obj to json: {}")
      self.obj_type="json"
    self.obj=obj
    self.changed=True
    
  @cmd2.with_argparser(ObedArgParsers.new_parser)
  def do_new(self, args):
    """  create new  object 
    usage:
      new                     - new empty '{}' json object
      new -j [object_string]  - new json object from string. defaults to {}
      new -y [object_string]  - new yaml object from string. defaults to {}
    example:
      new -j '{"a": [1, 2, "c"]}' - creating new dict json object
    """
    self._new(args)


  ############# open ##########################
  @close_at_first
  def _open(self, args):
    try:
      obj=load_json(args.file[0])
      self.psuccess("loaded file as json")
      self.obj_type="json"
    except:
      try:
        obj=load_yaml(args.file[0])
        if not isinstance(obj, (dict,list)):
          raise TypeError("yaml loaded object is not instance of list or dict")
        self.obj_type="yaml"
        self.psuccess("loaded file as yaml")
      except:
        raise TypeError("neither json nor yaml loaders has worked to open file: %s" % args.file[0])
    self.wrk_file=args.file[0]
    self.obj=obj
  
  @cmd2.with_argparser(ObedArgParsers.open_parser)
  def do_open(self, args):
    """ load json/yaml from file
    usage:
      open file     - load file as json
    """
    self._open(args)

  do_load=do_open

      
  ############### save ########################
  @open_at_first
  def _save(self, args):
    """ save objects to files """
    if not self.wrk_file and not args.file:
      self.perror("please provide file name to save object")
      return
    if self.wrk_file and not args.file:
      #self.poutput("save object to current opened file: %s" % self.wrk_file)
      file_to_write=self.wrk_file
    else:
      #self.poutput("save object to file: %s" % args.file[0])
      file_to_write=args.file[0]
    if args.type=="json" or (not args.type and self.obj_type=="json"):
      self.poutput("saving object as json to %s" % file_to_write)
      dump_json(self.obj, file_to_write)
    elif args.type=="yaml" or (not args.type and self.obj_type=="yaml"):
      self.poutput("saving object as yaml to %s" % file_to_write)
      dump_yaml(self.obj, file_to_write)
    else:
      self.perror("which type of object i should use to save this object...")
      return 
    self.changed=False
      
  @cmd2.with_argparser(ObedArgParsers.save_parser)
  def do_save(self, args):
    """ save object to file
    usage:
      save                              - save object to loaded/opened filed
      save [file] [-t json] [-t yaml]   - save object to file as yaml or json

    notice:
      if no '-t' option provided, self detected object type will be used
    """
    #print("save args: %s" % args)
    self._save(args)


  ##################### show hist ###################
  @cmd2.with_argument_list
  def do_showhist(self, args):
    """ show object history entries 
    usage:
      showhist              - show all object history entries
      showhist [nr [nr..]]  - show certain object history entries
                              examples for nr:
                                0 -> first change
                                1 -> second change
                               -1 -> last change
                               -2 -> last-1 change
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
  @open_at_first
  def _delete(self, args):
    """ delete elements from object 
    usage:
      delete path [path ..]  - delete one or more object elements described by path
    """
    if not args.elements:
      self.pwarning("deleting whole object..")
      self.delete_element()
    else:
      for e in args.elements:
        #self.poutput("deleting element %s" % e)
        self.delete_element(e)
    self.changed=True
  
  @cmd2.with_argparser(ObedArgParsers.delete_parser)
  def do_delete(self, args):
    self._delete(args)

    
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


  ################### compl test #######################
  @cmd2.with_argparser(ObedArgParsers.compl_test_parser)
  def do_compl_test(self, args):
    """ element completion test
    usage:
      compl_test -c ELEMENT [ELEMENT .. ]   - completion with choice provider
      compl_test -d ELEMENT [ELEMENT .. ]   - completion with delimiter completer
    """
    self.poutput("compl test: %s" % (args))


  ################### wait,sleep #######################
  @cmd2.with_argument_list
  def do_wait(self, args):
    """ wait some seconds
    usage:
      wait [SECONDS]   - wait/sleep for SECONDS. if no SECONDS provided wait for 1s
    """
    if args:
      for arg in args:
        try:
          sec_to_sleep=int(arg)
          if sec_to_sleep < 1:
            sec_to_sleep=1
          elif sec_to_sleep > 10:
            sec_to_sleep=10
        except:
          self.pwarning("can't convert arg '%s' to int" % arg)
          sec_to_sleep=1
        sleep(sec_to_sleep)
    else:
      sleep(1)

  ######################### restore ######################
  @open_at_first
  def _restore(self, args):
    """ restor help function
    current object will be saved and after restore
    appended to object history
    """
    hist_idx=args.hist_idx
    self.poutput("restoring obj from hist nr. %s" % hist_idx)
    curr_obj=deepcopy(self.obj)
    self.obj=deepcopy(self.obj_hist[hist_idx])
    self.obj_hist.append(curr_obj)
    self.changed=True

  @cmd2.with_argparser(ObedArgParsers.restore_parser)
  def do_restore(self, args):
    """ restore object from object hist
    usage:
      restore [history_index]  -  restore object from history with history_index
                                  default history_index=-1 (last change)
                                  examples for history_index:
                                     0  -> first change
                                     1  -> second change
                                    -1  -> last change
                                    -2  -> last-1 change
    """
    self._restore(args)


  ######################### gen secret ######################
  @cmd2.with_argparser(ObedArgParsers.gensec_parser)
  def do_gensec(self, args):
    """ generate password, token
    usage:
      gensec            - generate one password with length=17
      gensec -l 25      - generate one password with length=25
      gensec -c 3       - generate 3 passwords
      gensec -t         - generate one url safe token
    """
    secs=gen_secrets(**vars(args))
    for c, v in enumerate(secs):
      self.poutput("%s: %s" % (c, v))
   
 
def run():
  """ enter the void """
  handle_examples()
  c = Obed()
  sys.exit(c.cmdloop())


if __name__ == '__main__':
  run()
