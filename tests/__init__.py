"""Register tests as a package.

Imports from ``tests.static`` and ``tests.utils``
"""
import os
import re
from typing import Any, Callable, Dict, Tuple, Union

import pyaud

from . import files

REAL_REPO = os.path.dirname(os.path.dirname(__file__))


class PyaudTestError(Exception):
    """Error to be purposely raised within the testing environment."""


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
    def regex(out: str) -> str:
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
        return tuple([self.regex(r) for r in self.capsys.readouterr()])

    def _readouterr_index(self, idx: int) -> str:
        readouterr = self.readouterr()
        return readouterr[idx]

    def stdout(self) -> str:
        """Return stdout without referencing the tuple indices.

        :return: Stdout.
        """
        return self._readouterr_index(0)

    def stderr(self) -> str:
        """Return stderr without referencing the tuple indices.

        :return: Stderr.
        """
        return self._readouterr_index(1)


class CallStatus:  # pylint: disable=too-few-public-methods
    """Factory for producing functions that only return an exit-status.

    :param module_name: Name for the function.
    :param returncode:  Exit status for the function.
    """

    def __init__(self, module_name: str, returncode: int = 0) -> None:
        self._module_name = module_name
        self._returncode = returncode
        setattr(self, self._module_name, self._factory())

    def _factory(self) -> Any:
        def _func(**_: Any) -> int:
            return self._returncode

        _func.__name__ = self._module_name
        return _func

    def func(self) -> Any:
        """Get the dynamically named function."""
        return getattr(self, self._module_name)


class MakeWritten:
    """Create files containing text."""

    @staticmethod
    def _write(path: Union[bytes, str, os.PathLike], content: str) -> None:
        with open(path, "w") as fout:
            fout.write(content)

    @classmethod
    def readme(cls) -> None:
        """Make a README.rst file for testing."""
        cls._write(pyaud.environ.env["README_RST"], files.README_RST)

    @classmethod
    def index_rst(cls) -> None:
        """Make a docs/index.rst file for testing."""
        cls._write(
            os.path.join(pyaud.environ.env["DOCS"], "index.rst"),
            files.INDEX_RST,
        )

    @classmethod
    def readme_toc(cls) -> None:
        """Make a docs/readme.rst file for testing."""
        cls._write(
            os.path.join(pyaud.environ.env["DOCS"], "readme.rst"),
            files.README_RST,
        )

    @classmethod
    def repo_toc(cls) -> None:
        """Make a docs/repo.rst file for testing."""
        cls._write(os.path.join(pyaud.environ.env["TOC"]), files.DEFAULT_TOC)

    @classmethod
    def pipfile_lock(cls) -> None:
        """Make a Pipfile.lock file for testing."""
        cls._write(
            os.path.join(pyaud.environ.env["PIPFILE_LOCK"]), files.PIPFILE_LOCK
        )


class MakeProjectTree:
    """Make directory tree structure.

    :param make_tree:   Fixture returning function to recursively create
                        directories and files.
    """

    def __init__(self, make_tree: Any) -> None:
        self.make_tree = make_tree

    def package(self) -> None:
        """Make a Python package for testing."""
        self.make_tree(
            pyaud.environ.env["PROJECT_DIR"], {"repo": {"__init__.py": None}}
        )

    def docs_conf(self) -> None:
        """Make a docs/conf.py file for testing."""
        self.make_tree(
            pyaud.environ.env["PROJECT_DIR"], {"docs": {"conf.py": None}}
        )

    def toc(self) -> None:
        """Make a docs/repo.rst file for testing."""
        self.make_tree(
            pyaud.environ.env["PROJECT_DIR"], {"docs": {"repo.rst": None}}
        )

    def mock_virtualenv(self) -> None:
        """Make a fake ``venv`` directory."""
        venv: Dict[str, Any] = {
            "venv": {
                "pyvenv.cfg": None,
                "bin": {},
                "include": {},
                "share": {},
                "src": {},
                "lib": {"python3.8": {"site-packages": {"six.py": None}}},
                "lib64": "lib",
            }
        }
        self.make_tree(pyaud.environ.env["PROJECT_DIR"], venv)

    def be8a443_files(self) -> None:
        """Create .py files that would be scanned on commit be8a443."""
        self.make_tree(
            pyaud.environ.env["PROJECT_DIR"],
            {
                "tests": {"conftest.py": None, "files.py": None},
                "pyaud": {"src": {"__init__.py": None, "modules.py": None}},
            },
        )
