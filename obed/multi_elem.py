# test multiselecting objects with '*'

import re
from collections import namedtuple
import pprint

PrepObj=namedtuple('PrepObj', 'value, key, parent', defaults=("",{}))

start_obj={
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

search_str="*"
splt_search_list=search_str.split('|')

def prep_obj(obj=start_obj):
    po=PrepObj(value=obj)
    return _rec_prep_obj([po])

def _rec_prep_obj(obj_list, cnt=0, res_list=None):
    expr=splt_search_list[cnt]
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
                    if cnt == len(splt_search_list)-1:
                        res_list.append(PrepObj(value=value, key=key, parent=obj.value))
                    else:
                        r.append(PrepObj(value=value))
            elif isinstance(obj.value, list):
                for key,value in enumerate(obj.value):
                    # if last eexpression 
                    if cnt == len(splt_search_list)-1:
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
                    if cnt == len(splt_search_list)-1:
                        res_list.append(PrepObj(value=value, key=expr, parent=obj.value))
                    else:
                        r.append(PrepObj(val=obj.value[expr]))
            elif isinstance(obj.value, list):
                idx=None
                try:
                    idx=int(re.match(r"\[(\d+)\]", expr).group(1))
                    value=obj.value[idx]
                except (AttributeError,IndexError,ValueError):
                    print("idx error")
                except Exception as _exc:
                    print("unknown idx error")
                else: 
                    # if last expression 
                    if cnt == len(splt_search_list)-1:
                        res_list.append(PrepObj(value=value, key=idx, parent=obj.value))
                    else:
                        r.append(PrepObj(value=value))
            else:
                print("i don't now what to do")
    #print(f"cnt={cnt} r={r}")
    if cnt < len(splt_search_list)-1:
        _rec_prep_obj(r, cnt+1, res_list)
    return res_list

po=prep_obj()
pprint.pprint(po)
#print(f"orig id={id(start_obj['a'])}")
#print(f"new id ={id(po[0].val)}")
#print(f"orig id={id(start_obj['b'])}")
#print(f"new id ={id(po[1].val)}")
