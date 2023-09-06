<!--
This file is auto-generated and any changes made to it will be overwritten
-->
# tests

## tests._test


### Audit

Test when audit passes and fails.


### Audit error did no pass all checks

Test raising of `AuditError`.


### Audit raise

Test when audit fails with raised error.


### Autoname

Test names are automatically added as they should be.


### Default key

Test setting and restoring of existing dict keys.


### Default plugin

Test invalid module name provided.


### Del key in context

Confirm there is no error raised when deleting temp key-value.


### Imports

Test imports from relative plugin dir.


### Keyboard interrupt

Test commandline `KeyboardInterrupt`.


### Modules

Test expected output for help after plugins have been loaded.

Test no positional argument for json array of keys.
Test `audit` positional argument and docstring display.
Test all and display of all module docstrings.


### No exe provided

Test default value for exe property.


### Not a valid git repository

Test exit when not in a git repository.


### Parametrize

Test class for running multiple plugins.


### Parametrize fail

Test class for running multiple plugins.


### Plugin mro

Assert that plugins can inherit other plugins.

Prior to this commit 

```
``
```

PluginType\`\`s were only permitted, and not
children of 

```
``
```

PluginType\`\`s.


### Plugins call

Get coverage on `Plugin.__call__.`


### Register invalid type

Test correct error is displayed when registering unknown type.


### Register plugin name conflict error

Test `NameConflictError` is raised when same name provided.


### Staged file removed

Test run blocked when staged file removed.

Without this, files that do not exist could be passed to plugin
args.


