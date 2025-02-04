"""
modul for handling ansible vault yaml
"""

import yaml
import logging
from ansible_vault import Vault

class VaultError(Exception):
  """ Vault Error """

class VaultData:
  """ class for vault password data
  (vault_ids, passwords)
  """
  vault_data={}

class YamlVault:
  """ class für yaml vault tag """
  def __init__(self, **kwargs):
    self._passwd=VaultData.vault_data
    self._vault_id=None
    # first line split von cipher text
    self.flsp=None
    self._cipher_text=None
    self._plain_text=None
    self.cipher_text=kwargs.get("cipher_text", None)
    if not self.cipher_text:
      self.vault_id=kwargs.get("vault_id", None)
      self.plain_text=kwargs.get("plain_text", None)

  def __repr__(self):
    """ show cipher text if call repr() 
    for Yamlvault instances
    """
    return self.cipher_text

  def handle_vault_id(self, cipher_text):
    """ get vault id from cipher text 
    """
    flsp=cipher_text.splitlines()[0].split(";")
    self.flsp=flsp
    if len(flsp)==3:
      self._vault_id=None
    elif len(flsp)==4:
      self._vault_id=flsp[-1].strip()
    else:
      raise VaultError(f"vault format ist falsch (erste zeile): {flsp}")

  @property
  def vault_id(self):
    """ returns vault-id 
    """
    return self._vault_id

  @vault_id.setter
  def vault_id(self, vault_id):
    """ vault-id setter
    """
    self._vault_id=vault_id

  @property
  def cipher_text(self):
    """ returns cipher text 
    """
    return self._cipher_text

  @cipher_text.setter
  def cipher_text(self, cipher_text):
    """ cipher text setter 
    - determine vault-id
    - get plain text from cipher text
    """
    if cipher_text:
      cipher_text=cipher_text.strip()
      self.handle_vault_id(cipher_text)
      self._plain_text=self.decode(cipher_text)
      self._cipher_text=cipher_text

  @property
  def plain_text(self):
    """ returns plain text 
    """
    return self._plain_text

  @plain_text.setter
  def plain_text(self, plain_text):
    """ plain text setter 
    - raise error if no vault_id provided
    - get cipher text from plain text
    """
    if plain_text:
      if not self.vault_id:
        raise VaultError("vault-id nicht übergeben")
      self._vault_id=self.vault_id
      self._cipher_text=self.encode(plain_text)
      self._plain_text=plain_text

  def decode(self, cipher_text):
    """ decode cipher_text
    - try to decode with all possible passwords
    - raises VaultError if decode fails
    """
    for vault_id in self._passwd:
      vault=Vault(self._passwd[vault_id])
      try:
        dec_data=vault.load(cipher_text)
      except:
        continue
      else:
        self._vault_id=vault_id
        return dec_data
    raise VaultError("decryption with all possible secrets failed")

  def encode(self, plain_text):
    """ encode plain text
    - returns cipher text
    """
    vault=Vault(self._passwd[self._vault_id])
    return vault.dump_raw(plain_text)


def vault_constructor(loader, node):
  """ returns YamlVault instance while loading 
  yaml with !vault data 
  """
  #return f"_vault_ {loader.construct_scalar(node)}"
  return YamlVault(cipher_text=loader.construct_scalar(node))

def get_loader():
  """Add constructors to PyYAML loader.
  will be used with yaml.load() function
  """
  loader = yaml.SafeLoader
  loader.add_constructor("!vault", vault_constructor)
  return loader

def vault_plain_representer(dumper, vault):
  """ used to represent plain text vault data
  """
  return dumper.represent_scalar("!vault", vault.plain_text)

def vault_cipher_representer(dumper, vault):
  """ used to represent cipher text vault data
  """
  return dumper.represent_scalar("!vault", vault.cipher_text, style='|')

def get_plain_dumper():
  """ plain text dumper. will be used with 
  yaml.dump() function
  """
  safe_dumper=yaml.SafeDumper
  safe_dumper.add_representer(YamlVault, vault_plain_representer)
  return safe_dumper

def get_cipher_dumper():
  """ cipher text dumper. will be used with 
  yaml.dump() function
  """
  safe_dumper=yaml.SafeDumper
  safe_dumper.add_representer(YamlVault, vault_cipher_representer)
  return safe_dumper


