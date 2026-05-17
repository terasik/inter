import dataclasses
import typing

@dataclasses.dataclass
class PrepObj:

    obj: type
    idx: str|int
    multi: bool=False

    def prepare_search_string(self, opath=""):
        """ convert opath to jmespath query string
        params: 
            opath: str -> path to object element (ex.: book[0]:id )
        return:
            opath_search: str -> jmespath query string (ex.: "book"|[0]|"id")
        """
        opath=re.sub(r"(\[\d+\*\])|:", r"|\1", opath)
        opath_search="|".join([f'"{x}"' 
                               if not x.startswith('[') and not x=="*" else x 
                               for x in opath.split('|') if x])
        print(f"---- opath_search: {opath_search}")
        return opath_search

    def prepare_obj_for_action(self, obj, obj_hist, only_ref=False):
        """ preparing objects for next processing 
        (append, delete, setting values ) 
        params:
            opath: str  -> object element path string (Ex: 'a:b[0]')
            only_ref: bool -> if true get element of object 
                                which described by opath
                              if false return element ob object that 
                                will be edited
            return: tuppel -> (object element, index_or_key of element)
    
        """
        if not only_ref:
            self.obj_hist.append(deepcopy(self.obj))
        obj=self.obj
        idx_or_key=None
        opath_search=self._prepare_search_string(opath)
        opath_split=[x for x in opath_search.split('|') if x]
        for cnt,ele in enumerate(opath_split):
            l=re.match(r"\[(\d+)\]", ele)
            d=re.match(r"\"(.+?)\"", ele)
            if l:
                idx_or_key=int(l.group(1))
            else:
                idx_or_key=d.group(1)
            if (cnt < (len(opath_split)-1)) or only_ref:
                obj=obj[idx_or_key]
        return (obj, idx_or_key)



a=PrepObj({},0)
b=PrepObj([1],2, True)


print(a)
print(b)

print()

