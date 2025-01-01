#!/usr/bin/env python
import cmd2

class ObedArgParser:

  def json_choice_provider(self):
    return self.cl

  test_parser=cmd2.Cmd2ArgumentParser()
  test_parser.add_argument('elements', 
                          help='json element(s). element should be list', 
                          nargs='*', 
                          choices_provider=json_choice_provider)
  test_parser.add_argument('-v', '--values', nargs='+', help='test value')

class App(cmd2.Cmd, ObedArgParser):

  def __init__(self):
    super().__init__()
    self.cl=["xyj", "wam", "a", "ne", "molodostj"]

  def json_choice_provider(self):
    return self.cl

  @cmd2.with_argparser(ObedArgParser.test_parser)
  def do_test(self,  args):
    """ set value of json element """
    self.poutput("setting %s to %s" % (args.elements, args.values[0]))

if __name__ == '__main__':
  c=App()
  c.cmdloop()
