"""
pyaud._default
==============
"""
from . import _config
from . import plugins as _plugins
from ._locations import NAME as _NAME
from ._utils import colors as _colors


class _Audit(_plugins.Action):
    """Read from [audit] key in config."""

    def action(self, *args: str, **kwargs: bool) -> int:
        funcs = _config.toml["audit"]["modules"]
        for func in funcs:
            if func in _plugins.registered():
                _colors.cyan.bold.print(f"\n{_NAME} {func}")
                _plugins.get(func)(**kwargs)

        return 0


def register_default_plugins() -> None:
    """Register default plugins."""
    _plugins.register("audit")(_Audit)
