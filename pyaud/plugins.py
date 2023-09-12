"""
pyaud.plugins
=============

Main module used for public API.
"""
from __future__ import annotations as _annotations

import hashlib as _hashlib
import importlib as _importlib
import inspect as _inspect
import json as _json
import pkgutil as _pkgutil
import re as _re
import sys as _sys
import typing as _t
from abc import ABC as _ABC
from abc import abstractmethod as _abstractmethod
from pathlib import Path as _Path
from subprocess import CalledProcessError as _CalledProcessError

import git as _git

from . import _cachedir
from . import messages as _messages
from ._files import files as _files
from ._objects import NAME as _NAME
from ._objects import colors as _colors
from .exceptions import NameConflictError as _NameConflictError

IMPORT_RE = _re.compile("^pyaud[-_].*$")


# persistent data object
class _HashMapping:
    FALLBACK = "fallback"

    def __init__(self, cls: type[BasePlugin]) -> None:
        self._head = "uncommitted"
        self._cls = str(cls)
        self._path = _cachedir.PATH / "files.json"
        self._dict: dict[str, _t.Any] = {}
        self._cwd = _Path.cwd()
        repo = _git.Repo(self._cwd)
        if self._path.is_file():
            try:
                self._dict.update(_json.loads(self._path.read_text()))

                # remove cache of commits with no revision
                commits = repo.git.rev_list(all=True).splitlines()
                for commit in dict(self._dict):
                    if commit not in commits and commit != self.FALLBACK:
                        del self._dict[commit]
            except _json.decoder.JSONDecodeError:
                pass

        if not repo.git.status(short=True):
            try:
                self._head = repo.git.rev_parse("HEAD")
            except _git.GitCommandError:
                self._head = self.FALLBACK

        self._session = self._dict.get(
            self._head, self._dict.get(self.FALLBACK, {})
        ).get(self._cls, {})

    def match_file(self, path: _Path) -> bool:
        """Match selected class against a file relevant to it.

        :param path: Path to the file to check if it has changed.
        :return: Is the file a match (not changed)? True or False.
        """
        relpath = str(path.relative_to(self._cwd))
        newhash = _hashlib.new(  # type: ignore
            "md5", path.read_bytes(), usedforsecurity=False
        ).hexdigest()
        return newhash == self._session.get(relpath)

    def save_hash(self, path: _Path) -> None:
        """Populate file hash.

        :param path: Path to hash.
        """
        relpath = str(path.relative_to(self._cwd))
        if path.is_file():
            newhash = _hashlib.new(  # type: ignore
                "md5", path.read_bytes(), usedforsecurity=False
            ).hexdigest()
            self._session[relpath] = newhash
        else:
            if relpath in self._session:
                del self._session[relpath]

        cls = {self._cls: self._session}
        self._nested_update(self._dict, {self.FALLBACK: cls, self._head: cls})
        self._path.write_text(_json.dumps(self._dict, separators=(",", ":")))

    def _nested_update(
        self, obj: dict[str, _t.Any], update: dict[str, _t.Any]
    ) -> dict[str, _t.Any]:
        # add to __setitem__ to ensure that no entire dict keys with
        # missing nested keys overwrite all other values
        # run recursively to cover all nested objects if value is a dict
        # if value is a str pass through ``Path.expanduser()`` to
        # translate paths prefixed with ``~/`` for ``/home/<user>``
        # if value is all else assign it to obj key
        # return obj for recursive assigning of nested dicts
        for key, value in update.items():
            if isinstance(value, dict):
                value = self._nested_update(obj.get(key, {}), value)

            elif isinstance(value, str):
                value = str(_Path(value).expanduser())

            obj[key] = value

        return obj


# handle caching of a single file
def _cache_files_wrapper(
    self: Plugin, cls_call: _t.Callable[..., int], *args: str, **kwargs: _t.Any
) -> int:
    returncode = 0
    hashed = _HashMapping(self.__class__)
    with _files.state() as state:
        for file in state:
            if hashed.match_file(file):
                _files.remove(file)
            else:
                if self.cache_all:
                    _files.restore()
                    break

        if not _files and len(state):
            _colors.green.bold.print(_messages.NO_FILES_CHANGED)
        else:
            returncode = cls_call(self, *args, **kwargs)

        if not returncode:
            for path in _files:
                hashed.save_hash(path)

    return returncode


# handle caching of a repo's python files
def _cache_file_wrapper(
    self: Plugin, cls_call: _t.Callable[..., int], *args: str, **kwargs: _t.Any
) -> int:
    hashed = _HashMapping(self.__class__)
    returncode = 0
    file = self.cache_file
    if file is not None:
        path = _Path.cwd() / file
        returncode = cls_call(self, *args, **kwargs)
        if returncode:
            hashed.save_hash(path)
            return returncode

        if not returncode and path.is_file() and hashed.match_file(path):
            _colors.green.print(_messages.NO_FILE_CHANGED)
            return 0

        hashed.save_hash(path)

    return returncode


# wrap plugin with a hashing function
def _cache_wrapper(cls: type[Plugin]) -> type[Plugin]:
    cls_call = cls.__call__

    def __call__(self: Plugin, *args: str, **kwargs: _t.Any) -> int:
        if not kwargs.get("no_cache", False):
            if cls.cache_file is not None:
                return _cache_file_wrapper(self, cls_call, *args, **kwargs)

            if cls.cache and _files:
                return _cache_files_wrapper(self, cls_call, *args, **kwargs)

        return cls_call(self, *args, **kwargs)

    setattr(cls, cls.__call__.__name__, __call__)
    return cls


# run the routine common with single file fixes
def _file_wrapper(cls: PluginType) -> PluginType:
    cls_call = cls.__call__

    def __call__(self, *args: str, **kwargs: _t.Any) -> int:
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

    def __call__(self, *args: str, **kwargs: _t.Any) -> int:
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

    def __call__(self, *args: str, **kwargs: _t.Any) -> int:
        returncode = cls_call(self, *args, **kwargs)
        if returncode:
            if kwargs.get("fix", False):
                return self.fix(**kwargs)

            return 1

        return returncode

    setattr(cls, cls.__call__.__name__, __call__)
    return cls


def _commandline_error_catcher(cls: PluginType) -> PluginType:
    cls_call = cls.__call__

    def __call__(self, *args: str, **kwargs: _t.Any) -> int:
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
    cache_file: str | _Path | None = None


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

    @property
    def name(self) -> str:
        """Name of the plugin."""
        return self._name

    def __call__(self, *args: str, **kwargs: _t.Any) -> int:
        """Enables calling of all plugin instances."""
        return 0


@_commandline_error_catcher
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
    def audit(self, *args: str, **kwargs: _t.Any) -> int:
        """All audit logic to be written within this method.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify call whether process has succeeded or failed.
        """

    def __call__(self, *args: str, **kwargs: _t.Any) -> int:
        return self.audit(*args, **kwargs)


#: Blueprint for writing audit and fix plugins.
@_fix_wrapper
@_commandline_error_catcher
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
    def audit(self, *args: str, **kwargs: _t.Any) -> int:
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
    def fix(self, *args: str, **kwargs: _t.Any) -> int:
        """Run if audit fails but only if running a fix.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify __call__ whether process has succeeded or failed.
        """

    def __call__(self, *args: str, **kwargs: _t.Any) -> int:
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
    def audit(self, *args: str, **kwargs: _t.Any) -> int:
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
    def fix(self, *args: str, **kwargs: _t.Any) -> int:
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
    def audit(self, *args: str, **kwargs: _t.Any) -> int:
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
    def fix(self, *args: str, **kwargs: _t.Any) -> int:
        """Run if audit fails but only if running a fix.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: If any error has not been raised for any reason int
            object must be returned, from subprocess or written, to
            notify __call__ whether process has succeeded or failed.
        """


@_commandline_error_catcher
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
    def action(self, *args: str, **kwargs: _t.Any) -> int:
        """All logic to be written within this method.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: Any value and type can be returned.
        """

    def __call__(self, *args: str, **kwargs: _t.Any) -> int:
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

    def __call__(self, *args: str, **kwargs: _t.Any) -> int:
        returncode = 0
        for name in self.plugins():
            _colors.cyan.bold.print(f"\n{_NAME} {name}")
            if _plugins[name](*args, **kwargs):
                returncode = 1

        return returncode


# array of plugins
PLUGINS = (Audit, BaseFix, Fix, FixAll, Action, Parametrize)

# array of plugin names
PLUGIN_NAMES = tuple(t.__name__ for t in PLUGINS)

# array of plugin types before instantiation
# this ensures correct typing, at least for PyCharm
# if the type taken and returned is simply the type `Plugin` then you
# may get a warning like the following:
#   Unresolved attribute reference 'action' for class 'Plugin'
PluginType = _t.Union[
    _t.Type[Audit],
    _t.Type[BaseFix],
    _t.Type[Fix],
    _t.Type[FixAll],
    _t.Type[Action],
    _t.Type[Parametrize],
]


class Plugins(_t.Dict[str, Plugin]):
    """Holds registered plugins.

    Instantiate plugin on running __setitem__.

    :raises NameConflictError: If name of registered plugin is not
        unique.
    :raises TypeError: If non plugin type registered.
    """


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
        plugin_name = name or _name_plugin(plugin)
        if plugin_name in _plugins:
            raise _NameConflictError(plugin.__name__, plugin_name)

        mro = tuple(p.__name__ for p in _inspect.getmro(plugin))
        if not hasattr(plugin, "__bases__") or not any(
            i in PLUGIN_NAMES for i in mro
        ):
            raise TypeError(
                _messages.TYPE_ERROR.format(
                    valid=", ".join(PLUGIN_NAMES), invalid=mro
                )
            )
        _plugins[plugin_name] = plugin(plugin_name)
        return plugin

    return _register


def mapping() -> dict[str, Plugin]:
    """Get dict of named keys and their corresponding plugin values.

    :return: Mapping of plugins and their unique names.
    """
    return dict(_plugins)


def registered() -> list[str]:
    """Get list of registered plugins.

    :return: List of registered plugins.
    """
    return sorted(list(_plugins))


def get(name: str) -> Plugin:
    """Get plugins by name.

    :param name: Unique name of plugin.
    :return: Callable plugin instance.
    """
    try:
        return _plugins[name]
    except KeyError:
        _colors.red.print(
            _messages.NOT_FOUND.format(name=name), file=_sys.stderr
        )
        return _plugins["modules"]


def load() -> None:
    """Import all package prefixed with ``pyaud[-_]``."""
    for _, name, _ in _pkgutil.iter_modules():
        if IMPORT_RE.match(name):
            _importlib.import_module(name)
