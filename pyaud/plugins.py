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


class Write(Plugin):
    """Blueprint for writing file manipulation processes.

    Announce:

        - If the file did not exist and a file has been created
        - If the file did exist and the file has not been changed
        - If the file did exist and the file has been changed
    """

    def required(self) -> Optional[Path]:
        """Pre-requisite for working on file (if there is one).

        :return: Path object, otherwise None.
        """

    @property
    @abstractmethod
    def path(self) -> Path:
        """Path to file, absolute or relative, that will be worked on.

        :return: Returned value needs to be a Path object.
        """

    def write(self, *args: Any, **kwargs: bool) -> Any:
        """All write logic to be written within this method.

        :param args:    Args that can be passed from other plugins.
        :param kwargs:  Boolean flags for subprocesses.
        """

    def __call__(self, *args: Any, **kwargs: bool) -> None:
        if (
            self.required() is None  # type: ignore
            or self.required().exists()  # type: ignore
        ):
            path = Path(self.path)
            print(f"Updating ``{path}``")
            with HashCap(path) as cap:
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

    :return:                    Only 0 exit-status can be returned. If
                                process fails error will be raised.
    """

    @abstractmethod
    def fail_condition(self) -> Optional[bool]:
        """Condition to trigger non-subprocess failure."""

    @abstractmethod
    def audit(self, file: Path, **kwargs: bool) -> None:
        """All logic written within this method for each file's audit.

        :param file:    Individual file.
        :param kwargs:  Boolean flags for subprocesses.
        """

    @abstractmethod
    def fix(self, file: Path, **kwargs: bool) -> None:
        """All logic written within this method for each file's fix.

        :param file:    Individual file.
        :param kwargs:  Boolean flags for subprocesses.
        """

    @check_command
    def __call__(self, *args: Any, **kwargs: bool) -> Any:
        paths = [p for p in files if p.is_file()]
        for path in paths:
            self.audit(path, **kwargs)
            fail = self.fail_condition()
            if fail is not None and fail:
                if kwargs.get("fix", False):
                    self.fix(path, **kwargs)
                else:
                    raise self.audit_error()

        # if no error raised return 0 to decorator
        return 0


# array of plugins
PLUGINS = [Audit, Fix, Action, Parametrize, Write, FixFile]

# array of plugin names
PLUGIN_NAMES = [t.__name__ for t in PLUGINS]

# array of plugin types before instantiation
PluginType = Union[
    Type[Audit],
    Type[Fix],
    Type[Action],
    Type[Parametrize],
    Type[Write],
    Type[FixFile],
]

# array of plugin types after instantiation
PluginInstance = Union[Audit, Fix, Action, Parametrize, Write, FixFile]


class _Plugins(MutableMapping):  # pylint: disable=too-many-ancestors
    """Holds registered plugins.

    Instantiate plugin on running __setitem__.

    :raise NameConflictError:   If name of registered plugin is not
                                unique.
    :raise TypeError:           If non plugin type registered.
    """

    def __setitem__(self, name: str, plugin: PluginType) -> None:
        # only unique names to be set in `plugins` object
        # if name is not unique raise `NameConflictError`
        if name in self:
            raise NameConflictError(plugin.__name__, name)

        if (
            not hasattr(plugin, "__bases__")
            or plugin.__bases__[0].__name__ not in PLUGIN_NAMES
        ):
            raise TypeError(
                "can only register one of the following: "
                + ", ".join(PLUGIN_NAMES)
            )

        super().__setitem__(name, plugin(name))


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
