# test multiselecting objects with '*'
__all__ = ["prep_obj", "completion_build"]
import re
from collections import namedtuple
from functools import wraps
from inspect import signature, isfunction, Signature, BoundArguments
from copy import deepcopy
from obed.yavault import VaultData as VaDa
from obed.utils import convert_to_json

# PrepObj used to describe elements of object. 
# PrepObj will be used for better handling of commands like setval, append
# and object path's described by '*' 
PrepObj=namedtuple('PrepObj', 'value, key, parent', defaults=("",{}))


def _par_args_value(value, **kwargs):
    """ handling value in oact decorator
    for actions like setval*, append*
    """
    sign=kwargs.get('sign')
    if "vault_id" in sign.parameters:
        return value
    return convert_to_json(value)

def _par_args_vault_id(vault_id, **kwargs):
    """ handling vault-id in oact decorator
    for vault action like setval_, append_vault
    """
    if vault_id is None and len(VaDa.vault_data)==1:
        vault_id=list(VaDa.vault_data.keys())[0]
    if vault_id is None and len(VaDa.vault_data)==0:
        raise ValueError("no vault-id's was defined/provided. see 'vault' command")
    if vault_id is None and len(VaDa.vault_data)>1:
        raise ValueError("no vault-id provided. see '-i' option")
    if not vault_id:
        raise ValueError("vault_id is empty or not provided")
    if vault_id not in VaDa.vault_data:
        raise ValueError(f"unknown vault-id '{vault_id}'. this vault-id's was defined: {list(VaDa.vault_data.keys())}")
    bind=kwargs.get('bind')
    obed_inst=bind.arguments.get("self")
    if obed_inst.obj_type!="yaml":
        obed_inst.pwarning("vault's can be used only with yaml objects. changing object type from {self.obj_type} to yaml")
        obed_inst.obj_type="yaml"
    return vault_id

def _par_args_opath(opath, **kwargs):
    """ convert opath astring argument to 
    prep object list in oact decorator
    """
    bind=kwargs.get('bind')
    obed_inst=bind.arguments.get("self")
    po_list=prep_obj(obed_inst, opath)
    if not po_list:
        obed_inst.warn(f"no elements found for path '{opath}'")
    return po_list
    
def _par_args(sign: Signature, bind: BoundArguments) -> list:
    """ handling arguments in oact decorator
    if _par_args_<argument_name> function exist, this 
    will be used to handle argument values
    """
    args=[]
    for par,val in sign.parameters.items():
        par_args_func=f"_par_args_{par}"
        arg_val=bind.arguments.get(par)
        if par_args_func in globals() and isfunction(globals()[par_args_func]):
            arg_val=globals()[par_args_func](arg_val, sign=sign, bind=bind)
        args.append(arg_val)
    return args

def oact(f):
    """ will be used as decorator for commands like setval, append,
        for handling funtions argument
            opath -> convert to prepared object list
            vault_id -> check provided vault_id's
            value -> converting to object
    """
    @wraps(f)
    def inner(*args):
        sign=signature(f)
        bind=sign.bind(*args)
        obed_inst=bind.arguments.get("self")
        if not obed_inst.readonly:
            obj_copy=deepcopy(obed_inst.obj)
            changed=f(*_par_args(sign, bind))
            ch_ele_cnt=changed.count(True)
            if ch_ele_cnt:
                obed_inst.obj_hist.append(obj_copy)
                obed_inst.build_completion_list()
        return any(changed)
    return inner

def prep_obj(obed_inst, path):
    """ convert path string to prep object list
    """
    po=PrepObj(value=obed_inst.obj, parent=obed_inst.obj)
    if not path:
        return [po]
    prep_path=_prep_path(path)
    prep_path=[p for p in prep_path.split('|') if p]
    return _rec_prep_obj([po], prep_path, obed_inst)


def _rec_prep_obj(obj_list, prep_path, obed_inst, cnt=0, res_list=None):
    """ recursive build prep object list
        
    """
    expr=prep_path[cnt]
    r=[]
    if res_list is None:
        res_list=[]
    for obj in obj_list:
        if expr=="*" or expr=="[*]":
            if isinstance(obj.value, dict):
                for key,value in obj.value.items():
                    # if last eexpression 
                    if cnt == len(prep_path)-1:
                        res_list.append(PrepObj(value=value, key=key, parent=obj.value))
                    else:
                        r.append(PrepObj(value=value))
            elif isinstance(obj.value, list):
                for key,value in enumerate(obj.value):
                    # if last eexpression 
                    if cnt == len(prep_path)-1:
                        res_list.append(PrepObj(value=value, key=key, parent=obj.value))
                    else:
                        r.append(PrepObj(value=value, key=key, parent=obj.value))
            else:
                obed_inst.perror(f"found neither list nor dict by recursive object walk at key '{expr}'")
        else:
            if isinstance(obj.value, dict):
                if expr in obj.value:
                    # if last eexpression 
                    if cnt == len(prep_path)-1:
                        res_list.append(PrepObj(value=obj.value[expr], key=expr, parent=obj.value))
                    else:
                        r.append(PrepObj(value=obj.value[expr]))
                else:
                    if cnt == len(prep_path)-1:
                        obed_inst.pwarning(f"key '{expr}' does not exist. trying to create or return null")
                        po=PrepObj(value=None, key=expr, parent=obj.value)
                        res_list.append(po)
                    else:
                        obed_inst.perror(f"can't create new key '{expr}' of path '{':'.join(prep_path)}'")
            elif isinstance(obj.value, list):
                idx=None
                try:
                    idx=int(re.match(r"\[(\d+)\]", expr).group(1))
                    value=obj.value[idx]
                except (AttributeError,IndexError,ValueError) as _exc:
                    obed_inst.perror(f"some index error at key '{expr}'")
                except Exception as _exc:
                    obed_inst.perror(f"unknown index error at key'{expr}': {_exc}")
                else: 
                    # if last expression 
                    if cnt == len(prep_path)-1:
                        res_list.append(PrepObj(value=value, key=idx, parent=obj.value))
                    else:
                        r.append(PrepObj(value=value))
            else:
                obed_inst.perror(f"found neither list nor dict by recursive object walk at key '{expr}'")
    if cnt < len(prep_path)-1:
        _rec_prep_obj(r, prep_path, obed_inst, cnt+1, res_list)
    return res_list


def _prep_path(opath=""):
    """ convert opath to jmespath query string
    params: 
        opath: str -> path to object element (ex.: book[0]:id )
    return:
        opath: str -> jmespath query string (ex.: book|[0]|id)
    """
    opath=re.sub(r"(\[[\d+\*]\])|:", r"|\1", opath)
    return "|".join([x for x in opath.split('|') if x])

def completion_build(o, s="", l=None):
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
                completion_build(v,f"{s}[{c}]", l)
            elif type(v) == dict:
                completion_build(v,f"{s}[{c}]:", l)
            else:
                l.append(f"{s}[{c}]")
    elif type(o)==dict:
        if not o:
            l.append(f"{s}")
        for k,v in o.items():
            if type(v) == list:
                completion_build(v,f"{s}{k}", l)
            elif type(v) == dict:
                completion_build(v,f"{s}{k}:", l)
            else:
                l.append(f"{s}{k}")
    else:
        #self.pwarning("")
        pass
    return l

