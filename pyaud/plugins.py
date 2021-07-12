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

from .environ import DEFAULT_PLUGINS, SITE_PLUGINS, TempEnvVar
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


# array of plugins
PLUGINS = [Audit]

# array of plugin names
PLUGIN_NAMES = [t.__name__ for t in PLUGINS]

# array of plugin types before instantiation
PluginType = Union[Type[Audit]]

# array of plugin types after instantiation
PluginInstance = Union[Audit]


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

    def _register(plugin: Any):
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
