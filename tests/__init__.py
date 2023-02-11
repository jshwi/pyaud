"""
tests
=====

Test package for ``pyaud``.
"""
# pylint: disable=too-few-public-methods
from __future__ import annotations

import typing as t
from pathlib import Path

from mypy_extensions import KwArg
from templatest.utils import VarSeq

import pyaud

DEFAULT_KEY = "default_key"
DOCS = "docs"
FILE: str = "file.py"
FILES = "files"
FIX = "fix"
FIXER = "fixer"
FIX_ALL = "fix-all"
FIX_FILE = "fix-file"
FORMAT = "format"
FORMAT_DOCS = "format-docs"
INIT = "__init__.py"
KEY = "key"
LINT = "lint"
MODULES = "modules"
OS_GETCWD = "os.getcwd"
REPO = "repo"
TESTS = "tests"
UNPATCH_REGISTER_DEFAULT_PLUGINS = "unpatch_register_builtin_plugins"
VALUE = "value"
WHITELIST_PY = "whitelist.py"
PARAMS = "params"
STRFTIME = "%d%m%YT%H%M%S"

FixtureMain = t.Callable[..., int]
FixtureMakeTree = t.Callable[[Path, t.Dict[t.Any, t.Any]], None]
FileHashDict = t.Dict[str, str]
ClsDict = t.Dict[str, FileHashDict]
CommitDict = t.Dict[str, ClsDict]
CacheDict = t.Dict[str, CommitDict]
CacheUnion = t.Union[CacheDict, CommitDict, ClsDict, FileHashDict]
MockActionPluginList = t.Sequence[t.Type[pyaud.plugins.Action]]
FixtureMockActionPluginFactory = t.Callable[..., MockActionPluginList]
FixtureMockRepo = t.Callable[[KwArg(t.Callable[..., t.Any])], None]
FixtureMockSpallSubprocessOpenProcess = t.Callable[[int], None]

plugin_name = VarSeq("plugin", suffix="-")
plugin_class = VarSeq("Plugin")


class MockPluginType(pyaud.plugins.Plugin):
    """PluginType object."""


class MockCachedPluginType(MockPluginType):
    """PluginType object with ``cache`` set to True."""

    cache = True


class Tracker:
    """Track calls in mocked functions."""

    def __init__(self) -> None:
        self._called = False
        self.args: list[tuple[str, ...]] = []
        self.kwargs: list[dict[str, bool]] = []

    def was_called(self) -> bool:
        """Confirm whether object was called or not.

        :return: Was object called? True or False.
        """
        return self._called

    def __call__(self, *args: str, **kwargs: bool) -> None:
        """Call the object, update its fields, and return values passed.

        Fields to update:

            - ``_called``: Can be confirmed by calling ``was_called``
            - args: Args passed to called instance.
            - kwargs: Kwargs passed to called instance.

        Return values can be appended to ``return_values`` manually.

        :param args: Args passed to instance.
        :param kwargs: Kwargs passed to instance.
        :return: Values appended to ``return_values`` to mock.
        """
        self._called = True
        self.args.append(args)
        self.kwargs.append(kwargs)


class StrategyMockPlugin(MockCachedPluginType):
    """Create a base class that contains a `__call__` method that only
    returns an exit-code for a successful audit or a failed one."""

    cache = True
    cache_all = False

    def __call__(self, *args: str, **kwargs: bool) -> int:
        return 0


class MockAudit(pyaud.plugins.Audit):
    """Nothing to do."""

    def audit(self, *_: str, **__: bool) -> int:  # type: ignore
        """Nothing to do."""


class PluginTuple(t.NamedTuple):
    """Tuple of values to construct an ``Action`` plugin."""

    name: str
    exe: t.Optional[str] = None
    action: t.Optional[t.Callable[..., int]] = None
