"""
modul with helper functions
- loading, dumping json objects
- yaml vault dumpers
- generating password
"""
import json
import string
import secrets
import yaml
from obed.yavault import get_plain_dumper,get_cipher_dumper

def convert_to_json(value, check_type=False, raise_error=False):
  """ try to convert value to json
  if it doesn't work and check_type is false return value.

  when check_type is true, check of value type
  will be performed. if type of value is not list or 
  dict raise TypeError 
  
  params:
    value: obj -> value that will be converted to json
    check_type: bool -> if true check type of value.
                        when type of value is not list,dict
                        raise TypeError
    raise_error: bool -> raise errors. will be automatically 
                        set to True if check_type is True
  """
  if check_type: 
    raise_error=True
  try:
    js=json.loads(value)
  except (json.JSONDecodeError, TypeError) as exc:
    if raise_error:
      raise ValueError("json error: %s" % exc)
    return value
  if check_type and not isinstance(js, (list,dict)):
    raise TypeError("json is not dict or list")
  return js

def load_json(path):
  """ load json file

  params:
    path: str -> path to json file
  return:
    js: json -> loaded json object
  """
  with open(path) as _fr:
    js=json.load(_fr)
  return js

def obj_dumps(obj, obj_type="json"):
  """ return indentet json object
  as string. converting to ascii is disabled

  params: 
    obj: json -> object to dump
  return: 
    s: str -> object as json string
  """
  if obj_type=="json":
    s=json.dumps(obj, indent=2, ensure_ascii=False)
  elif obj_type=="yaml":
    s=yaml.dump(obj, Dumper=get_plain_dumper(), explicit_end=False, indent=2, default_style='')
  else:
    s=None
  return s

def dump_json(obj, path):
  """ write obj to path as json
  params:
    obj: json -> json object to write
    path: str -> path to file where obj will be written
  return: -
  """
  with open(path, 'w') as _fw:
    json.dump(obj, _fw, indent=2, ensure_ascii=False)


def dump_yaml(obj, path):
  """ write obj to path as json
  params:
    obj: yaml -> yaml object to write
    path: str -> path to file where obj will be written
  return: -
  """
  with open(path, 'w') as _fw:
    _fw.write(yaml.dump(obj, Dumper=get_cipher_dumper()))

def gen_passwd(l=17):
  a = string.ascii_letters + \
      string.digits + \
      "#!_@%"
  p = ''.join(secrets.choice(a) for i in range(l)) 
