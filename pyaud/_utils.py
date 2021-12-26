"""
pyaud.utils
===========

Utility classes and functions.
"""
from __future__ import annotations

import hashlib as _hashlib
import typing as _t
from pathlib import Path as _Path

import setuptools as _setuptools
from object_colors import Color as _Color

from . import config as _config
from ._objects import MutableSequence as _MutableSequence
from ._subprocess import git as _git
from .exceptions import (
    PythonPackageNotFoundError as _PythonPackageNotFoundError,
)

colors = _Color()
colors.populate_colors()


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


def branch() -> _t.Optional[str]:
    """Return current Git branch if in Git repository.

    :return: Checked out branch or None if no parent commit or repo.
    """
    _git.symbolic_ref(  # type: ignore
        "--short", "HEAD", suppress=True, capture=True
    )
    stdout = _git.stdout()
    if stdout:
        return stdout[-1]

    return None


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

    def populate(self) -> None:
        """Populate object with index of versioned Python files."""
        _git.ls_files(capture=True)  # type: ignore
        self.extend(
            list(
                # prevent duplicates which might occur during a merge
                set(
                    _Path.cwd() / p
                    for p in [_Path(p) for p in _git.stdout()]
                    # exclude any basename, stem, or part of a
                    # `pathlib.Path` path
                    if not any(i in self._exclude for i in (*p.parts, p.stem))
                    # only include Python files in index
                    and p.name.endswith(".py")
                )
            )
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


def get_packages() -> _t.List[str]:
    """Return list of Python package names currently in project.

    Prevent dot separated subdirectories (import syntax) as args are
    evaluated by path.

    Only return the parent package's name.

    :raises PythonPackageNotFoundError: Raised if no package can be
        found.
    :return: List of Python packages.
    """
    packages = list(
        set(
            i.split(".", maxsplit=1)[0]
            for i in _setuptools.find_packages(
                # in response to an update to `setuptools` stubs:
                # - error: Argument "where" has incompatible type
                #   "Path"; expected "str"
                where=str(_Path.cwd()),
                exclude=_config.toml["packages"]["exclude"],
            )
        )
    )
    if not packages:
        raise _PythonPackageNotFoundError("no packages found")

    packages.sort()
    return packages


def package() -> str:
    """Return name of primary Python package.

    :raises PythonPackageNotFoundError: Raised if no primary package can
        be determined.
    :return: Name of primary Python package.
    """
    # at least one package will be returned or an error would have been
    # raised
    packages = get_packages()

    # if there is only one package then that is the default
    if len(packages) == 1:
        return packages.pop()

    # if there are multiple packages found then look for a configured
    # package name that matches one of the project's packages
    package_name = _config.toml["packages"].get("name")
    if package_name in packages:
        return package_name

    # if there are multiple packages found, and none of the above two
    # apply, then the package with the same name as the project root (if
    # it exists) is the default
    repo = _Path.cwd().name
    if repo in packages:
        return repo

    # if none of the above criteria is met then raise
    raise _PythonPackageNotFoundError("cannot determine primary package")


files = _Files()
