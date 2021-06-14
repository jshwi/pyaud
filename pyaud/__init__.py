"""Select module with commandline arguments.

The word ``function`` and ``module`` are used interchangeably in this
package.
"""
import inspect
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from typing import Any, Dict

from . import config, environ, modules, utils

__version__ = "1.3.0"

MODULES = {
    k.replace("make_", "").replace("_", "-"): v
    for k, v in inspect.getmembers(modules, inspect.isfunction)
    if k.startswith("make_")
}
AUDIT_ARGS = (
    "format",
    "format-str",
    "format-docs",
    "format-str",
    "imports",
    "typecheck",
    "unused",
    "lint",
    "coverage",
    "readme",
    "docs",
)


class _Parser(ArgumentParser):
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
        self._modules: Dict[str, Any] = dict(MODULES)
        self._returncode = 0
        self._add_arguments()
        self.args = self.parse_args()
        if self.args.module == "modules":
            sys.exit(self._module_help())

    def _add_arguments(self) -> None:
        self.add_argument(
            "module",
            metavar="MODULE",
            choices=[*MODULES, "modules"],
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
        self.add_argument("pos", nargs="?", default=None, help=SUPPRESS)

    def _print_module_docs(self):
        # iterate over ``modules`` object to print documentation on
        # particular module or all modules, depending on argument passed
        # to commandline
        print()
        for key in sorted(self._modules):

            # keep a tab width of at least 1 space between key and
            # documentation
            # if all modules are printed adjust by the longest key
            tab = len(max(self._modules, key=len)) + 1
            doc = inspect.getdoc(self._modules[key])
            if doc is not None:
                print(
                    "{}-- {}".format(
                        key.ljust(tab),
                        doc.splitlines()[0][:-1].replace("``", "`"),
                    )
                )

    @staticmethod
    def _print_module_summary():
        # print summary of module use if no module is selected or an
        # invalid module name os provided
        utils.colors.yellow.print(
            f"{__name__} modules [<module> | all] for more on each module\n"
        )
        print(
            "MODULES = {}".format(
                json.dumps(list(MODULES), indent=4, sort_keys=True)
            )
        )

    def _print_err(self):
        # announce selected module does not exist
        self._returncode = 0
        utils.colors.red.print(
            f"No such module: {self.args.pos}", file=sys.stderr
        )

    def _module_help(self) -> int:
        self.print_usage()

        # module is selected or all has been entered
        if self.args.pos in (*self._modules, "all"):

            # specific module has been entered for help output
            # filter the remaining modules from ``modules`` object
            if self.args.pos in self._modules:
                positional = {self.args.pos: self._modules[self.args.pos]}
                self._modules.clear()
                self._modules.update(positional)

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


def audit(**kwargs: bool) -> None:
    """Run all modules for complete package audit.

    :param kwargs:  Pass keyword arguments to audit submodule.
    :key clean:     Insert clean module to the beginning of module list
                    to remove all unversioned files before executing
                    rest of audit.
    :key deploy:    Append deploy modules (docs and coverage) to end of
                    modules list to deploy package data after executing
                    audit.
    :return:        Exit status.
    """
    funcs = list(AUDIT_ARGS)
    if kwargs.get("clean", False):
        funcs.insert(0, "clean")

    if kwargs.get("deploy", False):
        funcs.append("deploy")

    for func in funcs:
        utils.colors.cyan.bold.print(f"\n{__name__} {func}")
        MODULES[func](**kwargs)


def main() -> None:
    """Module entry point.

    Parse commandline arguments and run the selected choice from the
    dictionary of functions which matches the key.
    """
    MODULES[audit.__name__] = audit
    parser = _Parser(utils.colors.cyan.get(__name__))
    environ.load_namespace()
    config.load_config(parser.args.rcfile)
    config.configure_logging(parser.args.verbose)
    utils.tree.populate()
    MODULES[parser.args.module](
        clean=parser.args.clean,
        suppress=parser.args.suppress,
        deploy=parser.args.deploy,
        fix=parser.args.fix,
    )
