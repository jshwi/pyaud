"""
pyaud._wraps
============

Decorators for wrapping plugins.
"""
import functools as _functools
import sys as _sys
import typing as _t
import warnings as _warnings

from . import _data
from . import exceptions as _exceptions
from ._environ import environ as _environ
from ._indexing import HashMapping as _HashMapping
from ._indexing import IndexedState as _IndexedState
from ._indexing import files as _files
from ._objects import BasePlugin as _BasePlugin
from ._utils import colors as _colors
from ._utils import get_commit_hash as _get_commit_hash
from ._utils import package as _package
from ._utils import working_tree_clean as _working_tree_clean


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


class ClassDecorator:
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
            package = _package()
            with _data.record.track(
                package, str(self._cls), _environ.DATADIR / "durations.json"
            ) as time_keeper:
                returncode = func(*args, **kwargs)

            _data.write(_data.record, _environ.DATADIR / _data.DURATIONS)
            logged_time = "{}: Execution time: {}s; Average time: {}s".format(
                self._cls.__name__,
                time_keeper.elapsed(),
                _data.record.average(package, str(self._cls)),
            )
            self._cls.logger().info(logged_time)
            if kwargs.get("timed", False):
                _colors.magenta.print(logged_time)

            return returncode

        return _wrapper

    def _cache_files(
        self, func: _t.Callable[..., int], *args: str, **kwargs: bool
    ) -> int:
        cache_file = _environ.CACHEDIR / self.FILE_HASHES
        package = _package()
        commit = _get_commit_hash()
        hashed = _HashMapping(cache_file, package, self._cls, commit)
        if not _working_tree_clean():
            hashed.tag("uncommitted")

        hashed.read()
        with _IndexedState() as state:
            for file in list(_files):
                if hashed.match_file(file):
                    self._cls.logger().debug("hit: %s", file)
                    _files.remove(file)
                else:
                    self._cls.logger().debug("miss: %s", file)
                    if self._cls.cache_all:
                        state.restore()
                        break

            if not _files and state.length:
                _colors.green.bold.print(
                    "No changes have been made to audited files"
                )
                returncode = 0
            else:
                returncode = func(*args, **kwargs)

            if not returncode:
                self._cls.logger().debug(
                    "%s finished successfully, writing to %s",
                    self._cls.__name__,
                    hashed.path,
                )
                hashed.hash_files()
                hashed.write()

        return returncode

    def files(self, func: _t.Callable[..., int]) -> _t.Callable[..., int]:
        """Wrap ``__call__`` with a hashing function.

        :param func: Function to wrap.
        :return: Wrapped function.
        """

        @_functools.wraps(func)
        def _wrapper(*args: str, **kwargs: bool) -> int:
            no_cache = kwargs.get("no_cache", False)
            self._cls.logger().info(
                "NO_CACHE=%s, %s.cache=%s",
                no_cache,
                self._cls.__name__,
                self._cls.cache,
            )
            if no_cache or not self._cls.cache:
                self._cls.logger().info("skipping reading and writing to disk")
                return func(*args, **kwargs)

            return self._cache_files(func, *args, **kwargs)

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
            except _exceptions.CommandNotFoundError as err:
                _warnings.warn(
                    f"{str(err).split(':', maxsplit=1)[0]}: Command not found",
                    RuntimeWarning,
                )
                _warnings.warn(
                    "plugin called a subprocess that doesn't exist",
                    RuntimeWarning,
                )

            return 1

        return _wrapper
