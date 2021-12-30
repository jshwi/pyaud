"""
pyaud._data
===========

Persistent data for use between runs.
"""
from __future__ import annotations

import contextlib as _contextlib
import json as _json
from time import time as _time

from ._objects import MutableMapping as _MutableMapping

DURATIONS = "durations.json"


class _TimeKeeper:
    def __init__(self) -> None:
        self._start_time = 0.0
        self._end_time = self._start_time
        self._elapsed = self._start_time

    def start(self) -> None:
        """Start the timer."""
        self._start_time = _time()
        self._end_time = self._start_time

    def stop(self) -> None:
        """Record the time from entry to exit.

        :return: Float containing elapsed time.
        """
        self._end_time = _time()
        self._elapsed = round(self._end_time - self._start_time, 2)

    def elapsed(self) -> float:
        """Return the elapsed time.

        :return: The elapsed time.
        """
        return self._elapsed


class Record(_MutableMapping):
    """Record floats to objects based on calling class."""

    def average(self, package: str, cls: str) -> float:
        """Get the average of all recorded times.

        :return: Float containing the average of elapsed times.
        """
        items = self.get(package, {}).get(cls, [])
        return round(sum(items) / len(items), 2)

    @_contextlib.contextmanager
    def track(self, package: str, cls: str, path):
        """Context manager for parsing envvars with a common prefix."""
        time_keeper = _TimeKeeper()
        try:
            self[package] = self.get(package, {})
            self[package][cls] = self[package].get(cls, [])
            time_keeper.start()
            yield time_keeper
        finally:
            time_keeper.stop()
            self[package][cls].append(time_keeper.elapsed())
            write(self, path)


def read(obj, path) -> None:
    """Read from file to object."""
    if path.is_file():
        try:
            obj.update(_json.loads(path.read_text()))
        except _json.decoder.JSONDecodeError:
            pass


def write(obj, path) -> None:
    """Write data to file."""
    path.write_text(_json.dumps(dict(obj), separators=(",", ":")))


record = Record()
