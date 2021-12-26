"""
pyaud._indexing
===============
"""
from __future__ import annotations

import hashlib as _hashlib
import typing as _t
from pathlib import Path as _Path

from ._objects import JSONIO as _JSONIO
from ._objects import BasePlugin as _BasePlugin
from ._objects import MutableSequence as _MutableSequence
from ._subprocess import git as _git


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


class _Files(_MutableSequence):  # pylint: disable=too-many-ancestors
    """Index all Python files in project."""

    def __init__(self) -> None:
        super().__init__()
        self._exclude: _t.List[str] = []

    def add_exclusions(self, *exclusions: str) -> None:
        """Add iterable of str objects to exclude from indexing.

        :param exclusions: Iterable of str names to exclude from index.
        """
        self._exclude.extend(exclusions)

    def extend(self, values: _t.Iterable[_Path]) -> None:
        """Like extend for a regular list but cannot duplicate.

        :param values: Method expects an iterable of ``pathlib.Path``
            objects.
        """
        super().extend(values)
        self._list = list(set(self))

    def populate(self) -> None:
        """Populate object with index of versioned Python files."""
        _git.ls_files(capture=True)  # type: ignore
        self.extend(
            _Path.cwd() / p
            for p in [_Path(p) for p in _git.stdout()]
            # exclude any basename, stem, or part of a
            # `pathlib.Path` path
            if not any(i in self._exclude for i in (*p.parts, p.stem))
            # only include Python files in index
            and p.name.endswith(".py")
        )

    def reduce(self) -> _t.List[_Path]:
        """Get all relevant python files starting from project root.

        :return: List of project's Python file index, reduced to their
            root, relative to $PROJECT_DIR. Contains no duplicate items
            so $PROJECT_DIR/dir/file1.py and $PROJECT_DIR/dir/file2.py
            become $PROJECT_DIR/dir but PROJECT_DIR/file1.py and
            $PROJECT_DIR/file2.py remain as they are.
        """
        project_dir = _Path.cwd()
        return list(
            set(
                project_dir / p.relative_to(project_dir).parts[0] for p in self
            )
        )

    def args(self, reduce: bool = False) -> _t.Tuple[str, ...]:
        """Return tuple suitable to be run with starred expression.

        :param reduce: :func:`~pyaud.utils._Tree.reduce`
        :return: Tuple of `Path` objects or str repr.
        """
        paths = list(self)
        if reduce:
            paths = self.reduce()

        return tuple(  # pylint: disable=consider-using-generator
            [str(p) for p in paths]
        )


class IndexedState:
    """Store index and ensure it's in its original state on exit."""

    def __init__(self) -> None:
        self.length = len(files)
        self._index = list(files)
        self._restored = False

    def __enter__(self) -> IndexedState:
        return self

    def __exit__(
        self, exc_type: _t.Any, exc_val: _t.Any, exc_tb: _t.Any
    ) -> None:
        if not self._restored:
            files.extend(self._index)

    def restore(self) -> None:
        """Restore the original state of index."""
        self._restored = True
        files.extend(self._index)


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
        for file in files:
            self._set_hash(file)

        self[self._project][self._FALLBACK] = dict(
            self[self._project][self._commit]
        )

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


files = _Files()
