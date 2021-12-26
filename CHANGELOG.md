Changelog
=========
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

[Unreleased](https://github.com/jshwi/pyaud/compare/v3.2.10...HEAD)
------------------------------------------------------------------------
### Added
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
