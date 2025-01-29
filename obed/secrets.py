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
import re
from getpass import getpass
import cmd2


vault_id_rgx=r'[a-zA-Z_0-9]+'
vault_id_choices=(";break", ";stop")

class VaultData:
  """ class for vault password data
  (vault_ids, passwords)
  """
  vault_data={}

class ObedVault():
  """ vault password """
  
  def vault_data_print(self, vault_ids=[]):
    """ print vault ids
    if no vault_ids provided print 
    everything
    """
    if vault_ids:
      for vid in vault_ids:
        self.poutput("vault_id=%s, password=%s" % (vid, self.vault_data[vid]))
    else:
      for vid,pwd in self.vault_data.items():
        self.poutput("vault_id=%s, password=%s" % (vid,pwd))


  def ask_vault_id_passwd(self, vid, try_cnt=3):
    """ function that read vault_id(vid) from stdin
    """
    for _ in range(try_cnt):
      p=getpass("password for vault_id=%s: " % vid)
      p=p.strip()
      if not p:
        self.pwarning("invalid or empty password")
        continue
      return p
    raise ValueError("invalid or empty password provided")

      
  def check_and_set_vault_data(self, vid, ask_for_passwd=True):
    """ check if vault_id (vid) already exists
    and set/change password of this id
    """
    # if vvault id already exists in vault_data
    if vid in self.vault_choice_provider():
      # if vault_id already exists and has passwd
      if self.vault_data[vid]:
        self.poutput("vault_id=%s alread exists with password=%s" % (vid, self.vault_data[vid]))
        if ask_for_passwd:
          i=self.read_input("change password for vault_id=%s ? " % vid,
                            completion_mode=cmd2.CompletionMode.CUSTOM,
                            choices=["yes", "no"])
          if re.match("yes|ja|y|j", i, re.I): 
            self.vault_data[vid]=self.ask_vault_id_passwd(vid)
      # vault_id exists but without password
      else:
        self.poutput("vault_id=%s already exists, but without password" % (vid))
        if ask_for_passwd:
          self.vault_data[vid]=self.ask_vault_id_passwd(vid)
    # if vault id not in vault data
    else:
      #self.vault_data[vid]=self.ask_vault_id_passwd(vid)
      if ask_for_passwd:
        self.poutput("vault_id=%s doen't exits. provide password" % vid)
        p=self.ask_vault_id_passwd(vid)
      else:
        self.poutput("adding vault_id=%s without password" % vid)
        p=""
      self.vault_data.update({vid: p})


  def vault_data_read(self, args):
    """ read passwords from stdin
    if no vault_ids provided ask also for vault_id names
    """
    # if vault_ids was provided
    if args.vault_ids:
      for vid in args.vault_ids:
        self.check_and_set_vault_data(vid)
    # no vault_id provided
    else:
      self.poutput("no vault_ids was provided. asking for vault_ids and their passwords\n"
                    "break asking loop with ';break', ';stop' or Ctrl-C")
      try:      
        while True:
          vid=self.read_input("new vault id: ",
                            completion_mode=cmd2.CompletionMode.CUSTOM,
                            choices=vault_id_choices)
          if vid in vault_id_choices:
            break
          elif re.match(vault_id_rgx, vid):
            self.check_and_set_vault_data(vid)
          else:
            self.perror("vault id %s doesn't match regex %s. provide new vault id" %
                        (vid, vault_id_rgx))
      except KeyboardInterrupt:
        self.poutput("stop the mystery vault id asking train")


  def vault_data_load_file(self, args):
    """ loading vault id file with format
    # comment
    vault_id = password
    ...
    vault_id_N = password_N
    """
    #self.poutput("loading vault data file")
    with open(args.load_file[0]) as f:
      lines=f.readlines()
    for cnt,line in enumerate(lines):
      line=line.strip()
      # empty line
      if not line:
        #self.poutput("  line %s -> empty" % cnt)
        continue
      #  comments
      if re.search(r'^\s*[#;]', line):
        #self.poutput("  line %s -> comment" % cnt)
        continue
      #r=re.match('^\s*(?P<vault_id>'+vault_id_rgx+')\s*=?\s*(?P<passwd>[^\s"\']+)?')
      r=re.match('^\s*(?P<vault_id>'+vault_id_rgx+')\s*(=\s*(?P<passwd>[^\s"\']+))?\s*$', line)
      if r:
        vid=r.group("vault_id")
        passwd=r.group("passwd")
        #self.poutput(" line %s -> ok vid=%s password=%s" % (cnt, vid, passwd))
        if vid in self.vault_data:
          self.pwarning("overwrite vault id %s" % vid) 
        self.vault_data.update({vid: passwd})
      else:
        self.pwarning("ignoring line %s (%s)" %(cnt,line))


  def handle_vault_ids_args(self, args):
    """ get vault ids from args (argpraser)
    if -r option is provided read password from stdin
    if -l option provided load file
    if no of both options, set only vault_ids
    """
    if args.read:
      self.vault_data_read(args)
    elif args.load_file:
      self.vault_data_load_file(args)
    else:
      for vid in args.vault_ids:
        self.check_and_set_vault_data(vid, False)

    

  

  

