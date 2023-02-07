"""
pyaud._default
==============
"""
import inspect as _inspect

from . import plugins as _plugins
from ._objects import NAME as _NAME
from ._objects import toml as _toml
from ._utils import colors as _colors


class _Audit(_plugins.Action):
    """Read from [audit] key in config."""

    def action(self, *args: str, **kwargs: bool) -> int:
        funcs = _toml["audit"]
        for func in funcs:
            if func in _plugins.registered():
                _colors.cyan.bold.print(f"\n{_NAME} {func}")
                _plugins.get(func)(**kwargs)

        return 0


class _Modules(_plugins.Action):
    """Display all available plugins and their documentation."""

    def action(self, *args: str, **kwargs: bool) -> int:
        # iterate over ``modules`` object to print documentation on
        # particular module or all modules, depending on argument passed
        # to commandline
        print()
        mapping = _plugins.mapping()
        for key in sorted(mapping):
            # keep a tab width of at least 1 space between key and
            # documentation
            # if all modules are printed adjust by the longest key
            tab = len(max(mapping, key=len)) + 1
            doc = _inspect.getdoc(mapping[key])
            if doc is not None:
                print(
                    "{}-- {}".format(
                        key.ljust(tab),
                        doc.splitlines()[0][:-1].replace("``", "`"),
                    )
                )

        return 0


def register_builtin_plugins() -> None:
    """Register builtin plugins."""
    _plugins.register("audit")(_Audit)
    _plugins.register("modules")(_Modules)
