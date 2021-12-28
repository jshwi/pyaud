"""
pyaud.parsers
=============
"""
from __future__ import annotations

import os
import typing as _t
from pathlib import Path as _Path

import m2r


class Md2Rst:
    """Convert markdown file into RST file.

    :param path: Path to the markdown file.
    :param temp: Is the new RST file only temporary? If True, remove on
        exit.
    """

    def __init__(self, path: _Path, temp: bool = False) -> None:
        self._new_path = path.parent / f"{path.stem}.rst"
        self._is_rst = self._new_path.is_file()
        self._temp = temp
        if path.is_file() and not self._is_rst:
            self._new_path.write_text(m2r.parse_from_file(path).strip())

    def __enter__(self) -> Md2Rst:
        return self

    def __exit__(
        self, exc_type: _t.Any, exc_val: _t.Any, exc_tb: _t.Any
    ) -> None:
        if self._temp and self._new_path.is_file() and not self._is_rst:
            os.remove(self._new_path)


class LineSwitch:
    """Take the ``path`` and ``replace`` argument from the commandline.

    Reformat the README whilst returning the original title to the
    parent process.

    :param path: File to manipulate.
    :param obj: t.Dictionary of line number's as key and replacement
        strings as values.
    """

    def __init__(self, path: _Path, obj: _t.Dict[int, str]) -> None:
        self._path = path
        self._obj = obj
        with open(path, encoding="utf-8") as fin:
            self.read = fin.read()

    def __enter__(self) -> None:
        with open(self._path, "w", encoding="utf-8") as file:
            for count, line in enumerate(self.read.splitlines()):
                if count in self._obj:
                    line = self._obj[count]

                file.write(f"{line}\n")

    def __exit__(
        self, exc_type: _t.Any, exc_val: _t.Any, exc_tb: _t.Any
    ) -> None:
        with open(self._path, "w", encoding="utf-8") as file:
            file.write(self.read)
