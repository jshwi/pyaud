"""
pyaud._utils
============
"""
from __future__ import annotations

from pathlib import Path as _Path

import git as _git
from lsfiles import LSFiles as _LSFiles

files = _LSFiles()


def get_commit_hash() -> str | None:
    """Get the hash of the current commit.

    :return: A ``str`` containing the hash of the commit, or None if no
        hash can be provided.
    """
    try:
        return _git.Repo(_Path.cwd()).git.rev_parse("HEAD")
    except _git.GitCommandError:
        return None


def working_tree_clean() -> bool:
    """Check if working tree clean.

    :return: Working tree clean? True or False.
    """
    return not _git.Repo(_Path.cwd()).git.status("--short")
