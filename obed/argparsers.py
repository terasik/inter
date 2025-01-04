import cmd2

class ObedArgParsers:

  def object_choice_provider(self):
    return self.compl_list

  set_parser=cmd2.Cmd2ArgumentParser()
  set_parser.add_argument('elements', help='object element(s) which will be set', nargs='*', choices_provider=object_choice_provider)
  set_parser.add_argument('-v', '--value', nargs=1, help='value of object element')

  append_parser=cmd2.Cmd2ArgumentParser()
  append_parser.add_argument('elements', help='object element(s). element should be list', nargs='*', choices_provider=object_choice_provider)
  append_parser.add_argument('-v', '--values', nargs='+', help='append value')

  copy_parser=cmd2.Cmd2ArgumentParser()
  copy_parser.add_argument('elements', help='object element(s)', nargs='+', choices_provider=object_choice_provider)
  copy_parser.add_argument('-d', '--dest', nargs='*', help='destionations where elements should be copied', choices_provider=object_choice_provider)
