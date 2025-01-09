import cmd2

class ObedArgParsers:
  """ argparsers for obed cmds:
    set_val, copy, close, append
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
    return self.compl_list

  # 
  set_parser=cmd2.Cmd2ArgumentParser()
  set_group=set_parser.add_mutually_exclusive_group(required=True)
  set_parser.add_argument('elements', help='object element(s) which will be set', nargs='*', choices_provider=object_choice_provider)
  set_group.add_argument('-v', '--value', nargs=1, help='value of object element')
  set_group.add_argument('-t', '--take-from', nargs=1, help='take value from another object element', choices_provider=object_choice_provider)

  #
  append_parser=cmd2.Cmd2ArgumentParser()
  append_parser.add_argument('elements', help='object element(s). element should be list', nargs='*', choices_provider=object_choice_provider)
  append_group=append_parser.add_mutually_exclusive_group(required=True)
  append_group.add_argument('-v', '--value', nargs='+', help='append this value to object lists')
  append_group.add_argument('-t', '--take-from', nargs='+', help='take append values from another elements', choices_provider=object_choice_provider)

  #
  copy_parser=cmd2.Cmd2ArgumentParser()
  copy_parser.add_argument('elements', help='object element(s)', nargs='+', choices_provider=object_choice_provider)
  copy_parser.add_argument('-d', '--dest', nargs='*', help='destionations where elements should be copied', choices_provider=object_choice_provider)

  #
  close_parser=cmd2.Cmd2ArgumentParser()
  close_group=close_parser.add_mutually_exclusive_group()
  close_group.add_argument('-s', '--save', help='save before close', action='store_true')
  close_group.add_argument('-n', '--no-save', help='dont save before closing', action='store_true')

