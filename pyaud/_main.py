"""
pyaud._main
===========

Contains package entry point.
"""
import os as _os
from pathlib import Path as _Path

from . import _config
from . import plugins as _plugins
from ._cli import Parser as _Parser
from ._default import register_default_plugins as _register_default_plugins
from ._indexing import files as _files
from ._locations import NAME as _NAME
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


def main() -> None:
    """Module entry point.

    Parse commandline arguments and run the selected choice from the
    dictionary of functions which matches the key.
    """
    _os.environ["PYAUD_CACHE"] = _os.environ.get("PYAUD_CACHE", ".pyaud_cache")
    _register_default_plugins()
    _plugins.load()
    parser = _Parser()
    _files.add_exclusions(*_config.toml["indexing"]["exclude"])
    _files.populate()
    _create_cachedir()
    _plugins.get(parser.args.module)(
        suppress=parser.args.suppress,
        fix=parser.args.fix,
        no_cache=parser.args.no_cache,
    )
