"""
pyaud._cache
============
"""
from __future__ import annotations

import hashlib as _hashlib
import typing as _t
from pathlib import Path as _Path

from . import exceptions as _exceptions
from ._indexing import IndexedState as _IndexedState
from ._indexing import files as _files
from ._locations import AppFiles as _AppFiles
from ._objects import JSONIO as _JSONIO
from ._objects import BasePlugin as _BasePlugin
from ._utils import colors as _colors
from ._utils import get_commit_hash as _get_commit_hash
from ._utils import working_tree_clean as _working_tree_clean


class HashMapping(_JSONIO):
    """Persistent data object.

    :param project: Project name.
    :param cls: Audit that this class is running in.
    :param commit: Commit that this audit is being run on.
    """

    _FB = "fallback"

    def __init__(
        self,
        project: str,
        cls: _t.Type[_BasePlugin],
        commit: _t.Optional[str] = None,
    ) -> None:
        super().__init__()
        self._project = project
        self._commit = commit or self._FB
        self._cls = str(cls)
        self._session: _t.Dict[str, str] = {}

    def tag(self, tag: str) -> None:
        """Tag commit key with a prefix.

        :param tag: Prefix to tag commit key with.
        """
        self._commit = f"{tag}-{self._commit}"

    def match_file(self, path: _Path) -> bool:
        """Match selected class against a file relevant to it.

        :param path: Path to the file to check if it has changed.
        :return: Is the file a match (not changed)? True or False.
        """
        relpath = str(path.relative_to(_Path.cwd()))
        newhash = _hashlib.md5(path.read_bytes()).hexdigest()
        return newhash == self._session.get(relpath)

    def save_hash(self, path: _Path) -> None:
        """Populate file hash.

        :param path: Path to hash.
        """
        relpath = str(path.relative_to(_Path.cwd()))
        if path.is_file():
            newhash = _hashlib.md5(path.read_bytes()).hexdigest()
            self._session[relpath] = newhash
        else:
            if relpath in self._session:
                del self._session[relpath]

    def read(self, path: _Path) -> None:
        """Read from file to object.

        :param path: Path to cache file.
        """
        super().read(path)
        project = self.get(self._project, {})
        fallback = project.get(self._FB, {})
        project[self._commit] = project.get(self._commit, fallback)
        self._session = project[self._commit].get(self._cls, {})

    def write(self, path: _Path) -> None:
        """Write data to file.

        :param path: Path to cache file.
        """
        cls = {self._cls: dict(self._session)}
        self[self._project] = {self._FB: cls, self._commit: cls}
        super().write(path)


class FileCacher:  # pylint: disable=too-few-public-methods
    """Handle caching of file(s).

    :param cls: Audit that this class is running in.
    :param func: Call function belonging to cls.
    :param app_files: App file locations object.
    :param args: Args that can be passed from other plugins.
    :param kwargs: Boolean flags for subprocesses.
    """

    def __init__(
        self,
        cls: _t.Type[_BasePlugin],
        func: _t.Callable[..., int],
        app_files: _AppFiles,
        *args: str,
        **kwargs: bool,
    ) -> None:
        self._cls = cls
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.no_cache = self.kwargs.get("no_cache", False)
        self._cache_file_path = app_files.cache_file
        self.hashed = HashMapping(
            app_files.user_project_dir.name, self._cls, _get_commit_hash()
        )
        if not _working_tree_clean():
            self.hashed.tag("uncommitted")

        self.hashed.read(app_files.cache_file)

    def _on_completion(self, *paths: _Path) -> None:
        self._cls.logger().debug("writing to %s", self._cache_file_path)
        for path in paths:
            self.hashed.save_hash(path)

        self.hashed.write(self._cache_file_path)

    def _cache_files(self) -> int:
        returncode = 0
        with _IndexedState() as state:
            for file in list(_files):
                if self.hashed.match_file(file):
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
            else:
                returncode = self.func(*self.args, **self.kwargs)

            if not returncode:
                self._on_completion(*_files)

        return returncode

    def _cache_file(self) -> int:
        returncode = 0
        file = self._cls.cache_file
        if file is not None:
            path = _Path.cwd() / file
            try:
                returncode = self.func(*self.args, **self.kwargs)
            except _exceptions.AuditError as err:
                self._on_completion(path)
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
            self._on_completion(path)

        return returncode

    def files(
        self, func: _t.Callable[..., int], *args: str, **kwargs: bool
    ) -> int:
        """Wrap ``__call__`` with a hashing function.

        :param func: Function to wrap.
        :param args: Args that can be passed from other plugins.
        :param kwargs: Boolean flags for subprocesses.
        :return: Wrapped function.
        """
        no_cache = kwargs.get("no_cache", False)
        self._cls.logger().info(
            "NO_CACHE=%s, %s.cache=%s, %s.cache_file=%s",
            no_cache,
            self._cls.__name__,
            self._cls.cache,
            self._cls.__name__,
            self._cls.cache_file,
        )
        if not no_cache:
            if self._cls.cache_file is not None:
                return self._cache_file()

            if self._cls.cache:
                return self._cache_files()

        self._cls.logger().info("skipping reading and writing to disk")
        return func(*args, **kwargs)
