"""Register tests as a package.

Imports from ``tests.static`` and ``tests.utils``
"""
import os
import re
from typing import Any, Tuple

import pyaud.config

from . import files

REAL_REPO = os.path.dirname(os.path.dirname(__file__))
FILES = "file.py"
PUSHING_SKIPPED = "Pushing skipped"
REPO = "repo"
GH_NAME = "test_user"
GH_EMAIL = "test_email.com"
GH_TOKEN = "token"
INITIAL_COMMIT = "Initial commit"
NO_ISSUES = "Success: no issues found in 1 source files"
INIT = "__init__.py"
CONFPY = "conf.py"
DEBUG = pyaud.config.DEBUG
INFO = pyaud.config.INFO
WARNING = pyaud.config.WARNING
ERROR = pyaud.config.ERROR
CRITICAL = pyaud.config.CRITICAL


class NoColorCapsys:
    """Capsys but with a regex to remove ANSI escape codes.

    Class is preferable for this as we can instantiate the instance
    as a fixture that also contains the same attributes as capsys

    We can make sure that the class is instantiated without executing
    capsys immediately thus losing control of what stdout and stderr
    we are to capture

    :param capsys: Capture and return stdout and stderr stream.
    """

    def __init__(self, capsys: Any) -> None:
        self.capsys = capsys

    @staticmethod
    def _regex(out: str) -> str:
        """Replace ANSI color codes with empty strings.

        Remove all escape codes. Preference is to test colored output
        this way as colored strings can be tricky and the effort in
        testing their validity really isn't worthwhile. It is also
        hard to  read expected strings when they contain the codes.

        :param out: String to strip of ANSI escape codes
        :return:    Same string but without ANSI codes
        """
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", out)

    def readouterr(self) -> Tuple[str, ...]:
        """Call as capsys ``readouterr`` but remove ANSI color-codes.

        :return:    A tuple (just like the capsys) containing stdout in
                    the first index and stderr in the second
        """
        return tuple([self._regex(r) for r in self.capsys.readouterr()])

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
