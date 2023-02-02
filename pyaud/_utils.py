"""
pyaud._utils
============
"""
from __future__ import annotations

from pathlib import Path as _Path

import setuptools as _setuptools
from gitspy import Git as _Git
from lsfiles import LSFiles as _LSFiles
from object_colors import Color as _Color

from . import _config

colors = _Color()
git = _Git()
files = _LSFiles()

colors.populate_colors()


def get_packages() -> list[str]:
    """Return list of Python package names currently in project.

    Prevent dot separated subdirectories (import syntax) as args are
    evaluated by path.

    Only return the parent package's name.

    :raises PythonPackageNotFoundError: Raised if no package can be
        found.
    :return: List of Python packages.
    """
    packages = list(
        {
            i.split(".", maxsplit=1)[0]
            for i in _setuptools.find_packages(
                # in response to an update to `setuptools` stubs:
                # - error: Argument "where" has incompatible type
                #   "Path"; expected "str"
                where=str(_Path.cwd()),
                exclude=_config.toml["packages"]["exclude"],
            )
        }
    )
    return sorted(packages)


def package() -> str | None:
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

    return None


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
