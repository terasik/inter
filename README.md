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
  - *restore* - restore object from object history
  - *open* - loading json or yaml files
  - *new* - creating new json or yaml object from stdin (strings)
  - *save* - saving json or yaml objects to file
  - *close* - closing object (with save or without saving it)
  - *version* - print version of obed package/script
  - *gensec* - generate password(s) or url safe token(s)
- supporting ansible vault yaml values (**works only with yaml objects**)
  - *vault* - handling vault ids and vault passwords
  - *setval_vault* - setting vault values
  - *append_vault* - appending valut values to list
- supporting also all *cmd2* commands (*shell*, *alias*, ...)

## TODO's for future
- run default skript at startup

## examples/usage
some example files you can find in *~/.obed/* directory after first start of *obed* script

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
after successfull start you have *>* prompt.

### loading objects from file
to load objects from file use *open* command. use tabulator for path completion
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
use colon *:* to get subelements of objects. use *[]* to get elements of list.

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
> new '{"a": 23}' -j
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
tab completion works for *setval*

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
> new [] -j
> append -v where are you?
> print
[
  "where",
  "are",
  "you?"
]
>
```
tab completion works for *append*

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

### vault 
*vault* command is used to handle (read, save, edit) vault-id/password data to encrypt/decrypt ansible vault data. vault data works only wiith yaml objects. future versions of *obed* will support also json object with vault data.

#### reading/editing vault from stdin
to read vault id and corresponding password from stdin use
```
> vault -r
no vault_ids was provided. asking for vault_ids and their passwords
break asking loop with ';break', ';stop' or Ctrl-C
new vault id: floor
vault_id=floor doen't exits. provide password
password for vault_id=floor: 
new vault id:
```
to add new vault-id or to edit existing id use:
```
> vault floor -r
vault_id=floor alread exists with password=uhbvjhbdc
change password for vault_id=floor ? 
```
if vault-id doesn't exists output will be:
```
> vault very_new_vault_id -r
vault_id=very_new_vault_id doen't exits. provide password
password for vault_id=very_new_vault_id:
```

#### printing vault-id's
to print vault-id's and corresponding passwords use *-p* or *--print* option. example:
```
> vault -p
vault_id=abc, password=ztzewfd
vault_id=floor, password=uhbvjhbdc
vault_id=very_new_vault_id, password=jbfgr
```

#### loading vault-id file
*-l* option makes possible to load vault-ids and passwords from file. example file:
```
# example vault id file

# comment
# vault-id = password
buben = baraban
; should be also comment
bazuka = ty54#!jhB
```
to load vault-id file use:
```
> vault -l examples/vault_ids
> vault -p 
vault_id=abc, password=ztzewfd
vault_id=buben, password=baraban
vault_id=bazuka, password=ty54#!jhB
vault_id=floor, password=uhbvjhbdc
vault_id=very_new_vault_id, password=jbfgr
```
#### setting vault values
to set vault values use *setval_vault* command. for appending vault values to list use *append_vault* command. *copy* and *delete* commands works for both 'normal' and vault values. 
example of using vault data:
```
> # create new empty yaml object
> new -y                    
> # read vault-id and password from stdin                                                                                                                                                                                                     > vault -r                                                                                                                                                                                                                                    
no vault_ids was provided. asking for vault_ids and their passwords                                                                                                                                                                           
break asking loop with ';break', ';stop' or Ctrl-C                                                                                                                                                                                            
new vault id: pepelaz                                                                                                                                                                                                                         
vault_id=pepelaz doen't exits. provide password
password for vault_id=pepelaz: 
new vault id: ;stop
> # show yaml object
> print
{}
> # show all vault-ids with passwords
> vault -p
vault_id=pepelaz, password=UgzjhbzGhgt876d
> # set vault value with vault-id=pepelaz
> setval_vault vault_var --vault-id pepelaz --value gravizapa
> print
vault_var: !vault 'gravizapa'
> # set 'normal' variable
> setval normal_var --value "dodeskaden, dodeskaden"                                                                    
> print
normal_var: dodeskaden, dodeskaden
vault_var: !vault 'gravizapa'

> # save object to yaml file
> save some_vault.yml
saving as yaml to some_vault.yml
> # show yaml file with shell command cat ('!' is shortcut for 'shell' command)
> !cat some_vault.yml 
normal_var: dodeskaden, dodeskaden
vault_var: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  34373333333932633234316638336261316666333466656231643932346633666261346430643061
  3430353261613564373536306632636265396137303864310a316166653334653164303664613062
  33373135356433653335656161663336626236653232623231333833626230633137363537393235
  6665313933663064340a343065393638366537343062386331313461383830346130343934303332
  6533
> # done!
```

### creating new object from stdin
to create new json or yaml object from stdin use *new* command. 
to create new json object use *-j* or *--json* option. for yaml new yaml oqsbjects use *-y* or *--yaml*. 
if no positional args was provided to *new*, empty dict will be created.

json example:
```
> new --json '["a", true, {"b": "tr"}]'
> print
[
  "a",
  true,
  {
    "b": "tr"
  }
]
```
yaml example:
```
> new '["a", true, {"b": "tr"}]' -y
> print
- a
- true
- b: tr
```

### saving objects to file
to save objects to file use *save* command. you can use tab completion to select files.
if no positional args was provided, *obed* will try to save to the file opened with *open* cmd. 
if no *-t* or *--type*  option was provided, *save* cmd will use type (*json* or *yaml*) detected by *open* or *new* commands.
**NOTICE: ansible vault values works only with yaml**

### closing objects
to close objects use *close* command. if you have some unsaved changes you can save your object to file. 
if you want to close without saving provide *-n* option to *close* cmd.

### object change history
every change on object will be saved in internal object history list. up to 50 changes will be saved. to show object history use *showhist* command
```
> new -j
> setval a -v b
> setval b -v c
> setval c -v d
> print
{
  "a": "b",
  "b": "c",
  "c": "d"
}
> showhist
hist Nr. 0 -> 
{}
hist Nr. 1 -> 
{
  "a": "b"
}
hist Nr. 2 -> 
{
  "a": "b",
  "b": "c"
}
```
to restore object from internal history list use *restore* command. as example object histor we will use object defined above.
```
> # restore last-1 change
> restore -2
restoring obj from hist nr. -2
> print
{
  "a": "b"
}
> # restore to first change
> restore 0
restoring obj from hist nr. 0
> print
{}
```
examples for history nr (= history index):
- *0* first change
- *1* second change
- *-1* last change (default value for *restore* command)
- *-2* last-1 change
...

### generate secrets
to generate password or url-safe tokens use *gensec* command. usage:
```
gensec [-c COUNT] [-l LENGTH] [-t] 
```
options of *gensec* command:
- *-c*, *--count* - number of generated passwords/tokens. (default: 1, max: 10)
- *-l*, *--length* - length of generated password(s). (default: 17, max: 49)
  - don't work with *-t* option
- *-t*, *--token* - generate url-safe token(s)

examples:
```
> gensec -c 2 -l 23
0: FA9MwbCgmYr1uvePckWX3@
1: 0fkaf_CXJSe%BseyqOoTKL
> gensec -t
0: 3EvspWn_6TkP3BXoYSywDCiTAvUHZzbHfWY1FIiz2GE
```
