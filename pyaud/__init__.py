"""
Select module with commandline arguments.

The word ``function`` and ``module`` are used interchangeably in this
package.
"""
import argparse
import contextlib
import inspect
import os
import sys
from typing import Any, Callable, List, Optional

from .src import (
    EnterDir,
    Git,
    HashCap,
    LineSwitch,
    PyaudSubprocessError,
    Subprocess,
    Tally,
    check_command,
    colors,
    config,
    environ,
    get_branch,
    get_logger,
    modules,
    print_command,
    pyitems,
    write_command,
)

__version__ = "1.3.0"

MODULES = {
    m[0].replace("make_", ""): m[1]
    for m in inspect.getmembers(modules)
    if m[0].startswith("make_") and inspect.isfunction(m[1])
}


class Parser(argparse.ArgumentParser):
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
        self.module_list = [m.replace("_", "-") for m in list(MODULES)]
        self._add_arguments()
        self.args = self.parse_args()
        self.module = self.args.module

        if self.module == "modules":
            self._print_module_help()
        else:
            self.function = MODULES[self.module.replace("-", "_")]

        self.path = os.path.abspath(self.args.path)

    def _add_arguments(self) -> None:
        self.add_argument(
            "module",
            metavar="MODULE",
            choices=self.module_list + ["modules"],
            help="choice of module: ``modules`` to list all options",
        )
        self.add_argument(
            "positional", nargs="?", default=None, help=argparse.SUPPRESS
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
        colors.yellow.print(
            "``pyaud modules MODULE`` for more on each module or "
            "``pyaud modules all``"
        )
        print(
            "\nMODULES = [\n"
            + "\n".join([f"    {m}," for m in self.module_list])
            + "\n]"
        )

    def _populate_functions(self) -> List[Callable[..., Any]]:
        funcs = []
        try:
            funcs.append(MODULES[self.args.positional])

        except KeyError:
            if self.args.positional == "all":
                funcs.extend([MODULES[k] for k in MODULES])

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
            for func in funcs:
                print_command(func)
                print(self._get_docs(func))
        else:
            with contextlib.redirect_stdout(sys.stderr):
                colors.red.print(f"No such module: ``{self.args.positional}``")
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
    colors.populate_colors()
    parser = Parser(colors.cyan.get(__name__.split(".")[0]))
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
    pyitems.get_files()
    pyitems.exclude_virtualenv()
    pyitems.exclude_unversioned()
    pyitems.get_file_paths()
    environ.env["BRANCH"] = get_branch()
    parser.function()


__all__ = [
    "EnterDir",
    "Git",
    "HashCap",
    "LineSwitch",
    "PyaudSubprocessError",
    "Subprocess",
    "Tally",
    "check_command",
    "colors",
    "config",
    "environ",
    "get_branch",
    "get_logger",
    "modules",
    "print_command",
    "pyitems",
    "write_command",
]
