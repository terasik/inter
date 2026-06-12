# test multiselecting objects with '*'
__all__ = ["prep_obj", "completion_build"]
import re
import pprint
from collections import namedtuple

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

def prep_obj(obj, path):
    if not path:
        return obj
    prep_path=_prep_path(path)
    print(f"---- prep_path: {prep_path}")
    prep_path=[p for p in prep_path.split('|') if p]
    po=PrepObj(value=obj)
    return _rec_prep_obj([po], prep_path)

def _rec_prep_obj(obj_list, prep_path, cnt=0, res_list=None):
    expr=prep_path[cnt]
    r=[]
    if res_list is None:
        res_list=[]
    #print(f"cnt={cnt}")
    #print(f"cnt={cnt} obj_list={obj_list}")
    for obj in obj_list:
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
        else:
            # TODO: what to do with other types?
            if isinstance(obj.value, dict):
                if expr in obj.value:
                    # if last eexpression 
                    if cnt == len(prep_path)-1:
                        res_list.append(PrepObj(value=obj.value[expr], key=expr, parent=obj.value))
                    else:
                        r.append(PrepObj(value=obj.value[expr]))
            elif isinstance(obj.value, list):
                idx=None
                try:
                    idx=int(re.match(r"\[(\d+)\]", expr).group(1))
                    value=obj.value[idx]
                except (AttributeError,IndexError,ValueError) as _exc:
                    print(f"idx error, but its ok: {_exc}" )
                except Exception as _exc:
                    print("unknown idx error")
                else: 
                    # if last expression 
                    if cnt == len(prep_path)-1:
                        res_list.append(PrepObj(value=value, key=idx, parent=obj.value))
                    else:
                        r.append(PrepObj(value=value))
            else:
                print("found something that are not list or dict")
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
    po=prep_obj(test_obj, test_path)
    pprint.pprint(po)
