"""
pyaud._environ
==============
"""
# pylint: disable=invalid-name,too-many-public-methods
import os as _os
import typing as _t
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
    def CONFIGDIR(self) -> _Path:
        """Where to store config."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "CONFIGDIR", default=_Path(_appdirs.user_config_dir(self.NAME))
            )

    @property
    def LOGDIR(self) -> _Path:
        """Where to store logs."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "LOGDIR", default=_Path(_appdirs.user_log_dir(self.NAME))
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

    @property
    def ENCODING(self) -> str:
        """Default encoding."""
        with self.prefixed(self.PREFIX):
            return self.str("ENCODING", default="utf-8")

    @property
    def GLOBAL_CONFIG_FILE(self) -> _Path:
        """Path to this package's toml config."""
        with self.prefixed(self.PREFIX):
            return self.CONFIGDIR / self.path(
                "GLOBAL_CONFIG_FILE", default=_Path(f"{self.NAME}.toml")
            )

    @property
    def GLOBAL_CONFIG_BAK_FILE(self) -> _Path:
        """Path to this package's toml config backup."""
        with self.prefixed(self.PREFIX):
            return self.CONFIGDIR / self.path(
                "GLOBAL_CONFIG_BAK_FILE",
                default=_Path(f".{self.NAME}.toml.bak"),
            )

    @property
    def USER_CONFIG_FILE(self) -> _Path:
        """Path to this package's rc config."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "RC_FILE", default=_Path.home() / f".{self.NAME}rc"
            )

    @property
    def PROJECT_CONFIG_FILE(self) -> _Path:
        """Path to this package's rc config."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "PROJECT_CONFIG_FILE", default=_Path.cwd() / f".{self.NAME}rc"
            )

    @property
    def PYPROJECT(self) -> _Path:
        """Path to pyproject.toml."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "PYPROJECT", default=_Path.cwd() / "pyproject.toml"
            )

    @property
    def FILECACHE_FILE(self) -> _Path:
        """Path to file cache file."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "FILECACHE_FILE", default=self.CACHEDIR / "files.json"
            )

    @property
    def DURATIONS_FILE(self) -> _Path:
        """Path to durations data file."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "DURATIONS_FILE", default=self.DATADIR / "durations.json"
            )

    @property
    def LOG_FILE(self) -> _Path:
        """Path to log file."""
        with self.prefixed(self.PREFIX):
            return self.path(
                "LOG_FILE", default=self.LOGDIR / f"{self.NAME}.log"
            )

    @property
    def CLEAN(self) -> bool:
        """Set ``clean`` to True without needing to pass arg."""
        with self.prefixed(self.PREFIX):
            return self.bool("CLEAN", default=False)

    @property
    def SUPPRESS(self) -> bool:
        """Set ``suppress`` to True without needing to pass arg."""
        with self.prefixed(self.PREFIX):
            return self.bool("SUPPRESS", default=False)

    @property
    def NO_CACHE(self) -> bool:
        """Set ``no_cache`` to True without needing to pass arg."""
        with self.prefixed(self.PREFIX):
            return self.bool("NO_CACHE", default=False)

    @property
    def RCFILE(self) -> _t.Optional[_t.Union[str, _os.PathLike]]:
        """Set default rcfile without needing to pass arg."""
        with self.prefixed(self.PREFIX):
            return self.path("RCFILE", default=None)

    @property
    def VERBOSE(self) -> int:
        """Set default verbosity without needing to pass arg."""
        with self.prefixed(self.PREFIX):
            return self.int("VERBOSE", default=0)


#: package environment, both parsed from .env file (with set defaults
#: for missing keys), and static values
environ = Environ()


def initialize_dirs() -> None:
    """Ensure app dirs exist."""
    environ.DATADIR.mkdir(exist_ok=True, parents=True)
    environ.CACHEDIR.mkdir(exist_ok=True, parents=True)
