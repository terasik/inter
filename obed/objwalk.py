# test multiselecting objects with '*'
__all__ = ["prep_obj", "completion_build"]
import re
import pprint
from collections import namedtuple
from functools import wraps
from inspect import signature, isfunction, Signature, BoundArguments
from copy import deepcopy
from obed.yavault import VaultData as VaDa
from obed.utils import convert_to_json

PrepObj=namedtuple('PrepObj', 'value, key, parent', defaults=("",{}))

test_obj={
    "a": { 
        "a1": 1,
        "a2": 3 
        },
    "b": { "a1": 2 },
    "b1": [10, 20, [30, {"g": 40}]],
    "c": "b",
    "e": { "e1": {"a1": 4}, "e2": 2},
    "d": {"a1": 3}
}

test_path="*[0]"
#splt_search_list=search_str.split(':')

def _par_args_value(value, sign):
    if "vault_id" in sign.parameters:
        return value
    return convert_to_json(value)

def _par_args_vault_id(vault_id):
    if vault_id is None and len(VaDa.vault_data)==1:
        return list(VaDa.vault_data.keys())[0]
    if vault_id is None and len(VaDa.vault_data)==0:
        raise ValueError("no vault-id's was defined/provided. see 'vault' command")
    if vault_id is None and len(VaDa.vault_data)>1:
        raise ValueError("no vault-id provided. see '-i' option")
    if not vault_id:
        raise ValueError("vault_id is empty or not provided")
    if vault_id not in VaDa.vault_data:
        raise ValueError(f"unknown vault-id '{vault_id}'. this vault-id's was defined: {list(VaDa.vault_data.keys())}")
    return vault_id

def _par_args_opath(opath, bind):
    obed_inst=bind.arguments.get("self")
    po=prep_obj(obed_inst.obj, opath)
    if not po:
        obed_inst.warn(f"no elements found for path '{opath}'")
    return po
    
def _par_args(sign: Signature, bind: BoundArguments) -> list:
    args=[]
    for par,val in sign.parameters.items():
        par_args_func=f"_par_args_{par}"
        arg_val=bind.arguments.get(par)
        if par_args_func in globals() and isfunction(globals()[par_args_func]):
            if par=="value":
                arg_val=globals()[par_args_func](arg_val, sign)
            elif par=="opath":
                arg_val=globals()[par_args_func](arg_val, bind)
            else:
                arg_val=globals()[par_args_func](arg_val)
        args.append(arg_val)
    return args

def oact(f):
    #def decor(f):
    @wraps(f)
    def inner(*args):
        sign=signature(f)
        bind=sign.bind(*args)
        obed_inst=bind.arguments.get("self")
        if not obed_inst.readonly:
            obed_inst.obj_hist.append(deepcopy(obed_inst.obj))
            r=f(*_par_args(sign, bind))
            #if change:
            obed_inst.build_completion_list()
        return r
    return inner
    #return decor

def prep_obj(obj, path):
    po=PrepObj(value=obj, parent=obj)
    if not path:
        return [po]
    prep_path=_prep_path(path)
    print(f"---- prep_path: {prep_path}")
    prep_path=[p for p in prep_path.split('|') if p]
    return _rec_prep_obj([po], prep_path)

def _rec_prep_obj(obj_list, prep_path, cnt=0, res_list=None):
    expr=prep_path[cnt]
    r=[]
    if res_list is None:
        res_list=[]
    print(f"cnt={cnt}")
    print(f"cnt={cnt} obj_list={obj_list}")
    for obj in obj_list:
        print(f"obj={obj}, expr={expr}")
        if expr=="*" or expr=="[*]":
            # TODO: what to do with other types?
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
                        r.append(PrepObj(value=value))
            else:
                print("* but what now?") 
                pass
        else:
            # TODO: what to do with other types?
            if isinstance(obj.value, dict):
                if expr in obj.value:
                    # if last eexpression 
                    if cnt == len(prep_path)-1:
                        res_list.append(PrepObj(value=obj.value[expr], key=expr, parent=obj.value))
                    else:
                        r.append(PrepObj(value=obj.value[expr]))
                else:
                    print(f"key '{expr}' does not exist")
                    # check next key
                    # create PrepObj depending on type of next key 
            elif isinstance(obj.value, list):
                idx=None
                try:
                    idx=int(re.match(r"\[(\d+)\]", expr).group(1))
                    value=obj.value[idx]
                except (AttributeError,IndexError,ValueError) as _exc:
                    print(f"idx error, but its ok: {_exc}" )
                    pass
                except Exception as _exc:
                    print("unknown idx error")
                    pass
                else: 
                    # if last expression 
                    if cnt == len(prep_path)-1:
                        res_list.append(PrepObj(value=value, key=idx, parent=obj.value))
                    else:
                        r.append(PrepObj(value=value))
            else:
                print("found something that are not list or dict")
                pass
    if cnt < len(prep_path)-1:
        _rec_prep_obj(r, prep_path, cnt+1, res_list)
    return res_list


def _prep_path(opath=""):
    """ convert opath to jmespath query string
    params: 
        opath: str -> path to object element (ex.: book[0]:id )
    return:
        opath_search: str -> jmespath query string (ex.: "book"|[0]|"id")
    """
    opath=re.sub(r"(\[[\d+\*]\])|:", r"|\1", opath)
    #opath_search="|".join([f'"{x}"' 
    #                       if not x.startswith('[') and not x=="*" else x 
    #                       for x in opath.split('|') if x])
    
    #print(f"---- opath_search: {opath_search}")
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

if __name__ == '__main__':
    print("test path: ", test_path)
    print("test obj : ")
    pprint.pprint(test_obj)
    po=prep_obj(test_obj, test_path)
    print("result   : ")
    pprint.pprint(po)
