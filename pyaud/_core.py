"""
pyaud._core
===========
"""
from __future__ import annotations

import os as _os
import sys as _sys
from pathlib import Path as _Path

import git as _git

from . import messages as _messages
from . import plugins as _plugins
from ._builtins import register_builtin_plugins as _register_builtin_plugins
from ._objects import JSONIO as _JSONIO
from ._objects import NAME as _NAME
from ._objects import colors as _colors
from ._objects import files as _files
from ._objects import toml as _toml
from ._version import __version__


def _populate_files(exclude: str | None = None) -> None:
    try:
        _files.populate(exclude)
    except _git.InvalidGitRepositoryError as err:
        _sys.exit(
            _colors.red.bold.get(_messages.INVALID_REPOSITORY.format(path=err))
        )

    if [i for i in _files if not i.is_file()]:
        _sys.exit(
            "{}\n{}".format(
                _colors.red.bold.get(_messages.REMOVED_FILES),
                _messages.RUN_COMMAND.format(
                    command=_colors.cyan.get("git add")
                ),
            )
        )


def _create_cachedir() -> None:
    path = _Path(_os.environ["PYAUD_CACHE"])
    (path / __version__).mkdir(exist_ok=True, parents=True)
    (path / "CACHEDIR.TAG").write_text(
        "Signature: 8a477f597d28d172789f06886806bc55\n"
        f"# This file is a cache directory tag created by {_NAME}.\n"
        "# For information about cache directory tags, see:\n"
        "#	https://bford.info/cachedir/spec.html\n"
    )
    (path / ".gitignore").write_text(f"# Created by {_NAME} automatically.\n*")


# remove cache of commits with no revision
def _garbage_collection() -> None:
    path = _Path.cwd()
    repo = _git.Repo(path)
    commits = repo.git.rev_list("--all").splitlines()
    json = _JSONIO(
        _Path(_os.environ["PYAUD_CACHE"]) / __version__ / _plugins.CACHE_FILE
    )
    json.read()
    project = json.get(path.name, {})
    for commit in dict(project):
        if (
            commit not in commits
            and commit != _plugins.FALLBACK
            and not commit.startswith(_plugins.UNCOMMITTED)
        ):
            del project[commit]

    json.write()


def pyaud(  # pylint: disable=too-many-arguments
    module: str,
    audit: list[str] | None = None,
    exclude: str | None = None,
    fix: bool = False,
    no_cache: bool = False,
) -> int:
    """Module entry point.

    Parse commandline arguments and run the selected choice from the
    dictionary of functions which matches the key.

    :param module: Choice of module: [modules] to list all.
    :param audit: List of plugins for audit.
    :param exclude: Regex of paths to ignore.
    :param fix: Suppress and fix all fixable issues.
    :param no_cache: Disable file caching.
    :return: Exit status.
    """
    _os.environ["PYAUD_CACHE"] = _os.environ.get("PYAUD_CACHE", ".pyaud_cache")
    _populate_files(exclude)
    _toml["audit"] = audit
    _register_builtin_plugins()
    _plugins.load()
    _create_cachedir()
    _garbage_collection()
    return _plugins.get(module, "modules")(fix=fix, no_cache=no_cache)
