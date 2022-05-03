"""
pyaud._data
===========

Persistent data for use between runs.
"""
from __future__ import annotations

import contextlib as _contextlib
import typing as _t
from pathlib import Path as _Path
from time import time as _time

from ._objects import JSONIO as _JSONIO
from ._objects import BasePlugin as _BasePlugin


class _TimeKeeper:
    def __init__(self, cls: _t.Type[_BasePlugin]) -> None:
        self._cls = cls
        self._start_time = 0.0
        self._end_time = self._start_time
        self._elapsed = self._start_time

    def _starter(self):
        self._start_time = _time()

    def _stopper(self):
        self._end_time = _time()

    def start(self) -> None:
        """Start the timer."""
        self._starter()
        self._end_time = self._start_time

    def stop(self) -> None:
        """Record the time from entry to exit."""
        self._stopper()
        self._elapsed = round(self._end_time - self._start_time, 2)

    def elapsed(self) -> float:
        """Return the elapsed time.

        :return: The elapsed time.
        """
        return self._elapsed


class Record(_JSONIO):
    """Record floats to objects based on calling class."""

    def average(self, repo: str, cls: _t.Type[_BasePlugin]) -> float:
        """Get the average of all recorded times.

        :param repo: Name of package audit is running in.
        :param cls: Name of class that this is running in.
        :return: Float containing the average of elapsed times.
        """
        items = self.get(repo, {}).get(str(cls), [])
        return round(sum(items) / len(items), 2)

    @_contextlib.contextmanager
    def track(
        self, repo: str, cls: _t.Type[_BasePlugin], path: _Path
    ) -> _t.Generator[_TimeKeeper, None, None]:
        """Context manager for parsing envvars with a common prefix.

        :param repo: Name of package audit is running in.
        :param cls: Name of class that this is running in.
        :param path: Path to datafile.
        :return: ``Instantiated _TimeKeeper`` object.
        """
        time_keeper = _TimeKeeper(cls)
        try:
            self[repo] = self.get(repo, {})
            self[repo][str(cls)] = self[repo].get(str(cls), [])
            time_keeper.start()
            yield time_keeper
        finally:
            time_keeper.stop()
            self[repo][str(cls)].append(time_keeper.elapsed())
            super().write(path)


record = Record()
