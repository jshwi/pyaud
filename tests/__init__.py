"""
tests
=====

Test package for ``pyaud``.
"""
import re
import typing as t
from pathlib import Path

from gitspy import Git

import pyaud

FILES: str = "file.py"
REPO = "repo"
GH_NAME = "test_user"
GH_EMAIL = "test_email.com"
INITIAL_COMMIT = "Initial commit"
INIT = "__init__.py"
CONFPY = "conf.py"
LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
DEBUG = LEVELS[0]
INFO = LEVELS[1]
WARNING = LEVELS[2]
ERROR = LEVELS[3]
CRITICAL = LEVELS[4]
SP_OPEN_PROC = "spall.Subprocess._open_process"
README = Path("README.rst")
PYAUD_PLUGINS_PLUGINS = "pyaud.plugins._plugins"
TYPE_ERROR = "can only register one of the following:"
PYPROJECT = "pyproject.toml"
GITIGNORE = ".gitignore"
PYAUD_FILES_POPULATE = "pyaud.files.populate"
OS_GETCWD = "os.getcwd"
WHITELIST_PY = "whitelist.py"
COMMIT = "7c57dc943941566f47b9e7ee3208245d0bcd7656"
git = Git()


class NoColorCapsys:
    """Capsys but with a regex to remove ANSI escape codes.

    Class is preferable for this as we can instantiate the instance
    as a fixture that also contains the same attributes as capsys

    We can make sure that the class is instantiated without executing
    capsys immediately thus losing control of what stdout and stderr
    we are to capture

    :param capsys: Capture and return stdout and stderr stream.
    """

    def __init__(self, capsys: t.Any) -> None:
        self.capsys = capsys

    @staticmethod
    def _regex(out: str) -> str:
        """Replace ANSI color codes with empty strings.

        Remove all escape codes. Preference is to test colored output
        this way as colored strings can be tricky and the effort in
        testing their validity really isn't worthwhile. It is also
        hard to  read expected strings when they contain the codes.

        :param out: String to strip of ANSI escape codes
        :return: Same string but without ANSI codes
        """
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", out)

    def readouterr(self) -> t.Tuple[str, ...]:
        """Call as capsys ``readouterr`` but remove ANSI color-codes.

        :return: A tuple (just like the capsys) containing stdout in the
            first index and stderr in the second
        """
        return tuple(  # pylint: disable=consider-using-generator
            [self._regex(r) for r in self.capsys.readouterr()]
        )

    def stdout(self) -> str:
        """Return stdout without referencing the tuple indices.

        :return: Stdout.
        """
        return self.readouterr()[0]

    def stderr(self) -> str:
        """Return stderr without referencing the tuple indices.

        :return: Stderr.
        """
        return self.readouterr()[1]


class MockPluginType(pyaud.plugins.Plugin):
    """PluginType object."""


class MockCachedPluginType(MockPluginType):
    """PluginType object with ``cache`` set to True."""

    cache = True


class Tracker:  # pylint: disable=too-few-public-methods
    """Track calls in mocked functions."""

    def __init__(self) -> None:
        self._called = False
        self.args: t.List[t.Tuple[str, ...]] = []
        self.kwargs: t.List[t.Dict[str, t.Any]] = []

    def was_called(self) -> bool:
        """Confirm whether object was called or not.

        :return: Was object called? True or False.
        """
        return self._called

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> None:
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

    def __call__(self, *args, **kwargs):
        return 0
