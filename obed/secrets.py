"""
handle vault commands

vault -r, --read [file]     -> read vault-ids/passwords from stdin or password
vault -p, --print           -> show password
vault -s, --set             -> set/change existing passwords
vault -h, --help            -> show help
vault-id [id, [id]]         -> set vault ids 
                                if no posit. args show vault ids only 
vault-id -m OLD NEW         -> change name of vault id
"""


import logging
import re
from getpass import getpass
import cmd2

vault_id_regex=r'[a-zA-Z_0-9]+'

class ObedVault():
  """ vault password """
  
  def vault_choice_provider(self):
    return [k for k,v in self.vault_data.items()]

  vault_parser=cmd2.Cmd2ArgumentParser()
  vault_group=vault_parser.add_mutually_exclusive_group()
  vault_parser.add_argument('vault_ids', 
                          help='vault ids. should match this regex [a-zA-Z_0-9]+', 
                          nargs='*')
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

  def vault_id_print(self, vault_ids=[]):
    """ print vault ids
    if no vault_ids provided print 
    everything
    """
    if vault_ids:
      for vid in vault_ids:
        self.poutput("vault_id=%s, password=%s" % (vid, self.vault_data[vid]))
    else:
      for vid,pwd self.vault_data.items():
        self.poutput("vault_id=%s, password=%s" % (vid,pwd))

  def ask_vault_id_passwd(self, vault_id, try_cnt=3):
    """ function that read vault_id from stdin
    """
    for _ in range(try_cnt):
      p=getpass("password for vault_id=%s: " % vault_id):
      p=p.strip()
      if not p:
        self.pwarning("invalid or empty password")
        continue
      return p
    raise ValueError("invalid or empty password provided")
      
    

  def vault_id_read(self, args):
    """ read passwords from stdin
    if no vault_ids provided ask also for vault_id names
    """
    # if vault_ids was provided
    if args.vault_ids:
      for vid in args.vault_ids:
        # if vvault id already exists in vault_data
        if vid in self.vault_choice_provider():
          # if vault_id already exists and has passwd
          if self.vault_data[vid]:
            self.poutput("vault_id=%s alread exists with password=%s" % (vid, self.vault_data[vid]))
            i=self.read_input("change password for vault_id=%s? " % vid,
                              completion_mode=cmd2.CompletionMode.CUSTOM,
                              choices=["yes", "no"])
            if re.match("yes|ja|y|j", i, re.I): 
              self.vault_data[vid]=self.ask_vault_id_passwd(vid)
          # vault_id exists but without password
          else:
            self.poutput("vault_id=%s already exists, but without password" % (vid, self.vault_data[vid]))
            self.vault_data[vid]=self.ask_vault_id_passwd(vid)
            
              
              
            

  def handle_vault_ids(self, args):
    """ get vault ids from args (argpraser)
    if -r option is provided read password from stdin
    if -l option provided load file
    if no of both options, set only vault_ids
    """
    if args.read:
      self.vault_id_read(args)


  @cmd2.with_argparser(vault_parser)
  def do_vault(self, args):
    """ handling of vault data
    """
    self.poutput("vault args: %s" % (args))
    
    

  

  

