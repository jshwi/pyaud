"""
pyaud.plugins
=============

Main module used for public API.
"""
from __future__ import annotations

import hashlib as _hashlib
import importlib as _importlib
import inspect as _inspect
import os as _os
import pkgutil as _pkgutil
import re as _re
import sys as _sys
import typing as _t
from abc import ABC as _ABC
from abc import abstractmethod as _abstractmethod
from pathlib import Path as _Path
from subprocess import CalledProcessError as _CalledProcessError
from types import TracebackType as _TracebackType

import git as _git
from spall import Subprocess as _Subprocess

from . import messages as _messages
from ._objects import JSONIO as _JSONIO
from ._objects import NAME as _NAME
from ._objects import MutableMapping as _MutableMapping
from ._objects import colors as _colors
from ._objects import files as _files
from ._version import __version__
from .exceptions import NameConflictError as _NameConflictError

IMPORT_RE = _re.compile("^pyaud[-_].*$")

CACHE_FILE = "files.json"
FALLBACK = "fallback"
UNCOMMITTED = "uncommitted"


class Subprocesses(_MutableMapping):
    """Instantiate collection of ``Subprocess`` objects.

    :param args: Commands to create subprocesses from.
    """

    def __init__(self, args: list[str]) -> None:
        super().__init__()
        for arg in args:
            self[arg] = _Subprocess(arg)


# store index and ensure it's in its original state on exit
class _IndexedState:
    def __init__(self) -> None:
        self._length = len(_files)
        self._index = list(_files)
        self._restored = False

    @property
    def length(self) -> int:
        """Number of files for run."""
        return self._length

    def __enter__(self) -> _IndexedState:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: _TracebackType | None,
    ) -> None:
        if not self._restored:
            _files.extend(self._index)

    def restore(self) -> None:
        """Restore the original state of index."""
        self._restored = True
        _files.extend(self._index)


# persistent data object
class _HashMapping(_JSONIO):
    def __init__(self, cls: type[BasePlugin]) -> None:
        super().__init__(
            _Path(_os.environ["PYAUD_CACHE"]) / __version__ / CACHE_FILE
        )
        self._project = _Path.cwd().name
        self._cls = str(cls)
        self._repo = _git.Repo(_Path.cwd())
        try:
            self._commit = self._repo.git.rev_parse("HEAD")
        except _git.GitCommandError:
            self._commit = FALLBACK

        if self._repo.git.status("--short"):
            self._commit = f"{UNCOMMITTED}-{self._commit}"

        super().read()
        project_obj = self.get(self._project, {})
        fallback = project_obj.get(FALLBACK, {})
        project_obj[self._commit] = project_obj.get(self._commit, fallback)
        self._session = project_obj[self._commit].get(self._cls, {})

    def match_file(self, path: _Path) -> bool:
        """Match selected class against a file relevant to it.

        :param path: Path to the file to check if it has changed.
        :return: Is the file a match (not changed)? True or False.
        """
        relpath = str(path.relative_to(_Path.cwd()))
        newhash = _hashlib.new(  # type: ignore
            "md5", path.read_bytes(), usedforsecurity=False
        ).hexdigest()
        return newhash == self._session.get(relpath)

    def save_hash(self, path: _Path) -> None:
        """Populate file hash.

        :param path: Path to hash.
        """
        relpath = str(path.relative_to(_Path.cwd()))
        if path.is_file():
            newhash = _hashlib.new(  # type: ignore
                "md5", path.read_bytes(), usedforsecurity=False
            ).hexdigest()
            self._session[relpath] = newhash
        else:
            if relpath in self._session:
                del self._session[relpath]

    def write(self) -> None:
        """Write data to file."""
        cls = {self._cls: dict(self._session)}
        self[self._project] = {FALLBACK: cls, self._commit: cls}
        super().write()


# temporarily set a mutable mapping key-value pair
class _TempEnvVar:
    def __init__(self, obj: _t.MutableMapping, **kwargs: str) -> None:
        self._obj = obj
        self._default = {k: obj.get(k) for k in kwargs}
        self._obj.update(kwargs)

    def __enter__(self) -> _TempEnvVar:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: _TracebackType | None,
    ) -> None:
        for key, value in self._default.items():
            if value is None:
                try:
                    del self._obj[key]
                except KeyError:
                    # in the case that key gets deleted within context
                    pass
            else:
                self._obj[key] = self._default[key]


# handle caching of a single file
def _cache_files_wrapper(
    cls_call: _t.Callable[..., int], self: Plugin, *args: str, **kwargs: bool
) -> int:
    returncode = 0
    hashed = _HashMapping(self.__class__)
    with _IndexedState() as state:
        for file in list(_files):
            if hashed.match_file(file):
                _files.remove(file)
            else:
                if self.cache_all:
                    state.restore()
                    break

        if not _files and state.length:
            _colors.green.bold.print(_messages.NO_FILES_CHANGED)
        else:
            returncode = cls_call(self, *args, **kwargs)

        if not returncode:
            for path in _files:
                hashed.save_hash(path)

            hashed.write()

    return returncode


# handle caching of a repo's python files
def _cache_file_wrapper(
    cls_call: _t.Callable[..., int], self: Plugin, *args: str, **kwargs: bool
) -> int:
    hashed = _HashMapping(self.__class__)
    returncode = 0
    file = self.cache_file
    if file is not None:
        path = _Path.cwd() / file
        returncode = cls_call(self, *args, **kwargs)
        if returncode:
            hashed.save_hash(path)
            hashed.write()
            return returncode

        if not returncode and path.is_file() and hashed.match_file(path):
            _colors.green.print(_messages.NO_FILE_CHANGED)
            return 0

        hashed.save_hash(path)
        hashed.write()

    return returncode


# wrap plugin with a hashing function
def _cache_wrapper(cls: type[Plugin]) -> type[Plugin]:
    cls_call = cls.__call__

    def __call__(self: Plugin, *args: str, **kwargs: bool) -> int:
        if not kwargs.get("no_cache", False):
            if cls.cache_file is not None:
                return _cache_file_wrapper(cls_call, self, *args, **kwargs)

            if cls.cache and _files:
                return _cache_files_wrapper(cls_call, self, *args, **kwargs)

        return cls_call(self, *args, **kwargs)

    setattr(cls, cls.__call__.__name__, __call__)
    return cls


# run the routine common with single file fixes
def _file_wrapper(cls: PluginType) -> PluginType:
    cls_call = cls.__call__

    def __call__(self, *args: str, **kwargs: bool) -> int:
        returncode = cls_call(self, *args, **kwargs)
        if returncode:
            _colors.red.bold.print(
                _messages.FAILED.format(returncode=returncode),
                file=_sys.stderr,
            )
        else:
            _colors.green.bold.print(_messages.SUCCESS_FILE)

        return returncode

    setattr(cls, cls.__call__.__name__, __call__)
    return cls


# run the routine common with multiple source file fixes
def _files_wrapper(cls: PluginType) -> PluginType:
    cls_call = cls.__call__

    def __call__(self, *args: str, **kwargs: bool) -> int:
        returncode = 0
        if _files.reduce():
            returncode = cls_call(self, *args, **kwargs)
            if returncode:
                _colors.red.bold.print(
                    _messages.FAILED.format(returncode=returncode),
                    file=_sys.stderr,
                )
            else:
                _colors.green.bold.print(
                    _messages.SUCCESS_FILES.format(len=len(_files))
                )

        return returncode

    setattr(cls, cls.__call__.__name__, __call__)
    return cls


def _fix_wrapper(cls: PluginType) -> PluginType:
    cls_call = cls.__call__

    def __call__(self, *args: str, **kwargs: bool) -> int:
        returncode = cls_call(self, *args, **kwargs)
        if returncode:
            if kwargs.get("fix", False):
                return self.fix(**kwargs)

            return 1

        return returncode

    setattr(cls, cls.__call__.__name__, __call__)
    return cls


def _env_wrapper(cls: PluginType) -> PluginType:
    cls_call = cls.__call__

    def __call__(self, *args: str, **kwargs: bool) -> int:
        with _TempEnvVar(_os.environ, **self.env):
            try:
                return cls_call(self, *args, **kwargs)

            except _CalledProcessError:
                return 1

    setattr(cls, cls.__call__.__name__, __call__)
    return cls


class BasePlugin(_ABC):  # pylint: disable=too-few-public-methods
    """Base type for all plugins."""

    #: If set to True then indexed files will be monitored for change.
    cache = False

    #: Only matters if ``cache`` is set to True.
    #: If False (default) then audit will cache on a file-by-file basis.
    #: If True, then no changes can be made to any file for a cache-hit
    #: to be valid.
    cache_all = False

    #: set a single cache file for plugin subclass.
    cache_file: _t.Optional[_t.Union[str, _Path]] = None


class Plugin(BasePlugin):
    """Base class of all plugins.

    Raises ``TypeError`` if registered directly.

    Contains the name attribute assigned upon registration.

    Subprocesses are stored in the ``subprocess`` dict object

    :param name: Name assigned to plugin via ``@register`` decorator.
    """

    def __new__(cls, name: str) -> Plugin:  # pylint: disable=unused-argument
        return super().__new__(_cache_wrapper(cls))

    def __init__(self, name: str) -> None:
        self._name = name
        self._subprocess = Subprocesses(self.exe)

    @property
    def env(self) -> dict[str, str]:
        """Return environment which will remain active for run."""
        return {}

    @property
    def exe(self) -> list[str]:
        """List of executables to add to ``subprocess`` dict."""
        return []

    @property
    def name(self) -> str:
        """Name of the plugin."""
        return self._name

    @property
    def subprocess(self) -> Subprocesses:
        """Collection of ``Subprocess`` objects."""
        return self._subprocess

    def __call__(self, *args: str, **kwargs: bool) -> int:
        """Enables calling of all plugin instances."""
        return 0


@_env_wrapper
@_files_wrapper
class Audit(Plugin):
    """Blueprint for writing audit-only plugins.

    Audit will be called from here.

    Run within context of defined environment variables.
    If no environment variables are defined nothing will change.

    :raises CalledProcessError: Will always be raised if something fails
        that is not to do with the audit condition. Will be excepted and
        reraised as ``AuditError`` if the audit fails.
    :raises AuditError: Raised from ``CalledProcessError`` if
        audit fails.
    :return: If any error has not been raised for any reason int object
        must be returned, from subprocess or written, to notify call
        whether process has succeeded or failed. No value will actually
        return from __call__ as it will be passed to the decorator.
    """

    @_abstractmethod
    def audit(self, *args: str, **kwargs: bool) -> int:
        """All audit logic to be written within this method.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify call whether process has succeeded or failed.
        """

    def __call__(self, *args: str, **kwargs: bool) -> int:
        return self.audit(*args, **kwargs)


#: Blueprint for writing audit and fix plugins.
@_fix_wrapper
@_env_wrapper
class BaseFix(Audit):
    """Blueprint for writing audit and fix plugins.

    Audit will be called from here.

    Called within context of defined environment variables.
    If no environment variables are defined nothing will change.

    If audit fails and the ``-f/--fix`` flag is passed to the
    commandline the ``fix`` method will be called within the
    ``CalledProcessError`` try-except block.

    If ``-f/--fix`` and the audit fails the user is running the
    audit only and will raise an ``AuditError``.

    :raises CalledProcessError: Will always be raised if something fails
        that is not to do with the audit condition. Will be excepted and
        reraised as ``AuditError`` if the audit fails and ``-f/--fix``
        is not passed to the commandline.
    :raises AuditError: Raised from ``CalledProcessError`` if audit
        fails and ``-f/--fix`` flag if not passed to the commandline.
    :return: If any error has not been raised for any reason int object
        must be returned, from subprocess or written, to notify call
        whether process has succeeded or failed. No value will actually
        return from __call__ as it will be passed to the decorator.
    """

    @_abstractmethod
    def audit(self, *args: str, **kwargs: bool) -> int:
        """All audit logic to be written within this method.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify __call__ whether process has succeeded or failed. If
            non-zero exist is returned and ``-f/--fix`` has been passed
            to the commandline run the ``fix`` method, otherwise raise
            ``AuditError``.
        """

    @_abstractmethod
    def fix(self, *args: str, **kwargs: bool) -> int:
        """Run if audit fails but only if running a fix.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify __call__ whether process has succeeded or failed.
        """

    def __call__(self, *args: str, **kwargs: bool) -> int:
        return self.audit(*args, **kwargs)


@_file_wrapper
class Fix(BaseFix):
    """Blueprint for writing audit and fix plugins for single files.

    Announce file status.

    :raises CalledProcessError: Will always be raised if something fails
        that is not to do with the audit condition. Will be excepted and
        reraised as ``AuditError`` if the audit fails and ``-f/--fix``
        is not passed to the commandline.
    :raises AuditError: Raised from ``CalledProcessError`` if audit
        fails and ``-f/--fix`` flag if not passed to the commandline.
    :return: If any error has not been raised for any reason int object
        must be returned, from subprocess or written, to notify call
        whether process has succeeded or failed. No value will actually
        return from __call__ as it will be passed to the decorator.
    """

    @_abstractmethod
    def audit(self, *args: str, **kwargs: bool) -> int:
        """All audit logic to be written within this method.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify __call__ whether process has succeeded or failed. If
            non-zero exist is returned and ``-f/--fix`` has been passed
            to the commandline run the ``fix`` method, otherwise raise
            ``AuditError``.
        """

    @_abstractmethod
    def fix(self, *args: str, **kwargs: bool) -> int:
        """Run if audit fails but only if running a fix.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify __call__ whether process has succeeded or failed.
        """


@_files_wrapper
class FixAll(BaseFix):
    """Blueprint for writing audit and fix plugins for Python files.

    Announce Python file status.

    :raises CalledProcessError: Will always be raised if something fails
        that is not to do with the audit condition. Will be excepted and
        reraised as ``AuditError`` if the audit fails and ``-f/--fix``
        is not passed to the commandline.
    :raises AuditError: Raised from ``CalledProcessError`` if audit
        fails and ``-f/--fix`` flag if not passed to the commandline.
    :return: If any error has not been raised for any reason int object
        must be returned, from subprocess or written, to notify call
        whether process has succeeded or failed. No value will actually
        return from __call__ as it will be passed to the decorator.
    """

    @_abstractmethod
    def audit(self, *args: str, **kwargs: bool) -> int:
        """All audit logic to be written within this method.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify __call__ whether process has succeeded or failed. If
            non-zero exist is returned and ``-f/--fix`` has been passed
            to the commandline run the ``fix`` method, otherwise raise
            ``AuditError``.
        """

    @_abstractmethod
    def fix(self, *args: str, **kwargs: bool) -> int:
        """Run if audit fails but only if running a fix.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify __call__ whether process has succeeded or failed.
        """


@_env_wrapper
class Action(Plugin):
    """Blueprint for writing generic plugins.

    Called within context of defined environment variables.
    If no environment variables are defined nothing will change.

    :raises CalledProcessError: Will always be raised if something fails
        that is not to do with the action condition. Will be excepted
        and reraised as ``AuditError`` if the action fails.
    :raises AuditError: Raised from ``CalledProcessError`` if action
        fails.
    :return: Any value and type can be returned.
    """

    @_abstractmethod
    def action(self, *args: str, **kwargs: bool) -> int:
        """All logic to be written within this method.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: Any value and type can be returned.
        """

    def __call__(self, *args: str, **kwargs: bool) -> int:
        return self.action(*args, **kwargs)


class Parametrize(Plugin):
    """Define a list of strings to call multiple plugins.

    :raises CalledProcessError: Will always be raised if something fails
        that is not to do with the called plugin's condition. Will be
        excepted and reraised as ``AuditError`` if the called plugin
        fails  and the called plugin does not specify a ``fix`` method
        or the ``-f/--fix`` flag is not passed to the commandline.
    :raises AuditError: Raised from ``CalledProcessError`` if called
        plugin fails and no ``fix`` method is specified or the
        ``-f/--fix`` flag is not passed to the commandline.
    """

    @_abstractmethod
    def plugins(self) -> list[str]:
        """List of plugin names to run.

        :return: List of plugin names, as defined in ``@register``.
        """

    def __call__(self, *args: str, **kwargs: bool) -> int:
        returncode = 0
        for name in self.plugins():
            _colors.cyan.bold.print(f"\n{_NAME} {name}")
            if _plugins[name](*args, **kwargs):
                returncode = 1

        return returncode


# array of plugins
PLUGINS = [Audit, BaseFix, Fix, FixAll, Action, Parametrize]

# array of plugin names
PLUGIN_NAMES = [t.__name__ for t in PLUGINS]

# array of plugin types before instantiation
PluginType = _t.Union[
    _t.Type[Audit],
    _t.Type[BaseFix],
    _t.Type[Fix],
    _t.Type[FixAll],
    _t.Type[Action],
    _t.Type[Parametrize],
]

# array of plugin types after instantiation
PluginInstance = _t.Union[Audit, BaseFix, Fix, FixAll, Action, Parametrize]


class Plugins(_MutableMapping):
    """Holds registered plugins.

    Instantiate plugin on running __setitem__.

    :raise NameConflictError: If name of registered plugin is not
        unique.
    :raise TypeError: If non plugin type registered.
    """

    def __setitem__(self, name: str, plugin: PluginType) -> None:
        # only unique names to be set in `plugins` object
        # if name is not unique raise `NameConflictError`
        if name in self:
            raise _NameConflictError(plugin.__name__, name)

        mro = tuple(p.__name__ for p in _inspect.getmro(plugin))
        if not hasattr(plugin, "__bases__") or not any(
            i in PLUGIN_NAMES for i in mro
        ):
            raise TypeError(
                _messages.TYPE_ERROR.format(
                    valid=", ".join(PLUGIN_NAMES), invalid=mro
                )
            )

        super().__setitem__(name, plugin(name))


_plugins = Plugins()


def _name_plugin(plugin: PluginType) -> str:
    parts = _re.findall("[A-Z][^A-Z]*", plugin.__name__)
    return "-".join(parts).lower()


def register(name: str | None = None) -> _t.Callable[[PluginType], PluginType]:
    """Register subclassed plugin to collection.

    If name is not provided a name will be assigned automatically.

    :param name: Name to register plugin as.
    :return: Return registered plugin to call.
    """

    def _register(plugin: PluginType) -> PluginType:
        _plugins[name or _name_plugin(plugin)] = plugin
        return plugin

    return _register


def mapping() -> dict[str, PluginInstance]:
    """Get dict of named keys and their corresponding plugin values.

    :return: Mapping of plugins and their unique names.
    """
    return dict(_plugins)


def registered() -> list[str]:
    """Get list of registered plugins.

    :return: List of registered plugins.
    """
    return sorted(list(_plugins))


def get(name: str, default: str | None = None) -> PluginInstance:
    """Get plugins by name.

    :param name: Unique name of plugin.
    :param default: Default plugin if name not valid.
    :return: Callable plugin instance.
    """
    try:
        return _plugins[name]
    except KeyError:
        _colors.red.print(
            _messages.NOT_FOUND.format(name=name), file=_sys.stderr
        )
        return _plugins[default]


def load() -> None:
    """Import all package prefixed with ``pyaud[-_]``."""
    for _, name, _ in _pkgutil.iter_modules():
        if IMPORT_RE.match(name):
            _importlib.import_module(name)
