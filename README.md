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

## examples/usage

### start
after installation of *obed* package you have executable *obed* script. start this script:
```shell
obed
```
after successfull start. you have *>* prompt.

### loading objects from file
to load objects from file you can use *open* for json objects or *open_yaml* for yaml objects. 





