"""
pyaud.environ
=============

Set up the environment variables for the current project.
"""
from __future__ import annotations

import os as _os
import typing as _t
from collections.abc import MutableMapping as _MutableMapping
from pathlib import Path as _Path

import appdirs as _appdirs
import dotenv as _dotenv

from ._version import __version__

NAME = __name__.split(".", maxsplit=1)[0]
DOCS = _Path("docs")
PIPFILE_LOCK = _Path("Pipfile.lock")
PLUGINS = _Path("plugins")
PYAUD_PLUGINS = _Path("pyaud_plugins")
DEFAULT_PLUGINS = _Path(__file__).absolute().parent.parent / PYAUD_PLUGINS
SITE_PLUGINS = _Path.cwd() / PLUGINS
DATADIR = _Path(_appdirs.user_data_dir(NAME))
CACHEDIR = _Path(_appdirs.user_cache_dir(NAME, version=__version__))


def load_namespace() -> None:
    """Load key-value pairs."""
    repo = _Path.cwd().name
    _os.environ.update(
        PYAUD_WHITELIST="whitelist.py",
        PYAUD_COVERAGE_XML="coverage.xml",
        PYAUD_REQUIREMENTS="requirements.txt",
        BUILDDIR=str(DOCS / "_build"),
        PYAUD_GH_NAME=_os.environ.get(
            "PYAUD_GH_NAME", _os.environ.get("GITHUB_REPOSITORY_OWNER", "")
        ),
        PYAUD_GH_EMAIL=_os.environ.get("PYAUD_GH_EMAIL", ""),
        PYAUD_GH_TOKEN=_os.environ.get("PYAUD_GH_TOKEN", ""),
        CODECOV_TOKEN=_os.environ.get("CODECOV_TOKEN", ""),
        PYAUD_DOCS=str(DOCS),
        PYAUD_PIPFILE_LOCK=str(PIPFILE_LOCK),
        PYAUD_TOC=str(DOCS / f"{repo}.rst"),
    )
    _dotenv.load_dotenv(_dotenv.find_dotenv(), override=True)
    if "PYAUD_GH_REMOTE" not in _os.environ:
        _os.environ[
            "PYAUD_GH_REMOTE"
        ] = "https://{}:{}@github.com/{}/{}.git".format(
            _os.environ["PYAUD_GH_NAME"],
            _os.environ["PYAUD_GH_TOKEN"],
            _os.environ["PYAUD_GH_NAME"],
            repo,
        )


class TempEnvVar:
    """Temporarily set a mutable mapping key-value pair.

    Set key-value whilst working within the context manager. If key
    already exists then change the key back to its original value. If
    key does not already exist then delete it so the environment is
    returned to its original state.

    :param obj: Mutable mapping to temporarily change.
    :param key: Key to temporarily change in supplied object.
    :param value: Value to temporarily change in supplied object.
    """

    def __init__(self, obj: _MutableMapping, **kwargs: str) -> None:
        self._obj = obj
        self._default = {k: obj.get(k) for k in kwargs}
        self._obj.update(kwargs)

    def __enter__(self) -> TempEnvVar:
        return self

    def __exit__(
        self, exc_type: _t.Any, exc_val: _t.Any, exc_tb: _t.Any
    ) -> None:
        for key, value in self._default.items():
            if value is None:
                try:
                    del self._obj[key]
                except KeyError:

                    # in the case that key gets deleted within context
                    pass
            else:
                self._obj[key] = self._default[key]


def initialize_dirs() -> None:
    """Ensure app dirs exist."""
    DATADIR.mkdir(exist_ok=True, parents=True)
    CACHEDIR.mkdir(exist_ok=True, parents=True)
