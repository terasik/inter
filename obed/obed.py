
#!/usr/bin/env python3
import sys
import os
import cmd2
from obed.objwalk import ObjWalk
from obed.utils import obj_dumps

class Obed(ObjWalk):

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

  def _reset(self):
    self.obj_hist.clear()
    self.jsw=None
    self.jcl=[]
    #self.hcl=[]
    self.wrk_file=None

  def hist_choice_provider(self):
    if self.jsw:
      l=len(self.obj_hist)
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
    if s:
       for c in s:
        self.poutput("hist Nr. %s:\n%s" % (c, obj_dumps(self.obj_hist[int(c)])))
    else: 
      for c,e in enumerate(self.obj_hist):
        self.poutput("hist Nr. %s:\n%s" % (c, obj_dumps(e)))

  def complete_showhist(self, text, line, begidx, endidx):
    """ completion für print """
    return self.basic_complete(text, line, begidx, endidx, match_against=self.hist_choice_provider())

  ##################### close #####################
  def do_close(self, s):
    """ close editing json objects """
    #if len(self.obj_hist):
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
  def do_print(self, s):
    """ zeige geladenes json """
    #self.poutput("print compl list: %s" % self.jsw.cl)
    if self.jsw:
      if not s:
        self.poutput(JsonWalk.dumps(self.jsw.js))
      else:
        for e in s:
          self.poutput("%s -> \n%s" % (e, JsonWalk.dumps(self.jsw.get_value(e))))
    else:
      self.pwarning("please open file at first")

  def complete_print(self, text, line, begidx, endidx):
    """ completion für print """
    return self.delimiter_complete(text, line, begidx, endidx, match_against=self.jcl, delimiter=":")

  ##################### delete #####################
  @cmd2.with_argument_list
  def do_delete(self, args):
    """ delete elements fromd object """
    #self.poutput("print compl list: %s" % self.jsw.cl)
    jcl=self.jcl  
    if self.jsw:
      if not args:
        self.pwarning("deleting whole object..")
        jcl=self.jsw.delete_element()
      else:
        for e in args:
          self.poutput("deleting element %s" % e)
          jcl=self.jsw.delete_element(e)
      self.jcl=jcl  
    else:
      self.pwarning("please open file at first")

  def complete_delete(self, text, line, begidx, endidx):
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
    jcl=self.jcl
    if args.elements:
      for e in args.elements:
        self.poutput("setting element %s to %s" % (e, args.value[0]))
        jcl=self.jsw.set_value(e,args.value[0])
    else:
      self.poutput("setting whole object to %s" % (args.value[0]))
      jcl=self.jsw.set_value("", args.value[0])
    self.jcl=jcl  
  
  ###################### append to list ########################
  append_parser=cmd2.Cmd2ArgumentParser()
  append_parser.add_argument('elements', help='json element(s). element should be list', nargs='*', choices_provider=json_choice_provider)
  append_parser.add_argument('-v', '--values', nargs='+', help='append value')

  
  @cmd2.with_argparser(append_parser)
  def do_append(self, args):
    """ set value of json element """
    #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
    jcl=self.jcl
    if args.elements:
      for ele in args.elements:
        for value in args.values:
          self.poutput("append %s to element %s" % (value, ele))
          jcl=self.jsw.append_value(ele, value)
    else:
      for value in args.values:
        self.poutput("append %s to whole object" % (value))
        jcl=self.jsw.append_value("", value)
    self.jcl=jcl  

if __name__ == '__main__':
  c = Obed()
  sys.exit(c.cmdloop())
