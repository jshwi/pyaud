"""
pyaud._default
==============
"""
import inspect as _inspect
import typing as _t

from . import messages as _messages
from . import plugins as _plugins
from ._objects import NAME as _NAME
from ._objects import colors as _colors


class _Audit(_plugins.Action):
    """Read from [audit] key in config."""

    def action(self, *args: str, **kwargs: _t.Any) -> int:
        audit = kwargs["audit"]
        returncode = 0
        message = _colors.green.bold.get(_messages.AUDIT_PASSED)
        bullet = _colors.cyan.get("-")
        _colors.cyan.bold.print(f"\n{_NAME} {self.name}")
        _colors.green.underline.print(_messages.AUDIT_RUNNING)
        results = []
        print(f"{bullet} " + f"\n{bullet} ".join(audit))
        for func in audit:
            symbol = _colors.green.get("\u2713")
            if func in _plugins.registered():
                _colors.cyan.bold.print(f"\n{_NAME} {func}")
                if _plugins.get(func)(**kwargs):
                    symbol = _colors.red.get("\u2716")
                    returncode = 1
                    message = _colors.red.bold.get(_messages.AUDIT_FAILED)

            results.append(f"{func} {symbol}")

        print(message)
        print(f"{bullet} " + f"\n{bullet} ".join(results))
        return returncode


class _Modules(_plugins.Action):
    """Display all available plugins and their documentation."""

    def action(self, *args: str, **kwargs: _t.Any) -> int:
        print()
        mapping = _plugins.mapping()
        for key in sorted(mapping):
            doc = _inspect.getdoc(mapping[key])
            if doc is not None:
                print(
                    "{}-- {}".format(
                        key.ljust(len(max(mapping, key=len)) + 1),
                        doc.splitlines()[0][:-1].replace("``", "`"),
                    )
                )

        return 0


def register_builtin_plugins() -> None:
    """Register builtin plugins."""
    _plugins.register("audit")(_Audit)
    _plugins.register("modules")(_Modules)
