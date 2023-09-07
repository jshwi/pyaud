"""
pyaud._cachedir
===============
"""
from abc import ABC as _ABC
from abc import abstractmethod as _abstractmethod
from pathlib import Path as _Path

from ._objects import NAME as _NAME
from ._version import __version__

PATH = _Path.cwd() / ".pyaud_cache" / __version__


class _File(_ABC):
    def __init__(self, parent: _Path) -> None:
        self._parent = parent

    @property
    @_abstractmethod
    def name(self) -> str:
        """File name."""

    @property
    @_abstractmethod
    def text(self) -> str:
        """File text."""

    @property
    def path(self) -> _Path:
        """File path."""
        return self._parent / self.name

    def write(self) -> None:
        """Write to file."""
        self.path.write_text(self.text.format(name=_NAME), encoding="utf-8")


class _Tag(_File):
    @property
    def name(self) -> str:
        """File path."""
        return "CACHEDIR.TAG"

    @property
    def text(self) -> str:
        """File text."""
        return """
Signature: 8a477f597d28d172789f06886806bc55
# This file is a cache directory tag created by {name}.
# For information about cache directory tags, see:
#	https://bford.info/cachedir/spec.html
"""


class _Gitignore(_File):
    @property
    def name(self) -> str:
        """File path."""
        return ".gitignore"

    @property
    def text(self) -> str:
        """File text."""
        return """
# Created by {name} automatically.
*
"""


def create() -> None:
    """Create cachedir and cachedir files."""
    PATH.mkdir(exist_ok=True, parents=True)
    _Tag(PATH).write()
    _Gitignore(PATH).write()
