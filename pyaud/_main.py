"""
pyaud._main
===========

Contains package entry point.
"""
import sys as _sys
from os import environ as _e

from rich.console import Console as _Console

from ._config import Parser as _Parser
from ._core import pyaud as _pyaud


def main() -> int:
    """Main function for package.

    :return: Exit status.
    """
    if _e.get("PYAUD_DEBUG", None) != "1":
        err = _Console(soft_wrap=False, stderr=True)
        _sys.excepthook = lambda x, y, _: err.print(
            f"[red bold]{x.__name__}[/red bold]: {y}"
        )

    parser = _Parser()
    return _pyaud(
        parser.args.module,
        audit=parser.args.audit,
        exclude=parser.args.exclude,
        fix=parser.args.fix,
        no_cache=parser.args.no_cache,
    )
