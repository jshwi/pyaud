"""
pyaud._main
===========

Contains package entry point.
"""
from ._config import Parser as _Parser
from ._core import pyaud as _pyaud


def main() -> int:
    """Main function for package.

    :return: Exit status.
    """
    parser = _Parser()
    return _pyaud(
        parser.args.module,
        audit=parser.args.audit,
        exclude=parser.args.exclude,
        fix=parser.args.fix,
        no_cache=parser.args.no_cache,
    )
