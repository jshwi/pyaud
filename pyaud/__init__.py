"""
Select module with commandline arguments.

The word ``function`` and ``module`` are used interchangeably in this
package.
"""
import contextlib
import inspect
import os
import sys
from argparse import SUPPRESS, ArgumentParser
from typing import Any, Callable, Dict, Optional

from . import config, environ, modules, utils

__version__ = "1.3.0"

MODULES = {
    k.replace("make_", "").replace("_", "-"): v
    for k, v in inspect.getmembers(modules, inspect.isfunction)
    if k.startswith("make_")
}


class Parser(ArgumentParser):
    """Inherited ``argparse.ArgumentParser`` object for the package.
    Assign positional argument to ``self.module``. If there is a
    positional argument accompanying the ``modules`` argument assign it
    to ``self.positional``. If ``modules`` has been called run the
    ``self._module_help`` method for extended documentation on each
    individual module that can be called. If a valid positional argument
    has been called and ``sys.exit`` has not been raised by
    ``argparse.ArgumentParser`` help method then assign the chosen
    function to ``self.function`` to be called in ``pyaud.main``.

    :param prog:    Name of the program.
    """

    def __init__(self, prog: str) -> None:
        super().__init__(prog=prog)
        self.module_list = list(MODULES)
        self._add_arguments()
        self.args = self.parse_args()
        self.module = self.args.module

        if self.module == "modules":
            self._print_module_help()

        self.path = os.path.abspath(self.args.path)

    def _add_arguments(self) -> None:
        self.add_argument(
            "module",
            metavar="MODULE",
            choices=self.module_list + ["modules"],
            help="choice of module: ``modules`` to list all options",
        )
        self.add_argument("positional", nargs="?", default=None, help=SUPPRESS)
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
            "--path",
            action="store",
            default=os.getcwd(),
            help="set alternative path to present working dir",
        )

    def _list_modules(self) -> None:
        utils.colors.yellow.print(
            f"``{__name__} modules MODULE`` for more on each module or "
            f"``{__name__} modules all``"
        )
        print(
            "\nMODULES = [\n"
            + "\n".join([f"    {m}," for m in self.module_list])
            + "\n]"
        )

    def _populate_functions(self) -> Dict[str, Callable[..., Any]]:
        funcs = {}
        try:
            funcs.update({self.args.positional: MODULES[self.args.positional]})

        except KeyError:
            if self.args.positional == "all":
                funcs.update(dict(MODULES))

        return funcs

    @staticmethod
    def _get_docs(func: Callable[..., Any]) -> str:
        docs = []
        docstring: Optional[str] = func.__doc__
        if docstring is not None:
            for line in docstring.splitlines():
                line = line.lstrip()
                if line and line[0] == ":":
                    break

                docs.append(line)

        return "\n".join(docs)

    def _print_module_info(self) -> None:
        funcs = self._populate_functions()
        if funcs:
            for key, value in funcs.items():
                print()
                utils.colors.cyan.bold.print(f"pyaud {key}")
                print(self._get_docs(value))
        else:
            with contextlib.redirect_stdout(sys.stderr):
                utils.colors.red.print(
                    f"No such module: ``{self.args.positional}``"
                )
                self._list_modules()
                sys.exit(1)

        sys.exit(0)

    def _print_module_help(self) -> None:
        self.print_usage()
        if self.args.positional:
            self._print_module_info()

        self._list_modules()
        sys.exit(0)

    def set_loglevel(self):
        """Set loglevel via commandline and override environment
        variable if one has been set.
        """
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        levels_index = 1
        if "LOG_LEVEL" in environ.env:
            levels_index = levels.index(environ.env["LOG_LEVEL"])

        environ.env["LOG_LEVEL"] = levels[
            max(0, levels_index - self.args.verbose)
        ]


def main() -> None:
    """Module entry point. Parse commandline arguments and run the
    selected choice from the dictionary of functions which matches the
    key.
    """
    parser = Parser(utils.colors.cyan.get(__name__))
    environ.env.store["PROJECT_DIR"] = parser.args.path
    environ.env.update(
        dict(
            PROJECT_DIR=parser.path,
            CLEAN=parser.args.clean,
            SUPPRESS=parser.args.suppress,
            DEPLOY=parser.args.deploy,
        )
    )
    environ.load_namespace()
    parser.set_loglevel()
    utils.pyitems.get_files()
    utils.pyitems.exclude_virtualenv()
    utils.pyitems.exclude_unversioned()
    utils.pyitems.get_file_paths()
    environ.env["BRANCH"] = utils.get_branch()
    MODULES[parser.args.module]()
