"""
pyaud._utils
============
"""
from __future__ import annotations

from gitspy import Git as _Git
from lsfiles import LSFiles as _LSFiles
from object_colors import Color as _Color

colors = _Color()
git = _Git()
files = _LSFiles()

colors.populate_colors()


def get_commit_hash() -> str | None:
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
