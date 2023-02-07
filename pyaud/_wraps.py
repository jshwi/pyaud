"""
pyaud._wraps
============

Decorators for wrapping plugins.
"""
from __future__ import annotations

import functools as _functools
import sys as _sys
import typing as _t
import warnings as _warnings

from spall.exceptions import CommandNotFoundError as _CommandNotFoundError

from ._cache import FileCacher as _FileCacher
from ._objects import BasePlugin as _BasePlugin
from ._objects import colors as _colors
from ._objects import files as _files


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
    """

    def __init__(self, cls: type[_BasePlugin]) -> None:
        self._cls = cls

    def files(self, func: _t.Callable[..., int]) -> _t.Callable[..., int]:
        """Wrap ``__call__`` with a hashing function.

        :param func: Function to wrap.
        :return: Wrapped function.
        """

        @_functools.wraps(func)
        def _wrapper(*args: str, **kwargs: bool) -> int:
            _file_cacher = _FileCacher(self._cls, func, *args, **kwargs)
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
            except _CommandNotFoundError as err:
                _warnings.warn(
                    f"{str(err).split(':', maxsplit=1)[0]}: Command not found",
                    RuntimeWarning,
                )

            return 1

        return _wrapper
