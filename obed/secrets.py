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
  vault_group.add_argument('-l', '-f', '--load-file', 
                          help='read vault ids aand passwds from file. file format: vault-id-1;passwort-1 ', 
                          nargs=1,
                          completer=cmd2.Cmd.path_complete)

  

  @classmethod
  def read_passwd(cls):
    """ setzt passwd variable in
    abhängigkeit von vault-ids """
    logging.debug("ermittelte vault-id liste aus hostvars: %s", cls.vault_id)
    try:
      logging.debug("versuche vault passwort datei zu laden")
      from .mysecret import vault_passwd
      cls.passwd=vault_passwd
    except:
      logging.debug("abfrage der vault passwörter startet")
      for _vault_id in cls.vault_id:
        p=getpass(f"vault password ({_vault_id}): ")
        cls.passwd.update({_vault_id:p})

  

  

