Changelog
=========
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

[Unreleased](https://github.com/jshwi/pyaud/compare/v7.5.1...HEAD)
------------------------------------------------------------------------
### Changed
- drop support for python3.8

### Security
- Update vulnerable dependencies

[7.5.1](https://github.com/jshwi/pyaud/releases/tag/v7.5.1) - 2024-04-09
------------------------------------------------------------------------
### Fixed
- relax version constraints for arcon

[7.5.0](https://github.com/jshwi/pyaud/releases/tag/v7.5.0) - 2024-02-01
------------------------------------------------------------------------
### Changed
- pin minimum pyaud-plugins version which enforces new style

[7.4.0](https://github.com/jshwi/pyaud/releases/tag/v7.4.0) - 2024-01-31
------------------------------------------------------------------------
### Changed
- bump pyaud-plugins including extra style enforcement

[7.3.1](https://github.com/jshwi/pyaud/releases/tag/v7.3.1) - 2024-01-06
------------------------------------------------------------------------
### Fixed
- relax version requirement for `pyaud-plugins`

[7.3.0](https://github.com/jshwi/pyaud/releases/tag/v7.3.0) - 2023-11-30
------------------------------------------------------------------------
### Changed
- bump pyaud-plugins

[7.2.2](https://github.com/jshwi/pyaud/releases/tag/v7.2.2) - 2023-11-27
------------------------------------------------------------------------
### Fixed
- published commit to pypi by accident

[7.2.1](https://github.com/jshwi/pyaud/releases/tag/v7.2.1) - 2023-11-27
------------------------------------------------------------------------
### Fixed
- use system agnostic root when finding pyproject.toml

[7.2.0](https://github.com/jshwi/pyaud/releases/tag/v7.2.0) - 2023-09-17
------------------------------------------------------------------------
### Fixed
- relax version requirement for `arcon`

[7.1.0](https://github.com/jshwi/pyaud/releases/tag/v7.1.0) - 2023-09-12
------------------------------------------------------------------------
### Added
- add `pyaud.plugins.PluginType`

[7.0.0](https://github.com/jshwi/pyaud/releases/tag/v7.0.0) - 2023-09-09
------------------------------------------------------------------------
### Added
- prune uncommitted objects from cache

### Changed
- change `pyaud.plugins.PLUGIN_NAMES` type to tuple
- change `pyaud.plugins.PLUGINS` type to tuple
- change name of uncommitted key
- remove project key from cache
- update error reporting

### Removed
- remove `pyaud.plugins.PluginType`
- remove `pyaud.plugins.PluginInstance`
- remove annotations from namespace
- remove `pyaud.plugins.UNCOMMITTED`
- remove `pyaud.plugins.FALLBACK`
- remove `pyaud.plugins.CACHE_FILE`
- remove `PYAUD_CACHE`
- remove `pyaud.plugins.Plugins.env`
- remove `pyaud.plugins.Plugin.exe`
- remove `pyaud.plugins.Plugin.subprocess`

[6.2.2](https://github.com/jshwi/pyaud/releases/tag/v6.2.2) - 2023-04-29
------------------------------------------------------------------------
### Fixed
- Remove `codecov` dependency

[6.2.1](https://github.com/jshwi/pyaud/releases/tag/v6.2.1) - 2023-02-28
------------------------------------------------------------------------
### Fixed
- Add support for Python 3.10

[6.2.0](https://github.com/jshwi/pyaud/releases/tag/v6.2.0) - 2023-02-28
------------------------------------------------------------------------
### Added
- Add support for Python 3.10

[6.1.2](https://github.com/jshwi/pyaud/releases/tag/v6.1.2) - 2023-02-26
------------------------------------------------------------------------
### Fixed
- Fix minimum version for `pyaud-plugins`

[6.1.1](https://github.com/jshwi/pyaud/releases/tag/v6.1.1) - 2023-02-26
------------------------------------------------------------------------
### Fixed
- Fix minimum version for `lsfiles`

[6.1.0](https://github.com/jshwi/pyaud/releases/tag/v6.1.0) - 2023-02-26
------------------------------------------------------------------------
### Added
- Add commandline `KeyboardInterrupt`
- Block runs when staged file removed

[6.0.1](https://github.com/jshwi/pyaud/releases/tag/v6.0.1) - 2023-02-26
------------------------------------------------------------------------
### Fixed
- Fix `-n/--no-cache` argument

[6.0.0](https://github.com/jshwi/pyaud/releases/tag/v6.0.0) - 2023-02-26
------------------------------------------------------------------------
### Added
- Add garbage collection
- Add constants to `pyaud.plugins`
- Add commandline exit for running outside of a git repository
- Add `pyaud.plugins.Subprocesses`
- Add `pyaud.messages`

### Changed
- Move `BasePlugin` to `pyaud.plugins`
- Remove project parent key from cache
- Update audit messages for consistency
- Make `Plugin.subprocess` a property
- Make `Plugin.name` a property
- Create cache dir after loading plugins

### Removed
- Remove warning for no files found
- Remove command not found warning
- Remove `FixFile` plugin

[5.0.1](https://github.com/jshwi/pyaud/releases/tag/v5.0.1) - 2023-02-09
------------------------------------------------------------------------
### Fixed
- Fix issue where failing `Parametrize` would not fail audit

[5.0.0](https://github.com/jshwi/pyaud/releases/tag/v5.0.0) - 2023-02-08
------------------------------------------------------------------------
### Added
- Add results to end of audit
- Add additional info for audit
- Add default plugin if incorrect plugin provided
- add `pyaud.pyaud`
- Add returncode to `pyaud.main`
- Add `pyaud.main`
- Add `--audit` argument
- Add `--exclude` argument

### Changed
- Change `audit` arg type
- File exclusions now uses regex instead of list
- Change `exclude` type from dict to list
- Rename `indexing` key to `exclude`
- Change `pyaud modules` positional to a builtin plugin
- Change cache dir to repo location
- Only parse pyproject.toml for config

### Removed
- Remove `-s/--suppress`
- Remove `AuditError`
- Remove default `audit` values
- Remove default `exclude` values
- Remove `pyaud.package`
- Remove logging
- Remove backup config
- Remove `-c/--clean` argument
- Remove `--rcfile` argument
- Remove `-t/--timed` argument

[4.1.0](https://github.com/jshwi/pyaud/releases/tag/v4.1.0) - 2023-01-05
------------------------------------------------------------------------
### Added
- Add support for `pre-commit`
- Add py.typed

### Security
- Add `usedforsecurity=False` to `hashlib`'

[4.0.2](https://github.com/jshwi/pyaud/releases/tag/v4.0.2) - 2022-08-05
------------------------------------------------------------------------
### Fixed
- Moves `configure_global` back to config to ensure config populated

[4.0.1](https://github.com/jshwi/pyaud/releases/tag/v4.0.1) - 2022-08-05
------------------------------------------------------------------------
### Fixed
- Ensures `pyaud-plugins>=0.8.0` is used

[4.0.0](https://github.com/jshwi/pyaud/releases/tag/v4.0.0) - 2022-08-04
------------------------------------------------------------------------
### Changed
- Reduces unnecessary logging
- Logs lowercase

### Fixed
- Removes second warning for single issue

### Removed
- Removes env variables
- Removes `pyaud.git`
- Removes `pyaud.config`
- Removes `pyaud.working_tree_clean`
- Removes `pyaud.get_packages`
- Removes `pyaud.get_commit_hash`
- Removes `pyaud.main`
- Removes `pyaud.Environ`
- Removes `pyaud.register_default_plugin`
- Removes `pyaud.HashMapping`
- Removes `pyaud.parsers`
- Removes `-d/--deploy` arg
- Removes `pyaud.branch`
- Removes env config for app dirs and files
- Removes `Write` plugin

[3.13.5](https://github.com/jshwi/pyaud/releases/tag/v3.13.5) - 2022-05-05
------------------------------------------------------------------------
### Fixed
- Relaxes version constraints on some dependencies

[3.13.4](https://github.com/jshwi/pyaud/releases/tag/v3.13.4) - 2022-04-30
------------------------------------------------------------------------
### Changed
- change: Clears cache for missing file

### Fixed
- Prevents crash when file does not get created for `Fix`

[3.13.3](https://github.com/jshwi/pyaud/releases/tag/v3.13.3) - 2022-04-29
------------------------------------------------------------------------
### Fixed
- Fixed issue where single files were not updating once hashed

[3.13.2](https://github.com/jshwi/pyaud/releases/tag/v3.13.2) - 2022-04-29
------------------------------------------------------------------------
### Fixed
- Fixed `PYAUD_CACHE` which was pointing to `PYAUD_DATADIR`

[3.13.1](https://github.com/jshwi/pyaud/releases/tag/v3.13.1) - 2022-04-29
------------------------------------------------------------------------
### Fixed
- Fixes file cache to return exit-code for missing files
- Fixes cache logging

[3.13.0](https://github.com/jshwi/pyaud/releases/tag/v3.13.0) - 2022-04-29
------------------------------------------------------------------------
### Added
- Adds individual file cache
- Adds `FixAll` plugin

### Change
- Updates `Fix.__call__` for more flexible error handling

[3.12.1](https://github.com/jshwi/pyaud/releases/tag/v3.12.1) - 2022-04-26
------------------------------------------------------------------------
### Fixed
- Relaxes the version constraints on `pyaud_plugins`

[3.12.0](https://github.com/jshwi/pyaud/releases/tag/v3.12.0) - 2022-04-24
------------------------------------------------------------------------
### Added
- Allows for plugins to be named automatically if no name provided

[3.11.1](https://github.com/jshwi/pyaud/releases/tag/v3.11.1) - 2022-04-23
------------------------------------------------------------------------
### Fixed
Reverts `pyaud.get_packages` but does not raise

[3.11.0](https://github.com/jshwi/pyaud/releases/tag/v3.11.0) - 2022-04-20
------------------------------------------------------------------------
### Changed
- `pyaud.get_packages` now resolves to project root

[3.10.0](https://github.com/jshwi/pyaud/releases/tag/v3.10.0) - 2022-04-01
------------------------------------------------------------------------
### Changed
Bumps `pyaud-plugins` from 0.2.0 to 0.3.0

[3.9.0](https://github.com/jshwi/pyaud/releases/tag/v3.9.0) - 2022-03-20
------------------------------------------------------------------------
### Added
- Adds logger to time-keeper
- Adds `pyaud.Plugin`
- Adds `pyaud.main`
- Adds `pyaud.initialize_dirs`
- Adds `pyaud.HashMapping`
- Adds `pyaud.Environ`

### Changed
- Improves `pyaud.plugins.load` to search for prefixes

### Fixed
- Handles `TypeError`s by returning `typing.Any` attributes

[3.8.0](https://github.com/jshwi/pyaud/releases/tag/v3.8.0) - 2022-01-09
------------------------------------------------------------------------
### Added
- Logs commencement of audit
- Adds logger for coverage.xml path

### Fixed
- Fixes `poetry` packaging
- Deploy runs `deploy-cov` before `deploy-docs`

[3.7.0](https://github.com/jshwi/pyaud/releases/tag/v3.7.0) - 2022-01-09
------------------------------------------------------------------------
### Added
- Logs commencement of audit
- Adds logger for coverage.xml path

### Fixed
- Deploy runs `deploy-cov` before `deploy-docs`

[3.6.0](https://github.com/jshwi/pyaud/releases/tag/v3.6.0) - 2022-01-04
------------------------------------------------------------------------
### Added
- Adds `PYAUD_FIX` env var
- Adds `PYAUD_TIMED` env var
- Adds `pyaud.environ`

[3.5.0](https://github.com/jshwi/pyaud/releases/tag/v3.5.0) - 2021-12-31
------------------------------------------------------------------------
### Changed
- Warns instead of crashes when command not found

### Fixed
- `cache` set to False for `pyaud clean`
- `pyaud docs` runs properly if using MD README instead of RST
- Essentials config keys will be restored to their defaults if missing

[3.4.0](https://github.com/jshwi/pyaud/releases/tag/v3.4.0) - 2021-12-30
------------------------------------------------------------------------
### Added
- Adds deepcopy functionality to `pyaud.plugin.Plugin`

### Fixed
- Fixes time tracking with nested plugins

[3.3.0](https://github.com/jshwi/pyaud/releases/tag/v3.3.0) - 2021-12-28
------------------------------------------------------------------------
### Added
- Adds file caching
- Adds timed feature
- Adds `pyaud.working_tree_clean`
- Adds `pyaud.get_commit_hash`
- Adds `pyaud --verison` option
- Adds cache flags to `pyaud.BasePlugin`
- Adds logger to `BasePlugin`
- Adds `pyaud.BasePlugin` class for typing

### Fixed
- Fixes returncode with tests
- Allows for multiple inheritance of plugins
- Ensures audit returns exit-status
- Ensures that all files indexed are unique
- Fixes up typing
- Fixes up context classes

[3.2.10](https://github.com/jshwi/pyaud/releases/tag/v3.2.10) - 2021-11-14
------------------------------------------------------------------------
### Fixed
- Fixes `pyaud generate-rcfile` when piping to file

[3.2.9](https://github.com/jshwi/pyaud/releases/tag/v3.2.9) - 2021-11-08
------------------------------------------------------------------------
### Fixed
- Bypasses `TypeError` when configuring logger

[3.2.8](https://github.com/jshwi/pyaud/releases/tag/v3.2.8) - 2021-10-25
------------------------------------------------------------------------
### Fixed
- `pyaud toc` only creates one file
- Renames `plugins` to `pyaud_plugins` to avoid name collisions

[3.2.7](https://github.com/jshwi/pyaud/releases/tag/v3.2.7) - 2021-09-29
------------------------------------------------------------------------
### Fixed
- Pinned `black` due to beta version

[3.2.6](https://github.com/jshwi/pyaud/releases/tag/v3.2.6) - 2021-09-29
------------------------------------------------------------------------
### Fixed
- Relaxes requirement versions
- Argument for `where` (`setuptools.find_packages`) is now a `str`

[3.2.5](https://github.com/jshwi/pyaud/releases/tag/v3.2.5) - 2021-08-31
------------------------------------------------------------------------
### Fixed
- Fixes pattern matching when configuring file index exclusions
- Ensures all configs are loaded with `main`

[3.2.4](https://github.com/jshwi/pyaud/releases/tag/v3.2.4) - 2021-08-13
------------------------------------------------------------------------
### Fixed
- Docs/toc requirement changed to docs/conf.py from docs

[3.2.3](https://github.com/jshwi/pyaud/releases/tag/v3.2.3) - 2021-08-13
------------------------------------------------------------------------
### Fixed
- Fixes `pyaud whitelist`: reverts to using index with `reduce`

[3.2.2](https://github.com/jshwi/pyaud/releases/tag/v3.2.2) - 2021-08-13
------------------------------------------------------------------------
### Fixed
- Prevent duplicates in index such as with unmerged trees

[3.2.1](https://github.com/jshwi/pyaud/releases/tag/v3.2.1) - 2021-08-12
------------------------------------------------------------------------
### Fixed
- Prevents `get_packages` from returning dot-separated subdirectories

[3.2.0](https://github.com/jshwi/pyaud/releases/tag/v3.2.0) - 2021-08-12
------------------------------------------------------------------------
### Added
- Adds option to set `packages["name"]: str` in config
- Adds `packages["exclude"]: List[str]` to config
- Adds `load_namespace` to `__all__
- Adds `__all__` to `plugins`

### Changed
- Updates package resolution to allow for multiple packages
- Allows variable message for `PythonPackageNotFoundError`
- Moves `pyaud._environ.package` → `pyaud._utils.package`
- Changes default names from primary package to name of project root

### Fixed
- Fixes `pyaud whitelist`: Reduces false-positives
- Updates nested config changes for global config
- Installs missing stubs automatically for `mypy==0.910`

### Security
- Upgrades package requirements

[3.1.0](https://github.com/jshwi/pyaud/releases/tag/v3.1.0) - 2021-07-27
------------------------------------------------------------------------
### Added
- Adds `pyaud.exceptions.CommandNotFoundError`
- Adds `pyaud.exceptions.PythonPackageNotFoundError`
- Adds `pyaud.exceptions.NotARepositoryError`
- Adds all git commands to `pyaud.git`

### Changed
- `pyblake2.blake2b` → `hashlib.blake2b`

[3.0.3](https://github.com/jshwi/pyaud/releases/tag/v3.0.3) - 2021-07-26
------------------------------------------------------------------------
### Fixed
- Reduces indexing time

[3.0.2](https://github.com/jshwi/pyaud/releases/tag/v3.0.2) - 2021-07-25
------------------------------------------------------------------------
### Fixed
- Fixes `pyaud format-str`

[3.0.1](https://github.com/jshwi/pyaud/releases/tag/v3.0.1) - 2021-07-24
------------------------------------------------------------------------
### Deprecated
- `pyaud.files.args(reduce=True)` is deprecated

### Fixed
- Prevents packaged plugins from indexing unversioned files

[3.0.0](https://github.com/jshwi/pyaud/releases/tag/v3.0.0) - 2021-07-17
------------------------------------------------------------------------
### Added
- Adds `pyaud.__all__`
- Adds `pyaud.plugins.FixFile` abstract base class
- Adds `pyaud.plugins.Write` abstract base class
- Adds `pyaud.plugins.Parametrize` abstract base class
- Adds `pyaud.plugins.Action` abstract base class
- Adds `pyaud.plugins.Fix` abstract base class
- Adds `pyaud.plugins.Audit` abstract base class
- Adds `pyaud.utils.files.args`
- Adds `plugins`
- Adds `pyaud.exceptions`
- Adds `pyaud.plugins`
- Adds `pyaud.objects`
- Adds `pyaud.main`
- Adds `pyaud.utils.Subprocess.args`

### Changed
- `pyaud.plugins._plugins` not for external api, `@register` decorator only
- `pyaud.plugins` → `pyaud.plugins._plugins` (helper functions added)
- `pyaud.utils` → `pyaud._utils`
- `pyaud.objects` → `pyaud._objects`
- `pyaud.main` → `pyaud._main`
- `pyaud.environ` → `pyaud._environ`
- `pyaud.utils.tree` → `pyaud.utils.files`
- `pyaud.main.audit` → `plugins.modules.audit`
- `pyaud.utils.tree` → `pyaud.utils.files`
- Moves plugin specific utilities to `plugins.utils`
- `pyaud.main.audit` → `plugins.modules.audit`
- `pyaud.modules` → `plugins.modules`

### Fixed
- `pyaud toc` sorts modules alphabetically so `package.__init__.py` is on top
- Adds positional arguments to `@check_command`
- Fixes errors raised for missing project files
- Fixes loading of `PYAUD_GH_NAME`

### Removed
- Removes support for ini config
- Removes loglevel constants from `pyaud.config`

[2.0.0](https://github.com/jshwi/pyaud/releases/tag/v2.0.0) - 2021-06-28
------------------------------------------------------------------------
### Added
- Adds configuration for `pyaud audit`
- Add: adds `-f/--fix` flag
- Adds `--rcfile RCFILE` flag
- Adds `indexing` key to config
- Adds `logging` key to config
- Adds `generate-rcfile` positional argument
- Adds support for Toml config
- Adds `docformatter` for docstring formatting
- Adds `flynt` for f-string formatting
- `PyAuditError` added for non-subprocess errors

### Changed
- Sets static values as constants
- Updates help for commandline
- Improves `pyaud format` error handling
- Sets `Black` loglevel to debug
- Sets `Git` loglevel to debug

### Deprecated
- Support for ini config is deprecated

### Fixed
- Restores configfile if it becomes corrupted
- Applies exclusions to non-reduced file paths
- `pyaud imports` displays success message
- `pyaud whitelist` sorts whitelist.py
- `readmetester` produces color output when `colorama` is installed
- Excludes setup.py from indexing by default
- Adds git environment variables to `Git`
- Moves console entry point to `pyaud.__main__`
- Patches "$HOME" for setting ~/.gitconfig in tests

### Removed
- Remove: removes `---path PATH` flag
- Remove: removes `PyaudEnvironmentError` for `EnvironmentError
- Removes json from `Environ.__repr__`

[1.3.0](https://github.com/jshwi/pyaud/releases/tag/v1.3.0) - 2021-03-18
------------------------------------------------------------------------
### Added
- Adds ``pyaud imports`` utilising ``isort``
- Adds ``pyaud readme`` utilising ``readmetester``

[1.2.2](https://github.com/jshwi/pyaud/releases/tag/v1.2.2) - 2021-03-17
------------------------------------------------------------------------
### Fixed
- Updates object-colors to the latest major release to prevent version conflicts with other packages

[1.2.1](https://github.com/jshwi/pyaud/releases/tag/v1.2.1) - 2021-02-06
------------------------------------------------------------------------
### Fixed
- Updates README to include ``-v/--verbose`` option
- Fixes ``pypi`` badge in README
- Updates .bump2version.cfg to ensure only this package gets bumped in setup.py

[1.2.0](https://github.com/jshwi/pyaud/releases/tag/v1.2.0) - 2021-02-06
------------------------------------------------------------------------
### Added
- Adds ``L0G_LEVEL`` environment variable to permanently set default loglevel to other from ``INFO``
- Adds ``-v/--verbose`` logging option to incrementally reduce loglevel from default
- Adds debugging logger to ``Subprocess``
- Logs failed ``Subprocess`` returncode
- Logs ``Environ.__repr__`` as ``DEBUG`` when running tests

### Changed
- ``Environ.__repr__`` as json
- Lowers loglevel for internal ``git`` actions from ``INFO`` to ``DEBUG``

### Fixed
- Fixes ``pylint --output-format=colorize`` when ``colorama`` is installed
- ``coverage`` only analyses directories so ``Module was never imported`` no longer sent to logs

[1.1.1](https://github.com/jshwi/pyaud/releases/tag/v1.1.1) - 2021-02-01
------------------------------------------------------------------------
### Added
- Adds ``twine`` to dev-packages

### Changed
- Adds REAL_REPO constant

### Fixed
- Removes useless environment variables
- Prevents environment variables from being set without prefix
- Ensures dest is always last argument for ``git clone``
- Ensures ``-p/--path`` argument always returns an absolute path
- Fixes failing build
- Ensures cache and reports are saved to project root

[1.1.0](https://github.com/jshwi/pyaud/releases/tag/v1.1.0) - 2021-01-30
------------------------------------------------------------------------
### Changed
- No longer analyses unversioned files

[1.0.0](https://github.com/jshwi/pyaud/releases/tag/v1.0.0) - 2021-01-26
------------------------------------------------------------------------
### Added
- Initial Release
