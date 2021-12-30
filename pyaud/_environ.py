"""
pyaud.environ
=============

Set up the environment variables for the current project.
"""
# pylint: disable=invalid-name,too-many-public-methods
import typing as _t
from pathlib import Path as _Path

import appdirs as _appdirs
from environs import Env as _Env

from ._version import __version__


class _Environ(_Env):
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
    def DEFAULT_PLUGINS(self) -> _Path:
        """Default plugins that ship with this package."""
        return _Path(__file__).absolute().parent.parent / "pyaud_plugins"

    @property
    def SITE_PLUGINS(self) -> _Path:
        """Plugins which may exist in user's current working dir."""
        return _Path.cwd() / "plugins"

    @property
    def GITHUB_REPOSITORY_OWNER(self) -> _t.Optional[str]:
        """Env variable which may exist in a GitHub workflow."""
        return self.str("GITHUB_REPOSITORY_OWNER", default=None)

    @property
    def WHITELIST(self) -> _Path:
        """File for allowed "unused" code (usually false-positives)."""
        with self.prefixed(self.PREFIX):
            return self.path("WHITELIST", default=_Path("whitelist.py"))

    @property
    def COVERAGE_XML(self) -> _Path:
        """Location to store coverage.xml file."""
        with self.prefixed(self.PREFIX):
            return self.path("COVERAGE_XML", default=_Path("coverage.xml"))

    @property
    def REQUIREMENTS(self) -> _Path:
        """Where to find requirements.txt (or other named) file."""
        with self.prefixed(self.PREFIX):
            return self.path("REQUIREMENTS", default=_Path("requirements.txt"))

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
                "DATADIR",
                default=_Path(
                    _appdirs.user_cache_dir(self.NAME, version=__version__)
                ),
            )

    @property
    def DOCS(self) -> _Path:
        """Location of the user's documentation."""
        with self.prefixed(self.PREFIX):
            return self.path("DOCS", default=_Path("docs"))

    @property
    def BUILDDIR(self) -> _Path:
        """Where to put built documentation."""
        return self.path("BUILDDIR", default=self.DOCS / "_build")

    @property
    def GH_NAME(self) -> _t.Optional[str]:
        """Username of GH user."""
        with self.prefixed(self.PREFIX):
            return self.str("GH_NAME", default=self.GITHUB_REPOSITORY_OWNER)

    @property
    def GH_EMAIL(self) -> _t.Optional[str]:
        """Email of GH user."""
        with self.prefixed(self.PREFIX):
            return self.str("GH_EMAIL", default=None)

    @property
    def GH_TOKEN(self) -> _t.Optional[str]:
        """Authentication token of GH user."""
        with self.prefixed(self.PREFIX):
            return self.str("GH_TOKEN", default=None)

    @property
    def CODECOV_TOKEN(self) -> _t.Optional[str]:
        """Authentication token for codecov.io."""
        return self.str("CODECOV_TOKEN", default=None)

    @property
    def GH_REMOTE(self) -> _t.Optional[str]:
        """URL of repository remote."""
        default = None
        if all(
            i is not None for i in (self.GH_NAME, self.GH_EMAIL, self.GH_TOKEN)
        ):
            default = "https://{0}:{1}@github.com/{0}/{2}.git".format(
                self.GH_NAME, self.GH_TOKEN, self.REPO
            )
        with self.prefixed(self.PREFIX):
            return self.str("GH_REMOTE", default=default)

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
environ = _Environ()


def initialize_dirs() -> None:
    """Ensure app dirs exist."""
    environ.DATADIR.mkdir(exist_ok=True, parents=True)
    environ.CACHEDIR.mkdir(exist_ok=True, parents=True)
