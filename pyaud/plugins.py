"""
pyaud.plugins
=============

Main module used for public API.
"""
import functools
import importlib
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .environ import DEFAULT_PLUGINS, NAME, SITE_PLUGINS, TempEnvVar
from .exceptions import NameConflictError, PyAuditError
from .objects import MutableMapping
from .utils import HashCap, Subprocess, colors, files

_plugin_paths: List[Path] = [DEFAULT_PLUGINS, SITE_PLUGINS]


def check_command(func: Callable[..., int]) -> Callable[..., None]:
    """Run the routine common with all functions in this package.

    :param func:    Function to decorate.
    :return:        Wrapped function.
    """

    @functools.wraps(func)
    def _wrapper(*args, **kwargs: bool) -> None:
        if not files.reduce():
            print("No files found")
        else:
            returncode = func(*args, **kwargs)
            if returncode:
                colors.red.bold.print(
                    f"Failed: returned non-zero exit status {returncode}",
                    file=sys.stderr,
                )
            else:
                colors.green.bold.print(
                    "Success: no issues found in {} source files".format(
                        len(files)
                    )
                )

    return _wrapper


def write_command(
    file: Union[bytes, str, os.PathLike],
    required: Optional[Union[bytes, str, os.PathLike]] = None,
) -> Callable[..., Any]:
    """Run the routine common with all functions manipulating files.

    :param file:        File which is to be written to.
    :param required:    Any required files.
    :return:            Wrapped function.
    """

    def _decorator(func: Callable[..., int]) -> Callable[..., None]:
        @functools.wraps(func)
        def _wrapper(*args: str, **kwargs: Union[bool, str]) -> None:
            if (
                not required
                or Path(Path.cwd() / os.environ[str(required)]).exists()
            ):
                _file = Path.cwd() / os.environ[str(file)]
                print(f"Updating ``{_file}``")
                with HashCap(_file) as cap:
                    func(*args, **kwargs)

                if cap.new:
                    print(f"created ``{_file.name}``")

                elif cap.compare:
                    print(f"``{_file.name}`` is already up to date")
                else:
                    print(f"updated ``{_file.name}``")

        return _wrapper

    return _decorator


class _SubprocessFactory(MutableMapping):  # pylint: disable=too-many-ancestors
    """Instantiate collection of ``Subprocess`` objects."""

    def __init__(self, args: List[str]):
        super().__init__()
        for arg in args:
            self[arg] = Subprocess(arg)


class Plugin(ABC):  # pylint: disable=too-few-public-methods
    """Base class of all plugins.

    Raises ``TypeError`` if registered directly.

    Contains the name attribute assigned upon registration.

    Subprocesses are stored in the ``subprocess`` dict object

    :param name: Name assigned to plugin via ``@register`` decorator.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.subprocess = _SubprocessFactory(self.exe)

    @staticmethod
    def audit_error() -> PyAuditError:
        """Raise if checks have failed.

        :return: AuditError instantiated with error message.
        """
        return PyAuditError(" ".join(sys.argv))

    @property
    def env(self) -> Dict[str, str]:
        """Return environment which will remain active for run.

        :return:    Dict containing any number of str keys and
                    corresponding str values.
        """
        return {}

    @property
    def exe(self) -> List[str]:
        """List of executables to add to ``subprocess`` dict.

        :return: List of str object to assign to subprocesses
        """
        return []

    def __call__(self, *args: Any, **kwargs: bool) -> Any:
        """Enables calling of all plugin instances."""


class Audit(Plugin):
    """Blueprint for writing audit-only plugins.

    Audit will be called from here.

    Run within context of defined environment variables.
    If no environment variables are defined nothing will change.

    :raises CalledProcessError: Will always be raised if something
                                fails that is not to do with the
                                audit condition.

                                Will be excepted and reraised as
                                ``AuditError`` if the audit fails.

    :raises AuditError:         Raised from ``CalledProcessError`` if
                                audit fails.

    :return:                    If any error has not been raised for any
                                reason int object must be returned, from
                                subprocess or written, to notify call
                                whether process has succeeded or failed.

                                No value will actually return from
                                __call__ as it will be passed to the
                                decorator.
    """

    @abstractmethod
    def audit(self, *args: Any, **kwargs: bool) -> int:
        """All audit logic to be written within this method.

        :param args:    Args that can be passed from other plugins.
        :param kwargs:  Boolean flags for subprocesses.
        :return:        If any error has not been raised for any reason
                        int object must be returned, from subprocess or
                        written, to notify call whether process has
                        succeeded or failed.
        """

    @check_command
    def __call__(self, *args: Any, **kwargs: bool) -> int:
        with TempEnvVar(os.environ, **self.env):
            try:
                return self.audit(*args, **kwargs)

            except CalledProcessError as err:
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

    :raises CalledProcessError: Will always be raised if something
                                fails that is not to do with the
                                audit condition.

                                Will be excepted and reraised as
                                ``AuditError`` if the audit fails and
                                ``-f/--fix`` is not passed to the
                                commandline.

    :raises AuditError:         Raised from ``CalledProcessError``
                                if audit fails and ``-f/--fix`` flag
                                if not passed to the commandline.

    :return:                    If any error has not been raised for any
                                reason int object must be returned, from
                                subprocess or written, to notify call
                                whether process has succeeded or failed.

                                No value will actually return from
                                __call__ as it will be passed to the
                                decorator.
    """

    @abstractmethod
    def audit(self, *args: Any, **kwargs: bool) -> int:
        """All audit logic to be written within this method.

        :param args:    Args that can be passed from other plugins.

        :param kwargs:  Boolean flags for subprocesses.

        :return:        If any error has not been raised for any reason
                        int object must be returned, from subprocess or
                        written, to notify __call__ whether process has
                        succeeded or failed.

                        If non-zero exist if returned and ``-f/--fix``
                        has been passed to the commandline run the
                        ``fix`` method, otherwise raise ``AuditError``.
        """

    @abstractmethod
    def fix(self, *args: Any, **kwargs: bool) -> int:
        """Run if audit fails but only if running a fix.

        :param args:    Args that can be passed from other plugins.
        :param kwargs:  Boolean flags for subprocesses.
        :return:        If any error has not been raised for any reason
                        int object must be returned, from subprocess or
                        written, to notify __call__ whether process has
                        succeeded or failed.
        """

    @check_command
    def __call__(self, *args: Any, **kwargs: bool) -> Any:
        with TempEnvVar(os.environ, **self.env):
            try:
                return self.audit(*args, **kwargs)

            except CalledProcessError as err:
                if kwargs.get("fix", False):
                    return self.fix(**kwargs)

                raise self.audit_error() from err


class Action(Plugin):  # pylint: disable=too-few-public-methods
    """Blueprint for writing generic plugins.

    Called within context of defined environment variables.
    If no environment variables are defined nothing will change.

    :raises CalledProcessError: Will always be raised if something
                                fails that is not to do with the
                                action condition.

                                Will be excepted and reraised as
                                ``AuditError`` if the action fails.

    :raises AuditError:         Raised from ``CalledProcessError``
                                if action fails.

    :return:                    Any value and type can be returned.
    """

    @abstractmethod
    def action(self, *args: Any, **kwargs: bool) -> Any:
        """All logic to be written within this method.

        :param args:    Args that can be passed from other plugins.
        :param kwargs:  Boolean flags for subprocesses.
        :return:        Any value and type can be returned.
        """

    def __call__(self, *args: Any, **kwargs: bool) -> Any:
        with TempEnvVar(os.environ, **self.env):
            try:
                return self.action(*args, **kwargs)

            except CalledProcessError as err:
                raise self.audit_error() from err


class Parametrize(Plugin):  # pylint: disable=too-few-public-methods
    """Define a list of strings to call multiple plugins.

    :raises CalledProcessError: Will always be raised if something
                                fails that is not to do with the
                                called plugin's condition.

                                Will be excepted and reraised as
                                ``AuditError`` if the called plugin
                                fails and the called plugin does not
                                specify a ``fix`` method or the
                                ``-f/--fix`` flag is not passed to the
                                commandline.

    :raises AuditError:         Raised from ``CalledProcessError``
                                if called plugin fails and no ``fix``
                                method is specified or the ``-f/--fix``
                                flag is not passed to the commandline.
    """

    @abstractmethod
    def plugins(self) -> List[str]:
        """List of plugin names to run.

        :return: List of plugin names, as defined in ``@register``.
        """

    def __call__(self, *args: Any, **kwargs: bool) -> None:
        for name in self.plugins():
            colors.cyan.bold.print(f"\n{NAME} {name}")
            plugins[name](*args, **kwargs)


# array of plugins
PLUGINS = [Audit, Fix, Action, Parametrize]

# array of plugin names
PLUGIN_NAMES = [t.__name__ for t in PLUGINS]

# array of plugin types before instantiation
PluginType = Union[Type[Audit], Type[Fix], Type[Action], Type[Parametrize]]

# array of plugin types after instantiation
PluginInstance = Union[Audit, Fix, Action, Parametrize]


class _Plugins(MutableMapping):  # pylint: disable=too-many-ancestors
    """Holds registered plugins."""

    def __setitem__(self, name: str, plugin: Any) -> None:
        # only unique names to be set in `plugins` object
        # if name is not unique raise `NameConflictError`
        if name in self:
            raise NameConflictError(plugin.__name__, name)

        if hasattr(plugin, "__bases__"):
            super().__setitem__(name, plugin(name))

        else:
            super().__setitem__(name, plugin)


plugins = _Plugins()


def register(name: str) -> Callable[..., PluginInstance]:
    """Register subclassed plugin to collection.

    :param name:    Name to register plugin as.
    :return:        Return registered plugin to call.
    """

    def _register(plugin: Any) -> Any:
        plugins[name] = plugin
        return plugin

    return _register


def load() -> None:
    """Import all registered plugins from provided plugin paths."""
    for plugin_path in _plugin_paths:
        sys.path.append(str(plugin_path.parent))
        if plugin_path.is_dir():
            for path in plugin_path.iterdir():
                if (
                    not path.name.startswith("_")
                    and not path.name.startswith(".")
                    and path.name.endswith(".py")
                ):
                    importlib.import_module(
                        f"{plugin_path.name}.{path.name.replace('.py', '')}"
                    )
