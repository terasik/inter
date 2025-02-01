# obed Package

object interactive editor with command and object element tab completion.

## general
project for interactive editing json or yaml objects. based on *cmd2* package. thanks to *cmd2* team!

## works
- handling json, yaml objects. possible actions
  - *setval* - setting values. possible values are all values that json,yaml also support (int, list, dict,..)
  - *append* - appending values to lists
  - *delete* - delete elements
  - *copy* - copy values from elements to another elements
  - *print* - printing yaml or json objects to sdtout
  - *showhist* - show object history after changes
  - *open*,*open_yaml* - loading json or yaml files
  - *new*,*new_yaml* - creating new json or yaml object from stdin (strings)
  - *save*,*save_yaml* - saving json or yaml objects to file
  - *close* - closing object (with save or without saving it)
- supporting ansible vault yaml values
  - *vault* - handling vault ids and vault passwords
  - *setval_vault* - setting vault values
  - *append_vault* - appending valut values to list
- supporting also all *cmd2* commands (*shell*, *alias*, ...)

## TODO's
- documentation
- *version* cmd
- some helpfull aliase like *exit*
- restoring object from history with *restore* command

## examples/usage
for next steps: 
-  example json object (*example.json* file):
```json
{ 
  "a": "searching", 
  "b": { "for": "sugar"},
  "c": [ "man" ],
  "d": 0
}
```
- example yaml object (*example.yml* file):
```yaml
---
a: searching
b:
  for: sugar
c:
  - man
d: 0
```

### start
after installation of *obed* package you have executable *obed* script. start this script:
```shell
obed
```
after successfull start. you have *>* prompt.

### loading objects from file
to load objects from file use *open* for json objects or *open_yaml* for yaml objects. use tabulator for path completion
```
open examples/example.json
```
or
```
open examples/example.yml
```
### printing objects/object elements
command *print* can be used to show objects:
```
> print
{
  "a": "searching",
  "b": {
    "for": "sugar"
  },
  "c": [
    "man"
  ],
  "d": 0
}
```
to print only specific elements of object use tab complition of print:
```
> print b b:for c[0] 
b -> 
{
  "for": "sugar"
}
b:for -> 
"sugar"
c[0] -> 
"man"
```
using colon *:* to get subelements of objects. use *[]* to get elements of list.

### setting values of object/object elements
to set value of object elements use *setval* command. to set new value to element use:
```
setval b:for d --value "sugar sugar"
```
result of this command is:
```json
{
  "a": "searching",
  "b": {
    "for": "sugar sugar"
  },
  "c": [
    "man"
  ],
  "d": "sugar sugar"
}
```
value can also be some complex data structure like:
```
setval a --value '{"she": {"lost": ["control", 1], "again": true}}'
```
result of setting *a* is:
```
> print a
a -> 
{
  "she": {
    "lost": [
      "control",
      1
    ],
    "again": true
  }
}
```
to take value from another object element use *-t* option of *setval* cmd:
```
setval d -t a:she:lost[1]
```
result of taking value from *a:she:lost[1]*:
```
> print d
d -> 
1
```
with *setval* it is also possible to add new elements. example:
```
setval a:she:get --value nothing
```
add new *get* element with value *nothing* to *a:she* dictionary. result:
```
> print a
a -> 
{
  "she": {
    "lost": [
      "control",
      1
    ],
    "again": true,
    "get": "nothing"
  }
}
```

use *setval --help* for help
it is possible to set one value to many elements. you can set also value to whole object. example:
```
> new '{"a": 23}'
> print
{
  "a": 23
}
> setval -v '["trubadur", 65]'
> print
[
  "trubadur",
  65
]
>
```
### appending values to lists

command *append* make it possible to append new (*-v* or *--value* option) or existing (*-t* or *--take-from* option) elements to lists. example:
```
append c a:she:lost --value bugi wugi
```
result:
```
> print
{
  "a": {
    "she": {
      "lost": [
        "control",
        1,
        "bugi",
        "wugi"
      ],
      "again": true,
      "get": "nothing"
    }
  },
  "b": {
    "for": "sugar sugar"
  },
  "c": [
    "man",
    "bugi",
    "wugi"
  ],
  "d": 1
}
```
to append value from existing elemt use *-t* or *--take-from* option
```
append c -t b b:for
```
result:
```
> print c
c -> 
[
  "man",
  "bugi",
  "wugi",
  {
    "for": "sugar sugar"
  },
  "sugar sugar"
]
```

with *append* you can append one or more values to one or more object elements. if whole object is a list, you can append also to whole object values. example
```
> new []
> append -v where are you?
> print
[
  "where",
  "are",
  "you?"
]
>
```
### copy elements 
*copy* command can  copy value of one elemet to another element. notice: *copy* perform a deepcopy of values. general usage:
```
copy VALUE_OF_ELEMENT_1 ...  VALUE_OF_ELEMENT_N --dest ELEMENT_1 ... ELEMENT_N
```
*copy* allows you to copy one or more element values to anothor elements. example:
```
> copy d -d a:she:again c[2]
> print
{
  "a": {
    "she": {
      "lost": [
        "control",
        1,
        "bugi",
        "wugi"
      ],
      "again": 1,
      "get": "nothing"
    }
  },
  "b": {
    "for": "sugar sugar"
  },
  "c": [
    "man",
    "bugi",
    1,
    {
      "for": "sugar sugar"
    },
    "sugar sugar"
  ],
  "d": 1
}
```
tab completion works for *copy*
### delete elements
with *delete* you can delete object elements. example:
```
> delete a:she d
> print
{
  "a": {},
  "b": {
    "for": "sugar sugar"
  },
  "c": [
    "man",
    "bugi",
    1,
    {
      "for": "sugar sugar"
    },
    "sugar sugar"
  ]
}
```
tab completion works for *delete*

