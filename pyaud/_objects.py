"""
pyaud._objects
==============
"""
from __future__ import annotations

import json as _json
import typing as _t
from pathlib import Path as _Path

from lsfiles import LSFiles as _LSFiles
from object_colors import Color as _Color

NAME = __name__.split(".", maxsplit=1)[0]

_KT = _t.TypeVar("_KT")
_VT = _t.TypeVar("_VT")
_T_co = _t.TypeVar("_T_co", covariant=True)


class MutableMapping(_t.MutableMapping[_KT, _VT]):
    """Inherit to replicate subclassing of ``dict`` objects."""

    def __init__(self) -> None:
        self._dict: dict[_KT, _VT] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._dict}>"

    def __len__(self) -> int:
        return self._dict.__len__()

    def __delitem__(self, key: _KT) -> None:
        self._dict.__delitem__(key)

    def __setitem__(self, key: _KT, value: _VT) -> None:
        self._dict = self._nested_update(self._dict, {key: value})

    def __getitem__(self, key: _KT) -> _VT:
        return self._dict.__getitem__(key)

    def __iter__(self) -> _t.Iterator[_KT]:
        return self._dict.__iter__()

    def _nested_update(
        self, obj: dict[_KT, _t.Any], update: dict[_KT, _t.Any]
    ) -> _t.Dict[_KT, _t.Any]:
        # add to __setitem__ to ensure that no entire dict keys with
        # missing nested keys overwrite all other values
        # run recursively to cover all nested objects if value is a dict
        # if value is a str pass through ``Path.expanduser()`` to
        # translate paths prefixed with ``~/`` for ``/home/<user>``
        # if value is all else assign it to obj key
        # return obj for recursive assigning of nested dicts
        for key, value in update.items():
            if isinstance(value, dict):
                value = self._nested_update(obj.get(key, {}), value)

            elif isinstance(value, str):
                value = str(_Path(value).expanduser())

            obj[key] = value

        return obj


class _Toml(MutableMapping):
    """Base class for all ``toml`` object interaction."""


class JSONIO(MutableMapping):
    """Base class JSON input/output actions.

    :param path: Path to data file.
    """

    def __init__(self, path: _Path) -> None:
        super().__init__()
        self._path = path

    def read(self) -> None:
        """Read from file to object."""
        if self._path.is_file():
            try:
                self.update(_json.loads(self._path.read_text()))
            except _json.decoder.JSONDecodeError:
                pass

    def write(self) -> None:
        """Write data to file."""
        self._path.write_text(_json.dumps(dict(self), separators=(",", ":")))


toml = _Toml()
colors = _Color()
files = _LSFiles()

colors.populate_colors()
