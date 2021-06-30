"""
pyaud.plugins
=============

Main module used for public API.
"""
import functools
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Union

from .exceptions import NameConflictError
from .objects import MutableMapping
from .utils import HashCap, colors, tree


def check_command(func: Callable[..., int]) -> Callable[..., None]:
    """Run the routine common with all functions in this package.

    :param func:    Function to decorate.
    :return:        Wrapped function.
    """

    @functools.wraps(func)
    def _wrapper(**kwargs: bool) -> None:
        if not tree.reduce():
            print("No files found")
        else:
            returncode = func(**kwargs)
            if returncode:
                colors.red.bold.print(
                    f"Failed: returned non-zero exit status {returncode}",
                    file=sys.stderr,
                )
            else:
                colors.green.bold.print(
                    "Success: no issues found in {} source files".format(
                        len(tree)
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


class _Plugins(MutableMapping):  # pylint: disable=too-many-ancestors
    """Holds registered plugins."""

    def __setitem__(self, name: str, plugin: Any) -> None:
        # only unique names to be set in `plugins` object
        # if name is not unique raise `NameConflictError`
        if name in self:
            raise NameConflictError(plugin.__name__, name)

        super().__setitem__(name, plugin)


plugins = _Plugins()


def register(name: str) -> Callable[..., Any]:
    """Register subclassed plugin to collection.

    :param name:    Name to register plugin as.
    :return:        Return registered plugin to call.
    """

    def _register(plugin: Any):
        plugins[name] = plugin
        return plugin

    return _register
