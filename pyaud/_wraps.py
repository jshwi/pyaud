"""
pyaud._wraps
============

Decorators for wrapping plugins.
"""
import functools as _functools
import sys as _sys
import typing as _t
import warnings as _warnings
from pathlib import Path as _Path

import spall.exceptions as sp_exceptions

from . import _data
from ._cache import FileCacher as _FileCacher
from ._indexing import files as _files
from ._locations import AppFiles as _AppFiles
from ._objects import BasePlugin as _BasePlugin
from ._utils import colors as _colors


class CheckCommand:
    """Decorate callable with status of completion."""

    @staticmethod
    def _announce_completion(success_message: str, returncode: int) -> None:
        if returncode:
            _colors.red.bold.print(
                f"Failed: returned non-zero exit status {returncode}",
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
            cls._announce_completion(
                "Success: no issues found in file", returncode
            )
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
                print("No files found")
            else:
                returncode = func(*args, **kwargs)
                cls._announce_completion(
                    f"Success: no issues found in {len(_files)} source files",
                    returncode,
                )

            return returncode

        return _wrapper


class ClassDecorator:
    """Handle reading and writing file data for called processes.

    Decorate on call to ``__new__`` to wrap uninstantiated class and its
    ``__call__`` method.

    :param cls: The class whose ``__call__`` method will be wrapped.
    :param app_files: App file locations object.
    """

    def __init__(
        self, cls: _t.Type[_BasePlugin], app_files: _AppFiles
    ) -> None:
        self._cls = cls
        self._app_files = app_files

    def time(self, func: _t.Callable[..., int]) -> _t.Callable[..., int]:
        """Wrap ``__call__`` with a timer.

        :param func: Function to wrap.
        :return: Wrapped function.
        """

        @_functools.wraps(func)
        def _wrapper(*args: str, **kwargs: bool) -> int:
            repo = _Path.cwd().name
            with _data.record.track(
                repo, self._cls, self._app_files.durations_file
            ) as time_keeper:
                returncode = func(*args, **kwargs)

            _data.record.write(self._app_files.durations_file)
            logged_time = "{}: Execution time: {}s; Average time: {}s".format(
                self._cls.__name__,
                time_keeper.elapsed(),
                _data.record.average(repo, self._cls),
            )
            self._cls.logger().info(logged_time)
            if kwargs.get("timed", False):
                _colors.magenta.print(logged_time)

            return returncode

        return _wrapper

    def files(self, func: _t.Callable[..., int]) -> _t.Callable[..., int]:
        """Wrap ``__call__`` with a hashing function.

        :param func: Function to wrap.
        :return: Wrapped function.
        """

        @_functools.wraps(func)
        def _wrapper(*args: str, **kwargs: bool) -> int:
            _file_cacher = _FileCacher(
                self._cls, func, self._app_files, *args, **kwargs
            )
            return _file_cacher.files(func, *args, **kwargs)

        return _wrapper

    @staticmethod
    def not_found(func: _t.Callable[..., int]) -> _t.Callable[..., int]:
        """Wrap ``__call__`` to resolve ``CommandNotFound`` errors.

        :param func: Function to wrap.
        :return: Wrapped function.
        """

        @_functools.wraps(func)
        def _wrapper(*args: str, **kwargs: bool) -> int:
            try:
                return func(*args, **kwargs)
            except sp_exceptions.CommandNotFoundError as err:
                _warnings.warn(
                    f"{str(err).split(':', maxsplit=1)[0]}: Command not found",
                    RuntimeWarning,
                )

            return 1

        return _wrapper
