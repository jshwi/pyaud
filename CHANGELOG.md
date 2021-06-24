Changelog
=========
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

[Unreleased](https://github.com/jshwi/pyaud/compare/v1.3.0...HEAD)
------------------------------------------------------------------------
### Added
- Adds `indexing` key to config
- Adds `logging` key to config
- Adds `generate-rcfile` positional argument
- Adds support for Toml config
- Adds `docformatter` for docstring formatting
- Adds `flynt` for f-string formatting
- `PyAuditError` added for non-subprocess errors

### Changed
- Updates help for commandline
- Improves `pyaud format` error handling
- Sets `Black` loglevel to debug
- Sets `Git` loglevel to debug

### Deprecated
- Support for ini config is deprecated

### Fixed
- Applies exclusions to non-reduced file paths
- `pyaud imports` displays success message
- `pyaud whitelist` sorts whitelist.py
- `readmetester` produces color output when `colorama` is installed
- Excludes setup.py from indexing by default
- Adds git environment variables to `Git`
- Moves console entry point to `pyaud.__main__`
- Patches "$HOME" for setting ~/.gitconfig in tests

### Removed
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
