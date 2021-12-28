"""
pyaud.plugins
=============

Main module used for public API.
"""
from __future__ import annotations

import importlib as _importlib
import inspect as _inspect
import os as _os
import sys as _sys
import typing as _t
from abc import abstractmethod as _abstractmethod
from pathlib import Path as _Path
from subprocess import CalledProcessError as _CalledProcessError

from . import config as _config
from . import exceptions as _exceptions
from ._environ import environ as _environ
from ._indexing import HashCap as _HashCap
from ._indexing import files as _files
from ._objects import BasePlugin as _BasePlugin
from ._objects import MutableMapping as _MutableMapping
from ._subprocess import Subprocess as _Subprocess
from ._utils import colors as _colors
from ._wraps import ClassDecorator as _ClassDecorator
from ._wraps import check_command as _check_command

_plugin_paths: _t.List[_Path] = [
    _environ.DEFAULT_PLUGINS,
    _environ.SITE_PLUGINS,
]


class _SubprocessFactory(  # pylint: disable=too-many-ancestors
    _MutableMapping
):
    """Instantiate collection of ``Subprocess`` objects."""

    def __init__(self, args: _t.List[str]):
        super().__init__()
        for arg in args:
            self[arg] = _Subprocess(arg)


class Plugin(_BasePlugin):  # pylint: disable=too-few-public-methods
    """Base class of all plugins.

    Raises ``TypeError`` if registered directly.

    Contains the name attribute assigned upon registration.

    Subprocesses are stored in the ``subprocess`` dict object

    :param name: Name assigned to plugin via ``@register`` decorator.
    """

    def __new__(cls, name: str) -> Plugin:  # pylint: disable=unused-argument
        class_decorator = _ClassDecorator(cls)
        cls.__call__ = class_decorator.not_found(cls.__call__)  # type: ignore
        cls.__call__ = class_decorator.files(cls.__call__)  # type: ignore
        cls.__call__ = class_decorator.time(cls.__call__)  # type: ignore
        return super().__new__(cls)

    def __init__(self, name: str) -> None:
        self.name = name
        self.subprocess = _SubprocessFactory(self.exe)

    def __deepcopy__(self, name: str) -> Plugin:
        return self

    @staticmethod
    def audit_error() -> _exceptions.AuditError:
        """Raise if checks have failed.

        :return: AuditError instantiated with error message.
        """
        return _exceptions.AuditError(" ".join(_sys.argv))

    @property
    def env(self) -> _t.Dict[str, str]:
        """Return environment which will remain active for run.

        :return: Dict containing any number of str keys and
            corresponding str values.
        """
        return {}

    @property
    def exe(self) -> _t.List[str]:
        """List of executables to add to ``subprocess`` dict.

        :return: List of str object to assign to subprocesses
        """
        return []

    def __call__(self, *args: str, **kwargs: bool) -> _t.Any:
        """Enables calling of all plugin instances."""


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

    @_check_command
    def __call__(self, *args: str, **kwargs: bool) -> int:
        with _config.TempEnvVar(_os.environ, **self.env):
            try:
                return self.audit(*args, **kwargs)

            except _CalledProcessError as err:
                raise self.audit_error() from err


class Fix(Audit):
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

    @_check_command
    def __call__(self, *args: str, **kwargs: bool) -> _t.Any:
        with _config.TempEnvVar(_os.environ, **self.env):
            try:
                return self.audit(*args, **kwargs)

            except _CalledProcessError as err:
                if kwargs.get("fix", False):
                    return self.fix(**kwargs)

                raise self.audit_error() from err


class Action(Plugin):  # pylint: disable=too-few-public-methods
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
    def action(self, *args: str, **kwargs: bool) -> _t.Any:
        """All logic to be written within this method.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: Any value and type can be returned.
        """

    def __call__(self, *args: str, **kwargs: bool) -> _t.Any:
        with _config.TempEnvVar(_os.environ, **self.env):
            try:
                return self.action(*args, **kwargs)

            except _CalledProcessError as err:
                raise self.audit_error() from err


class Parametrize(Plugin):  # pylint: disable=too-few-public-methods
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
    def plugins(self) -> _t.List[str]:
        """List of plugin names to run.

        :return: List of plugin names, as defined in ``@register``.
        """

    def __call__(self, *args: str, **kwargs: bool) -> None:
        for name in self.plugins():
            _colors.cyan.bold.print(f"\n{_environ.NAME} {name}")
            _plugins[name](*args, **kwargs)


class Write(Plugin):
    """Blueprint for writing file manipulation processes.

    Announce:

        - If the file did not exist and a file has been created
        - If the file did exist and the file has not been changed
        - If the file did exist and the file has been changed
    """

    def required(self) -> _t.Optional[_Path]:
        """Pre-requisite for working on file (if there is one).

        :return: Path object, otherwise None.
        """

    @property
    @_abstractmethod
    def path(self) -> _Path:
        """Path to file, absolute or relative, that will be worked on.

        :return: Returned value needs to be a Path object.
        """

    def write(self, *args: str, **kwargs: bool) -> _t.Any:
        """All write logic to be written within this method.

        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        """

    def __call__(self, *args: str, **kwargs: bool) -> None:
        if (
            self.required() is None  # type: ignore
            or self.required().exists()  # type: ignore
        ):
            path = _Path(self.path)
            print(f"Updating ``{path}``")
            with _HashCap(path) as cap:
                self.write(*args, **kwargs)

            if cap.new:
                print(f"created ``{path.name}``")

            elif cap.compare:
                print(f"``{path.name}`` is already up to date")
            else:
                print(f"updated ``{path.name}``")


class FixFile(Plugin):
    """Blueprint for writing audit and fix plugins for individual files.

    All logic can act on each file that would be passed from __call__.

    Called within context of defined environment variables.
    If no environment variables are defined nothing will change.

    Condition for failure needs to be defined, as the file argument
    passed from outer loop will not return an exit status.

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
    :return: Only 0 exit-status can be returned. If process fails error
        will be raised.
    """

    @_abstractmethod
    def fail_condition(self) -> _t.Optional[bool]:
        """Condition to trigger non-subprocess failure."""

    @_abstractmethod
    def audit(self, file: _Path, **kwargs: bool) -> None:
        """All logic written within this method for each file's audit.

        :param file: Individual file.
        :param kwargs: Boolean flags for subprocesses.
        """

    @_abstractmethod
    def fix(self, file: _Path, **kwargs: bool) -> None:
        """All logic written within this method for each file's fix.

        :param file: Individual file.
        :param kwargs: Boolean flags for subprocesses.
        """

    @_check_command
    def __call__(self, *args: str, **kwargs: bool) -> int:
        files = [p for p in _files if p.is_file()]
        for file in files:
            self.audit(file, **kwargs)
            fail = self.fail_condition()
            if fail is not None and fail:
                if kwargs.get("fix", False):
                    self.fix(file, **kwargs)
                else:
                    raise self.audit_error()

        # if no error raised return 0 to decorator
        return 0


# array of plugins
PLUGINS = [Audit, Fix, Action, Parametrize, Write, FixFile]

# array of plugin names
PLUGIN_NAMES = [t.__name__ for t in PLUGINS]

# array of plugin types before instantiation
PluginType = _t.Union[
    _t.Type[Audit],
    _t.Type[Fix],
    _t.Type[Action],
    _t.Type[Parametrize],
    _t.Type[Write],
    _t.Type[FixFile],
]

# array of plugin types after instantiation
PluginInstance = _t.Union[Audit, Fix, Action, Parametrize, Write, FixFile]


class _Plugins(_MutableMapping):  # pylint: disable=too-many-ancestors
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
            raise _exceptions.NameConflictError(plugin.__name__, name)

        mro = tuple(p.__name__ for p in _inspect.getmro(plugin))
        if not hasattr(plugin, "__bases__") or not any(
            i in PLUGIN_NAMES for i in mro
        ):
            raise TypeError(
                "can only register one of the following: {}; not {}".format(
                    ", ".join(PLUGIN_NAMES), mro
                )
            )

        super().__setitem__(name, plugin(name))


_plugins = _Plugins()


def register(name: str) -> _t.Callable[[PluginType], PluginType]:
    """Register subclassed plugin to collection.

    :param name: Name to register plugin as.
    :return: Return registered plugin to call.
    """

    def _register(plugin: PluginType):
        _plugins[name] = plugin
        return plugin

    return _register


def mapping() -> _t.Dict[str, PluginInstance]:
    """Get dict of named keys and their corresponding plugin values.

    :return: Mapping of plugins and their unique names.
    """
    return dict(_plugins)


def registered() -> _t.List[str]:
    """Get list of registered plugins.

    :return: List of registered plugins.
    """
    return sorted(list(_plugins))


def get(name: str) -> PluginInstance:
    """Get plugins by name.

    :param name: Unique name of plugin.
    :return: Callable plugin instance.
    """
    return _plugins[name]


def load() -> None:
    """Import all registered plugins from provided plugin  paths."""
    for plugin_path in _plugin_paths:
        _sys.path.append(str(plugin_path.parent))
        if plugin_path.is_dir():
            for path in plugin_path.iterdir():
                if (
                    not path.name.startswith("_")
                    and not path.name.startswith(".")
                    and path.name.endswith(".py")
                ):
                    _importlib.import_module(
                        f"{plugin_path.name}.{path.name.replace('.py', '')}"
                    )
