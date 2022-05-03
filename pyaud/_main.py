"""
pyaud._main
===========

Contains package entry point.
"""
import logging as _logging
from pathlib import Path as _Path

from . import _config, _data
from . import plugins as _plugins
from ._cli import Parser as _Parser
from ._config import configure_global as _configure_global
from ._default import register_default_plugins as _register_default_plugins
from ._indexing import files as _files
from ._locations import AppFiles as _AppFiles


def main() -> None:
    """Module entry point.

    Parse commandline arguments and run the selected choice from the
    dictionary of functions which matches the key.
    """
    app_files = _AppFiles()
    _configure_global(app_files)
    _register_default_plugins()
    _plugins.load()
    parser = _Parser()
    _data.record.read(app_files.durations_file)
    _config.load_config(app_files, parser.args.rcfile)
    _config.configure_logging(parser.args.verbose)
    _files.add_exclusions(*_config.toml["indexing"]["exclude"])
    _files.populate()
    _logging.getLogger(__name__).info(
        "commencing audit for %s in %s",
        app_files.user_project_dir.name,
        _Path.cwd(),
    )
    _plugins.get(parser.args.module)(
        clean=parser.args.clean,
        suppress=parser.args.suppress,
        fix=parser.args.fix,
        timed=parser.args.timed,
        no_cache=parser.args.no_cache,
    )
