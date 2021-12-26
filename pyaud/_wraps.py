"""
pyaud._wraps
============

Decorators for wrapping plugins.
"""
import functools as _functools
import sys as _sys
import typing as _t

from ._data import Record as _Record
from ._environ import DATADIR as _DATADIR
from ._indexing import files as _files
from ._objects import BasePlugin as _BasePlugin
from ._utils import colors as _colors
from ._utils import package as _package


def check_command(func: _t.Callable[..., int]) -> _t.Callable[..., int]:
    """Run the routine common with all functions in this package.

    :param func: Function to decorate.
    :return: Wrapped function.
    """

    @_functools.wraps(func)
    def _wrapper(*args: str, **kwargs: bool) -> int:
        returncode = 0
        if not _files.reduce():
            print("No files found")
        else:
            returncode = func(*args, **kwargs)
            if returncode:
                _colors.red.bold.print(
                    f"Failed: returned non-zero exit status {returncode}",
                    file=_sys.stderr,
                )
            else:
                _colors.green.bold.print(
                    f"Success: no issues found in {len(_files)} source files"
                )

        return returncode

    return _wrapper


class ClassDecorator:  # pylint: disable=too-few-public-methods
    """Handle reading and writing file data for called processes.

    Decorate on call to ``__new__`` to wrap uninstantiated class and its
    ``__call__`` method.

    :param cls: The class whose ``__call__`` method will be wrapped.
    """

    DURATIONS = "durations.json"
    FILE_HASHES = "files.json"

    def __init__(self, cls: _t.Type[_BasePlugin]) -> None:
        self._cls = cls

    def time(self, func: _t.Callable[..., int]) -> _t.Callable[..., int]:
        """Wrap ``__call__`` with a timer.

        :param func: Function to wrap.
        :return: Wrapped function.
        """

        @_functools.wraps(func)
        def _wrapper(*args: str, **kwargs: bool) -> int:
            data_file = _DATADIR / self.DURATIONS
            package = _package()
            with _Record(data_file, package, self._cls) as record:
                returncode = func(*args, **kwargs)

                # read old data in after receiving new data to ensure
                # data isn't lost between nested runs
                record.read()

            logged_time = "{}: Execution time: {}s; Average time: {}s".format(
                self._cls.__name__, record.time(), record.average()
            )
            self._cls.logger().info(logged_time)
            if kwargs.get("timed", False):
                _colors.magenta.print(logged_time)

            return returncode

        return _wrapper
