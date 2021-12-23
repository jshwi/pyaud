"""
pyaud._indexing
===============
"""
from __future__ import annotations

import hashlib as _hashlib
import typing as _t
from pathlib import Path as _Path

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


files = _Files()
