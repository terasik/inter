import functools
import cmd2
from obed.secrets import vault_id_rgx
from obed.defs import DEF_PASSWD_LEN, MAX_PASSWD_LEN

class ValArgParser(cmd2.Cmd2ArgumentParser):
    def __init__(self, obj_choices_provider, vault_choices_provider=None, need_mut_exc_gr=True):
        super().__init__()
        self.obj_choices_provider=obj_choices_provider
        self.vault_choices_provider=vault_choices_provider
        # TODO handling for delete parser
        if need_mut_exc_gr:
            self.mut_exc_group=self.add_mutually_exclusive_group(required=True) 
        #self.add_gen_value_arg()
        
    def add_elements_arg(self, choices_provider=None):
        if choices_provider is None:
            choices_provider=self.obj_choices_provider
        self.add_argument('elements', 
                            help='object element(s)',
                            nargs='*',
                            choices_provider=choices_provider)

    def add_value_arg(self, nargs=1, help_s="new value(s) of object element(s)"):
        self.mut_exc_group.add_argument('-v', '--value', 
                        nargs=nargs,
                        help=help_s)
    
    def add_take_from_arg(self, nargs=1, 
                            help_s="value(s) of existing elements used for new values",
                            choices_provider=None):
        if choices_provider is None:
            choices_provider=self.obj_choices_provider
        self.mut_exc_group.add_argument('-t', '--take-from', 
                            help=help_s,
                            nargs=nargs,
                            choices_provider=choices_provider)

    def add_vault_id_arg(self):
        self.add_argument('-i', '--vault-id', 
                            help='vault id used to encrypt values', 
                            choices_provider=self.vault_choices_provider)


class ObedArgParsers:
    """ argparsers for a lot of obed cmds:
    """

    def get_args_value(self, args, idx=0):
        """ get value from argparser args """
        if args.value:
            return args.value[idx]
        if args.take_from:
            return self.get_value(args.take_from[idx])
        self.perror("something wrong with your command args...", vault_choice_provide)

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
    setval_parser=ValArgParser(object_choice_provider)
    setval_parser.add_elements_arg()
    setval_parser.add_value_arg()
    setval_parser.add_take_from_arg()

    # delete cmd parser
    delete_parser=ValArgParser(object_choice_provider, None, False)
    delete_parser.add_elements_arg()

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
    setval_vault_parser=ValArgParser(object_choice_provider, vault_choice_provider)
    setval_vault_parser.add_elements_arg()
    setval_vault_parser.add_value_arg()
    setval_vault_parser.add_take_from_arg()
    setval_vault_parser.add_vault_id_arg()
    

    # append cmd parser
    append_parser=ValArgParser(object_choice_provider)
    append_parser.add_elements_arg(object_choice_provider)
    append_parser.add_value_arg('+')
    append_parser.add_take_from_arg('+')

    # append_vault cmd parser
    append_vault_parser=ValArgParser(object_choice_provider, vault_choice_provider)
    append_vault_parser.add_elements_arg(object_choice_provider)
    append_vault_parser.add_value_arg('+')
    append_vault_parser.add_take_from_arg('+')
    append_vault_parser.add_vault_id_arg()


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
    #vault_parser.add_argument('-p', '--print',
    vault_group.add_argument('-p', '--print',
                          help='print vault ids and passwords',
                          #nargs='*',
                          action='store_true')
                          #choices_provider=vault_choice_provider)
    vault_group.add_argument('-d', '--delete',
                          help='delete vault id(s)',
                          #nargs='+',
                          action='store_true') 
                          #choices_provider=vault_choice_provider)
    vault_group.add_argument('-r', '--read',
                          help='read vault ids and passwds from stdin',
                          action='store_true')
    vault_group.add_argument('-l', '--load-file',
                          help='read vault ids and passwds from file. file format: vault-id=password',
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
                                default=DEF_PASSWD_LEN,
                                choices=range(1, MAX_PASSWD_LEN))
    gensec_group.add_argument('-t', '--token',
                            help="generate url safe token",
                            action="store_true")

