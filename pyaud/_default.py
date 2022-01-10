"""
pyaud._default
==============
"""
from . import config as _config
from . import plugins as _plugins
from ._environ import environ as _environ
from ._utils import colors as _colors
from ._utils import git as _git


class _Audit(_plugins.Action):
    """Read from [audit] key in config."""

    def action(self, *args: str, **kwargs: bool) -> int:
        funcs = _config.toml["audit"]["modules"]
        if kwargs.get("clean", False):
            funcs.insert(0, "clean")

        for func in funcs:
            if func in _plugins.registered():
                _colors.cyan.bold.print(f"\n{_environ.NAME} {func}")
                _plugins.get(func)(**kwargs)

        return 0


class _GenerateRCFile(_plugins.Action):
    """Print rcfile to stdout.

    Print rcfile to stdout, so it may be piped to chosen filepath.
    """

    cache = False

    def action(self, *args: str, **kwargs: bool) -> int:
        print(_config.toml.dumps(_config.DEFAULT_CONFIG), end="")
        return 0


class _Clean(_plugins.Action):
    """Remove all unversioned package files recursively."""

    cache = False

    def action(self, *args: str, **kwargs: bool) -> int:
        exclude = _config.toml["clean"]["exclude"]
        return _git.clean(
            "-fdx", *[f"--exclude={e}" for e in exclude], **kwargs
        )


def register_default_plugins() -> None:
    """Register default plugins."""
    _plugins.register("audit")(_Audit)
    _plugins.register("generate-rcfile")(_GenerateRCFile)
    _plugins.register("clean")(_Clean)
