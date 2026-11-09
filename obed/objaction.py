"""
- editing objects (delete,append,set values to elements)
- build completion list for object elements
"""
import re
from copy import deepcopy
from collections import deque
import cmd2
import jmespath
from obed.utils import convert_to_json
from obed.yavault import YamlVault
from obed.objwalk import prep_obj,completion_build, oact



class ObjAction(cmd2.Cmd):
    """ set, append, get, delete values  
    """
    def __init__(self, obj=None):
        super().__init__()
        self.readonly=False
        self.coml_list=[]
        self.obj=obj
        self.obj_hist=deque([], 50)
  
    @property
    def obj(self):
        return self._obj

    @obj.setter
    def obj(self, obj):
        self._obj=obj
        self.build_completion_list()


    def build_completion_list(self):
        """ build completion  list for object paths
        (opath parameters by many functions)
        ['a[0]', 'a[1]', "b", "c", "c:o1", "c:o2", d]
  
        """
        self.compl_list=completion_build(self.obj)

    def get_value(self, opath=""):
        """ return value of object element
            described by opath 
        """
        if not opath:
            return self.obj
        po=prep_obj(self, opath)
        return [p.value for p in po]

    def _set_value(self, po_list, value):
        """ setting value of object element(s)
            in po_list (prepared object list)
        """
        changed=[False]
        for p in po_list:
            if p.key !='':
                try:
                    changed.append(True) if p.parent[p.key]!=value else changed.append(False)
                except (KeyError, IndexError):
                    changed.append(True)
                except Exception as exc:
                    self.perror(f"unknown error by setting value '{value}' for key '{p.key}': {exc}")
                p.parent[p.key]=value
            else:
                changed.append(True) if self.obj!=value else changed.append(False)
                self.obj=value
        return changed

    def _append_value(self, po_list, value):
        """ appending value to object element(s)
            in po_list (prepared object list)
        """
        changed=[False]
        for p in po_list:
            if p.key!='':
                if isinstance(p.value, list):
                    p.parent[p.key].append(value)
                    changed.append(True)
                else:
                    self.pwarning(f"object described by key '{p.key}' is not a list. appending values is only possible to lists")
            else:
                if isinstance(self.obj, list):
                    self.obj.append(value)
                    changed.append(True)
                else:
                    self.perror(f"object is not a list. appending values is only possible to lists")
        return changed


    @oact
    def set_value_vault(self, opath, value, vault_id):
        """ setting vault value to object elements
            described by opath

            oact decor transform opath string to prepared
            object list

        """
        value=YamlVault(plain_text=value, vault_id=vault_id, vault_format_12=self.vault_format_12)
        changed=self._set_value(opath, value)
        return changed

    @oact
    def append_value_vault(self, opath, value, vault_id):
        """ appending vault values to list
        """
        value=YamlVault(plain_text=value, vault_id=vault_id, vault_format_12=self.vault_format_12)
        changed=self._append_value(opath, value)
        return changed

    @oact
    def set_value(self, opath, value):
        """ setting value of object or object element
        params:
            opath: PrepObj
            value: obj -> value to be set
        return: -
        """
        changed=self._set_value(opath, value)
        return changed

    @oact
    def append_value(self, opath, value):
        """ append value to list in object
        described by opath
        """
        changed=self._append_value(opath, value)
        return changed

    @oact
    def delete_element(self, opath=""):
        """ delete object element
        described by opath
        """
        changed=[False]
        for p in opath:
            if p.key!='':
                del p.parent[p.key]
                changed.append(True)
            else:
                self.pwarning(f"setting whole object to empty dict")
                self.obj={}
                changed.append(True)
        return changed

