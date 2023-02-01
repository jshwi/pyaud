"""
pyaud._locations
================
"""
from __future__ import annotations

from pathlib import Path as _Path

from appdirs import AppDirs as _AppDirs

NAME = __name__.split(".", maxsplit=1)[0]


class AppDirs(_AppDirs):
    """Directories for app to interact with.

    Create app's data dirs on instantiation.
    """

    def __init__(self) -> None:
        super().__init__(appname=NAME)

    @property
    def user_project_dir(self) -> _Path:
        """path to user's current project."""
        return _Path.cwd()

    @property
    def user_cache_dir(self) -> _Path:
        """Path to the user's cache dir."""
        path = _Path(super().user_cache_dir)
        path.mkdir(exist_ok=True, parents=True)
        return path


class AppFiles(AppDirs):
    """Files for app to interact with."""

    @property
    def cache_file(self) -> _Path:
        """Path to the app's cache file."""
        return self.user_cache_dir / "files.json"

    @property
    def pyproject_toml(self) -> _Path:
        """Path to the project's pyproject.toml file."""
        return self.user_project_dir / "pyproject.toml"
