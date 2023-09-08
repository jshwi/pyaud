"""
pyaud._core
===========
"""
from __future__ import annotations as _annotations

from . import _cachedir
from . import plugins as _plugins
from ._builtins import register_builtin_plugins as _register_builtin_plugins
from ._files import files as _files


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
    _files.populate(exclude)
    _register_builtin_plugins()
    _plugins.load()
    _cachedir.create()
    return _plugins.get(module)(fix=fix, no_cache=no_cache, audit=audit)
