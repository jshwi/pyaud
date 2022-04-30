"""
pyaud._cache
============
"""
from __future__ import annotations

import hashlib as _hashlib
import typing as _t
from pathlib import Path as _Path

from . import exceptions as _exceptions
from ._environ import environ as _environ
from ._indexing import IndexedState as _IndexedState
from ._indexing import files as _files
from ._objects import JSONIO as _JSONIO
from ._objects import BasePlugin as _BasePlugin
from ._utils import colors as _colors
from ._utils import get_commit_hash as _get_commit_hash
from ._utils import working_tree_clean as _working_tree_clean


class HashCap:
    """Analyze hashes for before and after.

    :param file: The path of the file to hash.
    """

    def __init__(self, file: _Path) -> None:
        self.file = file
        self.before: _t.Optional[str] = None
        self.after: _t.Optional[str] = None
        self.compare = False
        self.new = not self.file.is_file()
        if not self.new:
            self.before = self._hash_file()

    def _hash_file(self) -> str:
        """Open the files and inspect it to get its hash.

        :return: Hash as a string.
        """
        with open(self.file, "rb") as lines:
            _hash = _hashlib.blake2b(lines.read())

        return _hash.hexdigest()

    def _compare(self) -> bool:
        """Compare two hashes in the ``snapshot`` list.

        :return: Boolean: True for both match, False if they don't.
        """
        return self.before == self.after

    def __enter__(self) -> HashCap:
        return self

    def __exit__(
        self, exc_type: _t.Any, exc_val: _t.Any, exc_tb: _t.Any
    ) -> None:
        try:
            self.after = self._hash_file()
        except FileNotFoundError:
            pass

        self.compare = self._compare()


class HashMapping(_JSONIO):
    """Persistent data object.

    :param path: Path to data file.
    :param project: Name of the project that this package is auditing.
    :param cls: Audit that this class is running in.
    :param commit: Commit that this audit is being run on.
    """

    _FALLBACK = "fallback"

    def __init__(
        self,
        path: _Path,
        project: str,
        cls: _t.Type[_BasePlugin],
        commit: _t.Optional[str] = None,
    ) -> None:
        super().__init__(path)
        self._project = project
        self._commit = commit or self._FALLBACK
        self._cls = str(cls)

    @staticmethod
    def _get_new_hash(path: _Path) -> str:
        # get a new md5 file hash
        return _hashlib.md5(path.read_bytes()).hexdigest()

    @staticmethod
    def _fmt(path: _Path) -> str:
        # format the `Path` object to JSON appropriate `str`
        # remove path from current working dir for flexible location
        return str(path.relative_to(_Path.cwd()))

    def _setitem(self, path: _Path, value: str) -> None:
        self[self._project][self._commit][self._cls][self._fmt(path)] = value

    def _getitem(self, path: _Path) -> str:
        # get path within the session object
        return self[self._project][self._commit][self._cls].get(
            self._fmt(path)
        )

    def _delitem(self, path: _Path) -> None:
        formatted = self._fmt(path)
        cls = self[self._project][self._commit][self._cls]
        if formatted in cls:
            del cls[formatted]

    def _set_hash(self, path: _Path) -> None:
        # get already existing hash
        self._setitem(path, self._get_new_hash(path))

    def match_file(self, path: _Path) -> bool:
        """Match selected class against a file relevant to it.

        :param path: Path to the file to check if it has changed.
        :return: Is the file a match (not changed)? True or False.
        """
        return self._get_new_hash(path) == self._getitem(path)

    def hash_files(self) -> None:
        """Populate file hashes."""
        for file in _files:
            self._set_hash(file)

        self[self._project][self._FALLBACK] = dict(
            self[self._project][self._commit]
        )

    def hash_file(self, path: _Path) -> None:
        """Populate file hash.

        :param path: Path to hash.
        """
        if path.is_file():
            self._set_hash(path)
            self[self._project][self._FALLBACK] = dict(
                self[self._project][self._commit]
            )
        else:
            self._delitem(path)

    def tag(self, tag: str) -> None:
        """Tag commit key with a prefix.

        :param tag: Prefix to tag commit key with.
        """
        self._commit = f"{tag}-{self._commit}"

    def read(self):
        """Read data from existing cache file if it exists,

        Ensure necessary keys exist regardless.
        """
        super().read()
        self[self._project] = self.get(self._project, {})
        self[self._project][self._commit] = self[self._project].get(
            self._commit, self[self._project].get(self._FALLBACK, {})
        )
        self[self._project][self._commit][self._cls] = self[self._project][
            self._commit
        ].get(self._cls, {})


class FileCacher:  # pylint: disable=too-few-public-methods
    """Handle caching of file(s)."""

    FILE_HASHES = "files.json"

    def __init__(self, cls, func, *args, **kwargs) -> None:
        self._cls: _t.Type[_BasePlugin] = cls
        self.func: _t.Callable = func
        self.args: _t.Tuple = args
        self.kwargs: _t.Dict = kwargs
        self.no_cache = self.kwargs.get("no_cache", False)
        self.hashed = HashMapping(
            _environ.CACHEDIR / self.FILE_HASHES,
            _environ.REPO,
            self._cls,
            _get_commit_hash(),
        )
        if not _working_tree_clean():
            self.hashed.tag("uncommitted")

        self.hashed.read()

    def _hash_file(
        self, file: _Path, passed: _t.Callable, *args: _t.Any
    ) -> bool:
        if self.hashed.match_file(file):
            self._cls.logger().debug("hit: %s", file)
            passed(*args)
            return True

        self._cls.logger().debug("miss: %s", file)
        return False

    def _post_check(self, condition: bool) -> int:
        if condition:
            _colors.green.bold.print(
                "No changes have been made to audited files"
            )
            return 0

        return self.func(*self.args, **self.kwargs)

    def _write(self, action: _t.Callable) -> None:
        self._cls.logger().debug(
            "%s finished successfully, writing to %s",
            self._cls.__name__,
            self.hashed.path,
        )
        action()
        self.hashed.write()

    def _cache_files(self) -> int:
        with _IndexedState() as state:
            for file in list(_files):
                is_hashed = self._hash_file(file, _files.remove, file)
                if not is_hashed and self._cls.cache_all:
                    state.restore()
                    break

            returncode = self._post_check(bool(not _files and state.length))
            self._write(self.hashed.hash_files)

        return returncode

    def _cache_file(self) -> int:
        returncode = 0
        file = self._cls.cache_file
        if file is not None:
            path = _Path.cwd() / file
            self._cls.logger().info(
                "%s.cache_file=%s", self._cls.__name__, path
            )
            try:
                returncode = self.func(*self.args, **self.kwargs)
            except _exceptions.AuditError as err:
                self._cls.logger().debug("miss: %s", path)
                self._write(lambda: self.hashed.hash_file(path))
                raise _exceptions.AuditError(str(err)) from err

            if (
                not returncode
                and path.is_file()
                and self.hashed.match_file(path)
            ):
                self._cls.logger().debug("hit: %s", path)
                _colors.green.print(
                    "No changes have been made to audited file"
                )
                return 0

            self._cls.logger().debug("miss: %s", path)
            self._write(lambda: self.hashed.hash_file(path))

        return returncode

    def files(
        self, func: _t.Callable[..., int], *args: str, **kwargs: bool
    ) -> int:
        """Wrap ``__call__`` with a hashing function.

        :param func: Function to wrap.
        :return: Wrapped function.
        """
        no_cache = kwargs.get("no_cache", False)
        self._cls.logger().info(
            "NO_CACHE=%s, %s.cache=%s",
            no_cache,
            self._cls.__name__,
            self._cls.cache,
        )
        if not no_cache:
            if self._cls.cache_file is not None:
                return self._cache_file()

            if self._cls.cache:
                return self._cache_files()

        self._cls.logger().info("skipping reading and writing to disk")
        return func(*args, **kwargs)
