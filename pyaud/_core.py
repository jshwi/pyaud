"""
pyaud._core
===========
"""
from __future__ import annotations

import os as _os
from pathlib import Path as _Path

from . import plugins as _plugins
from ._builtins import register_builtin_plugins as _register_builtin_plugins
from ._objects import NAME as _NAME
from ._objects import files as _files
from ._objects import toml as _toml
from ._version import __version__


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
    _files.populate_regex(exclude)
    _toml["audit"] = audit
    _create_cachedir()
    _register_builtin_plugins()
    _plugins.load()
    return _plugins.get(module, "modules")(fix=fix, no_cache=no_cache)
