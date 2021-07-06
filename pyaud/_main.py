"""
pyaud.main
==========
"""
import inspect as _inspect
import json as _json
import sys as _sys
from argparse import SUPPRESS as _SUPPRESS
from argparse import ArgumentParser as _ArgumentParser

from . import config as _config
from . import plugins as _plugins
from ._environ import NAME as _NAME
from ._environ import load_namespace as _load_namespace
from ._utils import colors as _colors
from ._utils import files as _files


class _Parser(_ArgumentParser):
    """Inherited ``argparse.ArgumentParser`` object for the package.

    Assign positional argument to ``self.module``. If there is a
    positional argument accompanying the ``modules`` argument assign it
    to ``self.positional``. If ``modules`` has been called run the
    ``self._module_help`` method for extended documentation on each
    individual module that can be called. If a valid positional argument
    has been called and ``sys.exit`` has not been raised by
    ``argparse.ArgumentParser`` help method then assign the chosen
    function to ``self.function`` to be called in ``pyaud.main``.

    :param prog: Name of the program.
    """

    def __init__(self, prog: str) -> None:
        super().__init__(prog=prog)
        self._mapping = _plugins.mapping()
        self._registered = _plugins.registered()
        self._returncode = 0
        self._add_arguments()
        self.args = self.parse_args()
        if self.args.module == "modules":
            _sys.exit(self._module_help())

    def _add_arguments(self) -> None:
        self.add_argument(
            "module",
            metavar="MODULE",
            choices=[*self._registered, "modules"],
            help="choice of module: [modules] to list all",
        )
        self.add_argument(
            "-c",
            "--clean",
            action="store_true",
            help="clean unversioned files prior to any process",
        )
        self.add_argument(
            "-d",
            "--deploy",
            action="store_true",
            help="include test and docs deployment after audit",
        )
        self.add_argument(
            "-f",
            "--fix",
            action="store_true",
            help="suppress and fix all fixable issues",
        )
        self.add_argument(
            "-s",
            "--suppress",
            action="store_true",
            help="continue without stopping for errors",
        )
        self.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="incrementally increase logging verbosity",
        )
        self.add_argument(
            "--rcfile",
            action="store",
            help="select file to override config hierarchy",
        )

        # pos argument following [modules] argument
        self.add_argument("pos", nargs="?", default=None, help=_SUPPRESS)

    def _print_module_docs(self):
        # iterate over ``modules`` object to print documentation on
        # particular module or all modules, depending on argument passed
        # to commandline
        print()
        for key in sorted(self._mapping):

            # keep a tab width of at least 1 space between key and
            # documentation
            # if all modules are printed adjust by the longest key
            tab = len(max(self._mapping, key=len)) + 1
            doc = _inspect.getdoc(self._mapping[key])
            if doc is not None:
                print(
                    "{}-- {}".format(
                        key.ljust(tab),
                        doc.splitlines()[0][:-1].replace("``", "`"),
                    )
                )

    def _print_module_summary(self):
        # print summary of module use if no module is selected or an
        # invalid module name os provided
        _colors.yellow.print(
            f"{_NAME} modules [<module> | all] for more on each module\n"
        )
        print(
            "modules = {}".format(
                _json.dumps(self._registered, indent=4, sort_keys=True)
            )
        )

    def _print_err(self):
        # announce selected module does not exist
        self._returncode = 0
        _colors.red.print(f"No such module: {self.args.pos}", file=_sys.stderr)

    def _module_help(self) -> int:
        self.print_usage()

        # module is selected or all has been entered
        if self.args.pos in (*self._mapping, "all"):

            # specific module has been entered for help output
            # filter the remaining modules from ``modules`` object
            if self.args.pos in self._mapping:
                positional = {self.args.pos: self._mapping[self.args.pos]}
                self._mapping.clear()
                self._mapping.update(positional)

            self._print_module_docs()

        # print module help summary if no argument to module has been
        # provided or argument has been provided but is not a valid
        # choice
        else:

            # argument has been provided which is not a valid option
            if self.args.pos is not None:
                self._print_err()

            self._print_module_summary()

        return self._returncode


def main() -> None:
    """Module entry point.

    Parse commandline arguments and run the selected choice from the
    dictionary of functions which matches the key.
    """
    _plugins.load()
    parser = _Parser(_colors.cyan.get(_NAME))
    _load_namespace()
    _config.load_config(parser.args.rcfile)
    _config.configure_logging(parser.args.verbose)
    _files.populate()
    _plugins.get(parser.args.module)(
        clean=parser.args.clean,
        suppress=parser.args.suppress,
        deploy=parser.args.deploy,
        fix=parser.args.fix,
    )
