"""
handle vault commands

vault -r, --read [file]     -> read passwords from stdin or password
vault -p, --print           -> show password
vault -s, --set             -> set/change existing passwords
vault-id [id, [id]]         -> set vault ids 
                                if no posit. args show vault ids only 
vault-id -m OLD NEW         -> change name of vault id
"""


import logging
from getpass import getpass
import cmd2

class ObedVault():
  """ vault password """
  passwd={}
  vault_id=[]

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

