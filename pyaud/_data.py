"""
pyaud._data
===========

Persistent data for use between runs.
"""
from __future__ import annotations

import typing as _t
from pathlib import Path as _Path
from time import time as _time

from ._objects import JSONIO as _JSONIO
from ._objects import BasePlugin as _BasePlugin


class Record(_JSONIO):
    """Record floats to objects based on calling class.

    :param path: Path to data file.
    :param project: Name of the project that this package is auditing.
    :param cls: Audit that this class is running in.
    """

    def __init__(
        self, path: _Path, project: str, cls: _t.Type[_BasePlugin]
    ) -> None:
        super().__init__(path)
        self._cls = str(cls)
        self._project = project
        self._start_time = _time()
        self._end_time = self._start_time
        self[self._project] = self.get(self._project, {self._cls: []})

    def __enter__(self) -> Record:
        return self

    def __exit__(
        self, exc_type: _t.Any, exc_val: _t.Any, exc_tb: _t.Any
    ) -> None:
        self._end_time = _time()
        self._record(self.time())
        self.write()

    def _get_by_context(self) -> _t.List[float]:
        # get list by the calling audit in project
        return self.get(self._project, {self._cls: []}).get(self._cls, [])

    def _record(self, item: float) -> None:
        # record time from entry to exit
        self[self._project][self._cls] = self._get_by_context()
        self[self._project][self._cls].append(item)

    def time(self) -> float:
        """Record the time from entry to exit.

        :return: Float containing elapsed time.
        """
        return round(self._end_time - self._start_time, 2)

    def average(self) -> float:
        """Get the average of all recorded times.

        :return: Float containing the average of elapsed times.
        """
        items = self._get_by_context()
        return round(sum(items) / len(items), 2)
