"""
pyaud._main
===========

Contains package entry point.
"""
import sys as _sys

from . import messages as _messages
from ._config import Parser as _Parser
from ._core import pyaud as _pyaud
from ._objects import colors as _colors


def main() -> int:
    """Main function for package.

    :return: Exit status.
    """
    try:
        parser = _Parser()
        return _pyaud(
            parser.args.module,
            audit=parser.args.audit,
            exclude=parser.args.exclude,
            fix=parser.args.fix,
            no_cache=parser.args.no_cache,
        )
    except KeyboardInterrupt:
        _sys.exit(_colors.red.bold.get(f"\n{_messages.KEYBOARD_INTERRUPT}"))
