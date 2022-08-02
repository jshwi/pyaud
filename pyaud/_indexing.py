"""
pyaud._indexing
===============
"""
from __future__ import annotations

import typing as _t
from types import TracebackType as _TracebackType

from lsfiles import LSFiles as _LSFiles


class IndexedState:
    """Store index and ensure it's in its original state on exit."""

    def __init__(self) -> None:
        self.length = len(files)
        self._index = list(files)
        self._restored = False

    def __enter__(self) -> IndexedState:
        return self

    def __exit__(
        self,
        exc_type: _t.Optional[_t.Type[BaseException]],
        exc_val: _t.Optional[BaseException],
        exc_tb: _t.Optional[_TracebackType],
    ) -> None:
        if not self._restored:
            files.extend(self._index)

    def restore(self) -> None:
        """Restore the original state of index."""
        self._restored = True
        files.extend(self._index)


files = _LSFiles()
