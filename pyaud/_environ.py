"""
pyaud.environ
=============

Set up the environment variables for the current project.
"""
# pylint: disable=invalid-name,too-many-public-methods
from pathlib import Path as _Path

import appdirs as _appdirs
from environs import Env as _Env

from ._version import __version__


class Environ(_Env):
    """Package's environment variables."""

    @property
    def NAME(self) -> str:
        """Name of this package."""
        return __name__.split(".", maxsplit=1)[0]

    @property
    def PREFIX(self) -> str:
        """Prefix for variables which may turn out to be ambiguous."""
        return f"{self.NAME.upper()}_"

    @property
    def REPO(self) -> str:
        """The name of the repo that this is being run in."""
        return _Path.cwd().name

    @property
    def DATADIR(self) -> _Path:
        """Where to store persistent data."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "DATADIR", default=_Path(_appdirs.user_data_dir(self.NAME))
            )

    @property
    def CACHEDIR(self) -> _Path:
        """Where to store cache."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "CACHEDIR",
                default=_Path(
                    _appdirs.user_cache_dir(self.NAME, version=__version__)
                ),
            )

    @property
    def TIMED(self) -> bool:
        """Set ``timed`` to True without needing to pass arg."""
        with self.prefixed(self.PREFIX):
            return self.bool("TIMED", default=False)

    @property
    def FIX(self):
        """Set ``fix`` to True without needing to pass arg."""
        with self.prefixed(self.PREFIX):
            return self.bool("FIX", default=False)


#: package environment, both parsed from .env file (with set defaults
#: for missing keys), and static values
environ = Environ()


def initialize_dirs() -> None:
    """Ensure app dirs exist."""
    environ.DATADIR.mkdir(exist_ok=True, parents=True)
    environ.CACHEDIR.mkdir(exist_ok=True, parents=True)
