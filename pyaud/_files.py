"""
pyaud._files
============
"""
from __future__ import annotations as _annotations

import contextlib as _contextlib
import copy
import sys as _sys
import typing as _t

from lsfiles import LSFiles as _LSFiles

from . import messages as _messages
from ._objects import colors as _colors


class _Files(_LSFiles):
    def __init__(self) -> None:
        super().__init__()
        self._state = self

    def populate(self, exclude: str | None = None) -> None:
        super().populate(exclude)
        if not all(i.is_file() for i in self):
            _sys.exit(
                "{}\n{}".format(
                    _colors.red.bold.get(_messages.REMOVED_FILES),
                    _messages.RUN_COMMAND.format(
                        command=_colors.cyan.get("git add")
                    ),
                )
            )

    def restore(self) -> None:
        """Restore the original state of index."""
        self.extend(self._state)

    @_contextlib.contextmanager
    def state(self) -> _t.Generator[_Files, None, None]:
        """Freeze a state of the instance at a point in time.

        Once the context is exited the state will be restored.

        :return: Generator yielding the instance's current state.
        """
        self._state = copy.deepcopy(self)
        yield self._state
        self.restore()


files = _Files()
