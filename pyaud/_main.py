"""
pyaud.main
==========
"""
import logging as _logging
from pathlib import Path as _Path

from . import _data
from . import config as _config
from . import plugins as _plugins
from ._cli import Parser as _Parser
from ._default import register_default_plugins as _register_default_plugins
from ._environ import environ as _environ
from ._environ import initialize_dirs as _initialize_dirs
from ._indexing import files as _files
from ._utils import colors as _colors


def main() -> None:
    """Module entry point.

    Parse commandline arguments and run the selected choice from the
    dictionary of functions which matches the key.
    """
    _environ.read_env()
    _register_default_plugins()
    _plugins.load()
    parser = _Parser(_colors.cyan.get(_environ.NAME))
    _initialize_dirs()
    _data.read(_data.record, _environ.DURATIONS_FILE)
    _config.load_config(parser.args.rcfile)
    _config.configure_logging(parser.args.verbose)
    _files.add_exclusions(*_config.toml["indexing"]["exclude"])
    _files.populate()
    _logging.getLogger(__name__).info(
        "Commencing audit for %s in %s", _environ.REPO, _Path.cwd()
    )
    _plugins.get(parser.args.module)(
        clean=parser.args.clean,
        suppress=parser.args.suppress,
        deploy=parser.args.deploy,
        fix=parser.args.fix,
        timed=parser.args.timed,
        no_cache=parser.args.no_cache,
    )
