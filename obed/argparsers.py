import functools
import cmd2
from obed.secrets import vault_id_rgx

class ObedArgParsers:
  """ argparsers for a lot of obed cmds:
  """

  def get_args_value(self, args, idx=0):
    """ get value from argparser args """
    if args.value:
      return args.value[idx]
    if args.take_from:
      return self.get_value(args.take_from[idx])
    self.perror("something wrong with your command args...")

  def get_args_values(self, args):
    """ get value from argparser args """
    if args.value:
      return args.value
    if args.take_from:
      return [self.get_value(x) for x in args.take_from]
    self.perror("something wrong with your command args...")

  def get_args_values_len(self, args):
    if args.value:
      return len(args.value)
    if args.take_from:
      return len(args.take_from)
    self.perror("something wrong with your command args...")
      
  def object_choice_provider(self):
    """ return list with all obj elements
    """
    return self.compl_list

  def vault_choice_provider(self):
    """ return list with known vault ids
    """
    return [k for k,v in self.vault_data.items()]

  def hist_choice_provider(self):
    """ showhist,restore choice provider
    used for tab completion
    return numbers of object history array
    negativ list: list(range(-len(a), 0, 1))
    """
    l=len(self.obj_hist)
    return [str(i) for i in list(range(-l, l, 1))]

  def my_delimiter_completer(self, text, line, begidx, endidx):
    """ completion für print """
    return self.delimiter_complete(text, line, begidx, endidx, match_against=self.compl_list, delimiter=":")

  # setval cmd parser
  set_parser=cmd2.Cmd2ArgumentParser()
  set_group=set_parser.add_mutually_exclusive_group(required=True)
  set_parser.add_argument('elements', 
                          help='object element(s) which will be set', 
                          nargs='*', 
                          choices_provider=object_choice_provider)
  set_group.add_argument('-v', '--value', 
                          nargs=1, 
                          help='value of object element')
  set_group.add_argument('-t', '--take-from', 
                          nargs=1, 
                          help='take value from another object element', 
                          choices_provider=object_choice_provider)

  # delete cmd parser
  delete_parser=cmd2.Cmd2ArgumentParser()
  delete_parser.add_argument('elements', 
                            help='object element(s) which will be deleted', 
                            nargs='*', 
                            completer=my_delimiter_completer)

  # new cmd parser
  new_parser=cmd2.Cmd2ArgumentParser()
  new_group=new_parser.add_mutually_exclusive_group(required=True)
  new_parser.add_argument('obj_str', 
                          help='object string', 
                          nargs=(0,1))
  new_group.add_argument('-y', '--yaml',
                          help='new yaml object',
                          action='store_true')
  new_group.add_argument('-j', '--json',
                          help='new json object',
                          action='store_true')

  # setval_vault cmd parser
  set_vault_parser=cmd2.Cmd2ArgumentParser()
  set_vault_group=set_vault_parser.add_mutually_exclusive_group(required=True)
  set_vault_parser.add_argument('elements', 
                                help='object element(s) which will be set', 
                                nargs='+', 
                                choices_provider=object_choice_provider)
  set_vault_group.add_argument('-v', '--value', 
                                nargs=1, 
                                help='value of object element')
  set_vault_group.add_argument('-t', '--take-from', 
                                nargs=1, 
                                help='take value from another object element', 
                                choices_provider=object_choice_provider)
  set_vault_parser.add_argument('-i', '--vault-id', 
                                nargs='*', 
                                help='value will be encrypted with vault id', 
                                choices_provider=vault_choice_provider)

  # append cmd parser
  append_parser=cmd2.Cmd2ArgumentParser()
  append_parser.add_argument('elements', 
                              help='object element(s). element should be list', 
                              nargs='*', 
                              choices_provider=object_choice_provider)
  append_group=append_parser.add_mutually_exclusive_group(required=True)
  append_group.add_argument('-v', '--value', 
                            nargs='+', 
                            help='append this value to object lists')
  append_group.add_argument('-t', '--take-from', 
                            nargs='+', 
                            help='take append values from another elements', 
                            choices_provider=object_choice_provider)

  # append_vault cmd parser
  append_vault_parser=cmd2.Cmd2ArgumentParser()
  append_vault_group=append_vault_parser.add_mutually_exclusive_group(required=True)
  append_vault_parser.add_argument('elements', 
                                    help='object element(s). element should be list', 
                                    nargs='*', 
                                    choices_provider=object_choice_provider)
  append_vault_group.add_argument('-v', '--value', 
                                  nargs='+', 
                                  help='append this value to object lists')
  append_vault_group.add_argument('-t', '--take-from', 
                                  nargs='+', 
                                  help='take append values from another elements', 
                                  choices_provider=object_choice_provider)
  append_vault_parser.add_argument('-i', '--vault-id', 
                                    nargs='*', 
                                    help='value will be encrypted with vault id', 
                                    choices_provider=vault_choice_provider)


  # copy cmd parser
  copy_parser=cmd2.Cmd2ArgumentParser()
  copy_parser.add_argument('elements', 
                            help='object element(s)', 
                            nargs='+', 
                            choices_provider=object_choice_provider)
  copy_parser.add_argument('-d', '--dest', 
                            nargs='*', 
                            help='destionations where elements should be copied', 
                            choices_provider=object_choice_provider)

  # close parser
  close_parser=cmd2.Cmd2ArgumentParser()
  close_group=close_parser.add_mutually_exclusive_group()
  close_group.add_argument('-s', '--save', 
                            help='save before close', 
                            action='store_true')
  close_group.add_argument('-n', '--no-save', 
                            help='dont save before closing', 
                            action='store_true')


  # open file parser
  open_parser=cmd2.Cmd2ArgumentParser()
  open_parser.add_argument('file',
                          help='file to load',
                          nargs=1,
                          completer=cmd2.Cmd.path_complete)


  # save parser
  save_parser=cmd2.Cmd2ArgumentParser()
  save_parser.add_argument('file',
                          help='save object to file.',
                          nargs='*',
                          completer=cmd2.Cmd.path_complete)
  save_parser.add_argument('-t', '--type',
                          help='type of saved object [json, yaml]',
                          choices=['json', 'yaml'])


  # vault parser
  vault_parser=cmd2.Cmd2ArgumentParser()
  vault_group=vault_parser.add_mutually_exclusive_group()
  vault_parser.add_argument('vault_ids',
                          help='vault ids. should match this regex %s' % vault_id_rgx,
                          nargs='*',
                          choices_provider=vault_choice_provider)
  vault_parser.add_argument('-p', '--print',
                          help='print vault ids and passwords',
                          nargs='*',
                          choices_provider=vault_choice_provider)
  vault_group.add_argument('-r', '--read',
                          help='read vault ids and passwds from stdin',
                          action='store_true')
  vault_group.add_argument('-l', '--load-file',
                          help='read vault ids aand passwds from file. file format: vault-id=password',
                          nargs=1,
                          completer=cmd2.Cmd.path_complete)


  # completion test parser
  compl_test_parser=cmd2.Cmd2ArgumentParser()
  compl_test_parser.add_argument('-c', '--choice',
                          help='completion test with choice provider',
                          nargs='+',
                          choices_provider=object_choice_provider)
  compl_test_parser.add_argument('-d', '--delimiter',
                          help='completion test with delimiter completer',
                          nargs='+',
                          completer=my_delimiter_completer)

  # restore command parser
  restore_parser=cmd2.Cmd2ArgumentParser()
  restore_parser.add_argument('hist_idx',
                              help="history index (integer)",
                              nargs=(0,1),
                              default="-1",
                              type=int,
                              choices_provider=hist_choice_provider)
                              
  # genpasswd command parser
  gensec_parser=cmd2.Cmd2ArgumentParser()
  gensec_group=gensec_parser.add_mutually_exclusive_group()
  gensec_parser.add_argument('-c', '--count',
                              help="count of generated secrets",
                              type=int,
                              default=1,
                              choices=range(1,10))
  gensec_group.add_argument('-l', '--length',
                                help="length of password",
                                type=int,
                                default=17,
                                choices=range(1,50))
  gensec_group.add_argument('-t', '--token',
                            help="generate url safe token",
                            action="store_true")

