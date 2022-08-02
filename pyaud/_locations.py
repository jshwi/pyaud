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
        for path in (
            self.user_config_dir,
            self.user_data_dir,
            self.user_cache_dir,
        ):
            path.mkdir(exist_ok=True, parents=True)

    @property
    def user_home_dir(self) -> _Path:
        """Path to user's home directory."""
        return _Path.home()

    @property
    def user_project_dir(self) -> _Path:
        """path to user's current project."""
        return _Path.cwd()

    @property
    def user_config_dir(self) -> _Path:
        """Path to the user's config dir."""
        return _Path(super().user_config_dir)

    @property
    def user_data_dir(self) -> _Path:
        """Path to the user's data dir."""
        return _Path(super().user_data_dir)

    @property
    def user_cache_dir(self) -> _Path:
        """Path to the user's cache dir."""
        return _Path(super().user_cache_dir)


class AppFiles(AppDirs):
    """Files for app to interact with."""

    @property
    def cache_file(self) -> _Path:
        """Path to the app's cache file."""
        return self.user_cache_dir / "files.json"

    @property
    def durations_file(self) -> _Path:
        """Path to the app's durations file."""
        return self.user_data_dir / "durations.json"

    @property
    def global_config_file(self) -> _Path:
        """Path to the app's global config file."""
        return self.user_config_dir / f"{NAME}.toml"

    @property
    def global_config_file_backup(self) -> _Path:
        """Path to the app's global config backup file."""
        return self.user_config_dir / f"{NAME}.toml.bak"

    @property
    def home_config_file(self) -> _Path:
        """Path to the app's home config file."""
        return self.user_home_dir / f".{NAME}rc"

    @property
    def project_config_file(self) -> _Path:
        """Path to the app's project config file."""
        return self.user_project_dir / f".{NAME}rc"

    @property
    def pyproject_toml(self) -> _Path:
        """Path to the project's pyproject.toml file."""
        return self.user_project_dir / "pyproject.toml"
