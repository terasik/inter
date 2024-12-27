import cmd2

append_parser=cmd2.Cmd2ArgumentParser()
append_parser.add_argument('elements', help='json element(s). element should be list', nargs='*', choices_provider=json_choice_provider)
append_parser.add_argument('-v', '--values', nargs='+', help='append value')


@cmd2.with_argparser(append_parser)
def do_append(self, args):
  """ set value of json element """
  #self.poutput("setting %s to %s" % (args.elements, args.value[0]))
