"""
- editing objects (delete,append,set values to elements)
- build completion list for object elements
"""
import re
from copy import deepcopy
from collections import deque, namedtuple
import cmd2
import jmespath
from obed.utils import convert_to_json
from obed.yavault import YamlVault
from obed.objwalk import prep_obj,completion_build, oact



class ObjAction(cmd2.Cmd):
    """ class to walk through (json,yaml) objects 
    and 
        - editing object elements
        - build completion lists for existing elemets
        - getting values ob object elements
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
        """ return value of element path (opath)
        """
        if not opath:
            return self.obj
        po=prep_obj(self, opath)
        return [p.value for p in po]

    @oact
    def set_value_vault(self, opath, value, vault_id):
        """ setting value as vault value
        """
        value=YamlVault(plain_text=value, vault_id=vault_id)
        for p in opath:
            if p.key !='':
                p.parent[p.key]=value
            else:
                self.obj=value

    def append_value_vault(self, opath, value, vault_id):
        """ appending vault values to list
        """
        if not isinstance(value, (YamlVault)):
            if not vault_id:
                raise ValueError("vault_id not provided") 
            value=YamlVault(plain_text=value, vault_id=vault_id[0])
        if type(self._get_object_ref(opath)) != list:
            raise TypeError("object path is not a list. only appending to lists ist possible!")
        obj,idx_or_key=self._prepare_obj_for_action(opath)
        if opath:
            obj[idx_or_key].append(value)
        else:
            self.obj.append(value)
        self.build_completion_list()

    @oact
    def set_value(self, opath=None, value=None):
        """ setting value of object or object element
        params:
            opath: PrepObj
            value: obj -> value to be set
        return: -
        """
        for p in opath:
            if p.key !='':
                p.parent[p.key]=value
            else:
                self.obj=value

    @oact
    def append_value(self, opath="", value=None):
        """ append value to list in object
        described by opath
        """
        for p in opath:
            if p.key!='':
                if isinstance(p.value, list):
                    p.parent[p.key].append(value)
                else:
                    self.pwarning(f"object described by key '{p.key}' is not a list. appending values is only possible to lists")
            else:
                if isinstance(self.obj, list):
                    self.obj.append(value)
                else:
                    self.perror(f"object is not a list. appending values is only possible to lists")

    @oact
    def delete_element(self, opath=""):
        """ delete object element
        described by opath
        """
        for p in opath:
            if p.key!='':
                del p.parent[p.key]
            else:
                self.pwarning(f"setting whole object to empty dict")
                self.obj={}

    def _rec_compl_build(self, o, s="", l=None):
        """
        recursiv build of completion list. 
        walk through object and check if lements are lists
        or dicts. 
        by dicts append ':' to dict key (ex.: book:id)
        by lists append '[]' with index (ex.: [1][45])
        by others go to next element. example:
        object: { "book": {"id": 123, "authors": ["kira", "juraj]}}"}
        complition list: ["book:", "book:id", "book:authors[0]", "book:authors[1]"]
        """
        if l is None:
            l=[]
        if type(o)==list:
            if not o:
                l.append(f"{s}")
            for c,v in enumerate(o):
                if type(v) == list:
                    self._rec_compl_build(v,f"{s}[{c}]", l)
                elif type(v) == dict:
                    self._rec_compl_build(v,f"{s}[{c}]:", l)
                else:
                    l.append(f"{s}[{c}]")
        elif type(o)==dict:
            if not o:
                l.append(f"{s}")
            for k,v in o.items():
                if type(v) == list:
                    self._rec_compl_build(v,f"{s}{k}", l)
                elif type(v) == dict:
                    self._rec_compl_build(v,f"{s}{k}:", l)
                else:
                    l.append(f"{s}{k}")
        else:
            #self.pwarning("")
            pass
        return l

