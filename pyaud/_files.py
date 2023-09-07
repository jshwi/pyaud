"""
pyaud._files
============
"""
from __future__ import annotations

import sys as _sys

from lsfiles import LSFiles as _LSFiles

from . import messages as _messages
from ._objects import colors as _colors


class _Files(_LSFiles):
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


files = _Files()
