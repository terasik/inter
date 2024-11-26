#!/usr/bin/env python3

import readline
import cmd

class Inter(cmd.Cmd):
  """ command loop """
  prompt="> "
  intro="inter konsole"

  def __init__(self):
    super().__init__()
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \n\t=")

  def complete_ls(self,text, line, begidx, endidx):
      choices=["ch1", "ch2", "ch45"]
      if not text:
        completions=choices[:]
      else:
        completions=[c for c in choices if c.startswith(text)]
      return completions

  def do_ls(self, line):
    "liste etwas auf"
    print(f"liste {line} auf")

  def do_cd(self, line):
    print(f"wechsle zu {line}")

  def do_exit(self, line):
    """ ende """
    print("beende interaktive konsole")
    return True

if __name__ == "__main__":
  Inter().cmdloop()
