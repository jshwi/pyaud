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

PLUGIN_NAME = VarSeq("plugin", suffix="-")
PLUGIN_CLASS = VarSeq("Plugin")

AUDIT = "audit"
COMMIT = "7c57dc943941566f47b9e7ee3208245d0bcd7656"
CONFPY = "conf.py"
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
TYPE_ERROR = "can only register one of the following:"
UNPATCH_REGISTER_DEFAULT_PLUGINS = "unpatch_register_builtin_plugins"
VALUE = "value"
WHITELIST_PY = "whitelist.py"
PARAMS = "params"

MockMainType = t.Callable[..., int]
MakeTreeType = t.Callable[[Path, t.Dict[t.Any, t.Any]], None]
FileHashDict = t.Dict[str, str]
ClsDict = t.Dict[str, FileHashDict]
CommitDict = t.Dict[str, ClsDict]
CacheDict = t.Dict[str, CommitDict]
CacheUnion = t.Union[CacheDict, CommitDict, ClsDict, FileHashDict]
MockActionPluginList = t.Sequence[t.Type[pyaud.plugins.Action]]
MockActionPluginFactoryType = t.Callable[..., MockActionPluginList]
FixtureMockRepo = t.Callable[[KwArg(t.Callable[..., t.Any])], None]
FixtureMockSpallSubprocessOpenProcess = t.Callable[[int], None]


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


class NotSubclassed:
    """Nothing to do."""


class MockAudit(pyaud.plugins.Audit):
    """Nothing to do."""

    def audit(self, *_: str, **__: bool) -> int:
        """Nothing to do."""
        return 1


class PluginTuple(t.NamedTuple):
    """Tuple of values to construct an ``Action`` plugin."""

    name: str
    exe: t.Optional[str] = None
    action: t.Optional[t.Callable[..., int]] = None
