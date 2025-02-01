"""
y=yaml.load(ys, Loader=get_loader())
print(y)
v=y['some_user']
print(v.plain_text, v.vault_id)

ys='''
---
some_user: !vault |
          $ANSIBLE_VAULT;1.2;AES256;nonprod
          34636135356562363932366561373066343764363663316234303463303930623338656266386533
          3730623164383032303865656261326466626237323764340a646339373536303830643562636363
          38306433313131623235386330643739666231633938656566366639636436343531656439663066
          3566623765343137660a653139333035303136373361366465343138393639633839383462656238
          3030
vault_tech_users:
  babu: !vault |
            $ANSIBLE_VAULT;1.2;AES256;nonprod
            65643064646466306635636431623830323664333735326162646238373039633834626236366433
            6433353835333638343339333465343831333930383133660a616233376330626533336232396464
            39316662656264373861383436303166346132383136386639326266613032306539613466333331
            3561643661306236620a613361613763366130383438623962663637636132336166353331623231
            3638
'''

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
  """ klasse für yaml vault tag """
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
    #self._vault=Vault(self._passwd['nonprod'])

  def __repr__(self):
    """ wird für yaml dumper benötigt """
    #return f"YamlVault(flsp={self.flsp}, vault_id={self._vault_id}, plain_text={self.decode()})"
    return self.cipher_text

  def handle_vault_id(self, cipher_text):
    """ ermittelt vault-id """
    flsp=cipher_text.splitlines()[0].split(";")
    self.flsp=flsp
    if len(flsp)==3:
      self._vault_id=None
    elif len(flsp)==4:
      self._vault_id=flsp[-1].strip()
    else:
      #logging.error("unbekanntes vault format (erste zeile): %s", flsp)
      #self._vault_id=None
      raise VaultError(f"vault format ist falsch (erste zeile): {flsp}")

  @property
  def vault_id(self):
    """ liefert vault-id zurück """
    return self._vault_id

  @vault_id.setter
  def vault_id(self, vault_id):
    self._vault_id=vault_id

  @property
  def cipher_text(self):
    """ liefert cipher text zurück """
    return self._cipher_text

  @cipher_text.setter
  def cipher_text(self, cipher_text):
    """ cipher text setzen/verarbeitung """
    if cipher_text:
      cipher_text=cipher_text.strip()
      self.handle_vault_id(cipher_text)
      self._plain_text=self.decode(cipher_text)
      self._cipher_text=cipher_text

  @property
  def plain_text(self):
    """ liefert plain text zurück """
    return self._plain_text

  @plain_text.setter
  def plain_text(self, plain_text):
    """ plain text setzen/verarbeitung """
    if plain_text:
      if not self.vault_id:
        raise VaultError("vault-id nicht übergeben")
      self._vault_id=self.vault_id
      self._cipher_text=self.encode(plain_text)
      self._plain_text=plain_text

  def decode(self, cipher_text):
    #if self._vault_id:
    #  vault=Vault(self._passwd[self._vault_id])
    #  return
    #else:
    for vault_id in self._passwd:
      vault=Vault(self._passwd[vault_id])
      try:
        dec_data=vault.load(cipher_text)
      except:
        #logging.debug("versuch mit vault-id %s zu entschlüsseln ist gescheitert", vault_id)
        continue
      else:
        self._vault_id=vault_id
        return dec_data
    raise VaultError("mit keinem der passwörter hat entschlüsselung der vault daten funktioniert")

  def encode(self, plain_text):
    #print("self._passwd: %s" % self._passwd)
    #print("self._vault_id: %s" % self._vault_id)
    vault=Vault(self._passwd[self._vault_id])
    return vault.dump_raw(plain_text)

def vault_constructor(loader, node):
  """Construct a greeting."""
  #return f"_vault_ {loader.construct_scalar(node)}"
  return YamlVault(cipher_text=loader.construct_scalar(node))

def get_loader():
  """Add constructors to PyYAML loader."""
  loader = yaml.SafeLoader
  loader.add_constructor("!vault", vault_constructor)
  return loader

"""
def vault_representer(dumper, vault):
  #return dumper.represent_scalar("!vault", vault.cipher_text, style='|')
  return dumper.represent_scalar("!vault", vault.plain_text)
"""

def vault_plain_representer(dumper, vault):
  #return dumper.represent_scalar("!vault", vault.cipher_text, style='|')
  return dumper.represent_scalar("!vault", vault.plain_text)

def vault_cipher_representer(dumper, vault):
  return dumper.represent_scalar("!vault", vault.cipher_text, style='|')

"""
def get_dumper():
  safe_dumper=yaml.SafeDumper
  safe_dumper.add_representer(YamlVault, vault_representer)
  return safe_dumper
"""

def get_plain_dumper():
  safe_dumper=yaml.SafeDumper
  safe_dumper.add_representer(YamlVault, vault_plain_representer)
  return safe_dumper

def get_cipher_dumper():
  safe_dumper=yaml.SafeDumper
  safe_dumper.add_representer(YamlVault, vault_cipher_representer)
  return safe_dumper


