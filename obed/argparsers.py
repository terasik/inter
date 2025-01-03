import cmd2

class ObedArgParsers:

  def json_choice_provider(self):
    return self.compl_list

  set_parser=cmd2.Cmd2ArgumentParser()
  set_parser.add_argument('elements', help='json element(s)', nargs='*', choices_provider=json_choice_provider)
  set_parser.add_argument('-v', '--value', nargs=1, help='value of json element')

  append_parser=cmd2.Cmd2ArgumentParser()
  append_parser.add_argument('elements', help='json element(s). element should be list', nargs='*', choices_provider=json_choice_provider)
  append_parser.add_argument('-v', '--values', nargs='+', help='append value')
