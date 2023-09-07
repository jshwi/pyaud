"""
pyaud._files
============
"""
from __future__ import annotations

import contextlib as _contextlib
import sys as _sys
import typing as _t

from lsfiles import LSFiles as _LSFiles

from . import messages as _messages
from ._objects import colors as _colors


class _Files(_LSFiles):
    def __init__(self) -> None:
        super().__init__()
        self._length = len(self)
        self._index = list(self)
        self._restored = False

    def populate(self, exclude: str | None = None) -> None:
        super().populate(exclude)
        if [i for i in self if not i.is_file()]:
            _sys.exit(
                "{}\n{}".format(
                    _colors.red.bold.get(_messages.REMOVED_FILES),
                    _messages.RUN_COMMAND.format(
                        command=_colors.cyan.get("git add")
                    ),
                )
            )

    @property
    def length(self) -> int:
        """Number of files for run."""
        return self._length

    def restore(self) -> None:
        """Restore the original state of index."""
        self._restored = True
        self.extend(self._index)

    @_contextlib.contextmanager
    def __call__(self) -> _t.Generator[_Files, None, None]:
        self._length = len(files)
        self._index = list(files)
        self._restored = False
        yield self
        if not self._restored:
            self.extend(self._index)


files = _Files()
