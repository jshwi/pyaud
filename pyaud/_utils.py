"""
pyaud.utils
===========

Utility classes and functions.
"""
from __future__ import annotations

import typing as _t
from pathlib import Path as _Path

from gitspy import Git as _Git
from object_colors import Color as _Color

colors = _Color()
git = _Git()

colors.populate_colors()


def branch() -> _t.Optional[str]:
    """Return current Git branch if in Git repository.

    :return: Checked out branch or None if no parent commit or repo.
    """
    git.symbolic_ref("--short", "HEAD", suppress=True, capture=True)
    stdout = git.stdout()
    if stdout:
        return stdout[-1]

    return None


def get_packages() -> _t.List[str]:
    """Return list of Python package names currently in project.

    Prevent dot separated subdirectories (import syntax) as args are
    evaluated by path.

    Only return the parent package's name.

    :raises PythonPackageNotFoundError: Raised if no package can be
        found.
    :return: List of Python packages.
    """
    return [_Path.cwd().name]


def package() -> str:
    """Return name of primary Python package.

    :raises PythonPackageNotFoundError: Raised if no primary package can
        be determined.
    :return: Name of primary Python package.
    """
    # at least one package will be returned or an error would have been
    # raised
    return get_packages()[0]


def get_commit_hash() -> _t.Optional[str]:
    """Get the hash of the current commit.

    :return: A ``str`` containing the hash of the commit, or None if no
        hash can be provided.
    """
    git.rev_parse("HEAD", capture=True, suppress=True)
    try:
        return git.stdout()[0]
    except IndexError:
        return None


def working_tree_clean() -> bool:
    """Check if working tree clean.

    :return: Working tree clean? True or False.
    """
    git.stdout()  # [...] -> void; clear stdout, if it exists
    git.status("--short", capture=True)
    return not git.stdout()
