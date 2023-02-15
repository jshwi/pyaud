"""
pyaud.plugins
=============

Main module used for public API.
"""
from __future__ import annotations

import functools as _functools
import importlib as _importlib
import inspect as _inspect
import os as _os
import pkgutil as _pkgutil
import re as _re
import sys as _sys
import typing as _t
from abc import abstractmethod as _abstractmethod
from subprocess import CalledProcessError as _CalledProcessError

from spall import Subprocess as _Subprocess

from . import messages as _messages
from ._cache import FileCacher as _FileCacher
from ._config import TempEnvVar as _TempEnvVar
from ._objects import NAME as _NAME
from ._objects import BasePlugin as _BasePlugin
from ._objects import MutableMapping as _MutableMapping
from ._objects import colors as _colors
from ._objects import files as _files
from .exceptions import NameConflictError as _NameConflictError


class Subprocesses(_MutableMapping):
    """Instantiate collection of ``Subprocess`` objects.

    :param args: Commands to create subprocesses from.
    """

    def __init__(self, args: list[str]) -> None:
        super().__init__()
        for arg in args:
            self[arg] = _Subprocess(arg)


class _CheckCommand:
    @staticmethod
    def _announce_completion(success_message: str, returncode: int) -> None:
        if returncode:
            _colors.red.bold.print(
                _messages.FAILED.format(returncode=returncode),
                file=_sys.stderr,
            )
        else:
            _colors.green.bold.print(success_message)

    @classmethod
    def file(cls, func: _t.Callable[..., int]) -> _t.Callable[..., int]:
        """Run the routine common with single file fixes.

        :param func: Function to decorate.
        :return: Wrapped function.
        """

        @_functools.wraps(func)
        def _wrapper(*args: str, **kwargs: bool) -> int:
            returncode = func(*args, **kwargs)
            cls._announce_completion(_messages.SUCCESS_FILE, returncode)
            return returncode

        return _wrapper

    @classmethod
    def files(cls, func: _t.Callable[..., int]) -> _t.Callable[..., int]:
        """Run the routine common with multiple source file fixes.

        :param func: Function to decorate.
        :return: Wrapped function.
        """

        @_functools.wraps(func)
        def _wrapper(*args: str, **kwargs: bool) -> int:
            returncode = 0
            if not _files.reduce():
                print(_messages.NO_FILES_FOUND)
            else:
                returncode = func(*args, **kwargs)
                cls._announce_completion(
                    _messages.SUCCESS_FILES.format(len=len(_files)), returncode
                )

            return returncode

        return _wrapper


# wrap plugin with a hashing function
def _cache_wrapper(
    cls: type[Plugin], func: _t.Callable[..., int]
) -> _t.Callable[..., int]:
    @_functools.wraps(func)
    def _wrapper(*args: str, **kwargs: bool) -> int:
        if not kwargs.get("no_cache", False):
            _file_cacher = _FileCacher(cls, func, *args, **kwargs)
            if cls.cache_file is not None:
                return _file_cacher.file()

            if cls.cache and _files:
                return _file_cacher.files()

        return func(*args, **kwargs)

    return _wrapper


class Plugin(_BasePlugin):
    """Base class of all plugins.

    Raises ``TypeError`` if registered directly.

    Contains the name attribute assigned upon registration.

    Subprocesses are stored in the ``subprocess`` dict object

    :param name: Name assigned to plugin via ``@register`` decorator.
    """

    def __new__(cls, name: str) -> Plugin:  # pylint: disable=unused-argument
        cls.__call__ = _cache_wrapper(cls, cls.__call__)  # type: ignore
        return super().__new__(cls)

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

    @_CheckCommand.files
    def __call__(self, *args: str, **kwargs: bool) -> int:
        with _TempEnvVar(_os.environ, **self.env):
            try:
                return self.audit(*args, **kwargs)

            except _CalledProcessError:
                return 1


#: Blueprint for writing audit and fix plugins.
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
        with _TempEnvVar(_os.environ, **self.env):
            try:
                returncode = self.audit(*args, **kwargs)

            except _CalledProcessError:
                returncode = 1

        if returncode:
            if kwargs.get("fix", False):
                return self.fix(**kwargs)

            return 1

        return returncode


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

    @_CheckCommand.file
    def __call__(self, *args: str, **kwargs: bool) -> int:
        return super().__call__(*args, **kwargs)


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

    @_CheckCommand.files
    def __call__(self, *args: str, **kwargs: bool) -> int:
        return super().__call__(*args, **kwargs)


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
        with _TempEnvVar(_os.environ, **self.env):
            try:
                return self.action(*args, **kwargs)

            except _CalledProcessError:
                return 1


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
        if _re.match("^pyaud[-_].*$", name):
            _importlib.import_module(name)
