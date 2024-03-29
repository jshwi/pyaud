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
from templatest.utils import VarPrefix, VarSeq, VarSeqSuffix

import pyaud

AUDIT = "audit"
FIX = "fix"
FIX_ALL = "fix-all"
INIT = "__init__.py"
TESTS = "tests"
UNPATCH_REGISTER_DEFAULT_PLUGINS = "unpatch_register_builtin_plugins"
PARAMS = "params"
STRFTIME = "%d%m%YT%H%M%S"

FixtureMain = t.Callable[..., int]
FixtureMakeTree = t.Callable[[Path, t.Dict[t.Any, t.Any]], None]
MockActionPluginList = t.Sequence[t.Type[pyaud.plugins.Action]]
FixtureMockActionPluginFactory = t.Callable[..., MockActionPluginList]
FixtureMockRepo = t.Callable[[KwArg(t.Callable[..., t.Any])], None]

plugin_name = VarSeq("plugin", suffix="-")
plugin_class = VarSeq("Plugin")
repo = VarSeq("repo")
python_file = VarSeqSuffix("file", suffix=".py")
flag = VarPrefix("--", slug="-")


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


class PluginTuple(t.NamedTuple):
    """Tuple of values to construct an ``Action`` plugin."""

    name: str
    action: t.Optional[t.Callable[..., int]] = None


class ContentHash(t.NamedTuple):
    """Tuple for string and its corresponding hash."""

    content_str: str
    content_hash: str
