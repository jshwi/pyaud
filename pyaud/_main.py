"""
pyaud._main
===========

Contains package entry point.
"""

from . import _config
from . import plugins as _plugins
from ._cli import Parser as _Parser
from ._default import register_default_plugins as _register_default_plugins
from ._indexing import files as _files


def main() -> None:
    """Module entry point.

    Parse commandline arguments and run the selected choice from the
    dictionary of functions which matches the key.
    """
    _register_default_plugins()
    _plugins.load()
    parser = _Parser()
    _files.add_exclusions(*_config.toml["indexing"]["exclude"])
    _files.populate()
    _plugins.get(parser.args.module)(
        suppress=parser.args.suppress,
        fix=parser.args.fix,
        no_cache=parser.args.no_cache,
    )
