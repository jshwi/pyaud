"""
pyaud.objects
=============
"""
import json as _json
import logging as _logging
import typing as _t
from abc import ABC as _ABC
from collections.abc import MutableMapping as _MutableMapping
from collections.abc import MutableSequence as _MutableSequence
from pathlib import Path as _Path


class MutableSequence(_MutableSequence):  # pylint: disable=too-many-ancestors
    """Inherit to replicate subclassing of ``list`` objects."""

    def __init__(self) -> None:
        self._list: _t.List[_t.Any] = []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._list}>"

    def __len__(self) -> int:
        return self._list.__len__()

    def __delitem__(self, key: _t.Any) -> None:
        self._list.__delitem__(key)

    def __setitem__(self, index: _t.Any, value: _t.Any) -> None:
        self._list.__setitem__(index, value)

    def __getitem__(self, index: _t.Any) -> _t.Any:
        return self._list.__getitem__(index)

    def insert(self, index: int, value: str) -> None:
        """Insert values into ``_list`` object.

        :param index: ``list`` index to insert ``value``.
        :param value: Value to insert into list.
        """
        self._list.insert(index, value)


class MutableMapping(_MutableMapping):  # pylint: disable=too-many-ancestors
    """Inherit to replicate subclassing of ``dict`` objects."""

    def __init__(self) -> None:
        self._dict: _t.Dict[str, _t.Any] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._dict}>"

    def __len__(self) -> int:
        return self._dict.__len__()

    def __delitem__(self, key: _t.Any) -> None:
        self._dict.__delitem__(key)

    def __setitem__(self, key: _t.Any, value: _t.Any) -> None:
        self._dict = self._nested_update(self._dict, {key: value})

    def __getitem__(self, key: _t.Any) -> _t.Any:
        return self._dict.__getitem__(key)

    def __iter__(self) -> _t.Iterator:
        return iter(self._dict)

    def _nested_update(
        self, obj: _t.Dict[str, _t.Any], update: _t.Dict[str, _t.Any]
    ) -> _t.Dict[str, _t.Any]:
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


class BasePlugin(_ABC):  # pylint: disable=too-few-public-methods
    """Base type for all plugins."""

    #: If set to True then indexed files will be monitored for change.
    cache = False

    #: Only matters if ``cache`` is set to True.
    #: If False (default) then audit will cache on a file-by-file basis.
    #: If True, then no changes can be made to any file for a cache-hit
    #: to be valid.
    cache_all = False

    @classmethod
    def logger(cls) -> _logging.Logger:
        """Assign an audit logger dynamically, post logging config.

        :return: ``Logger`` object.
        """
        return _logging.getLogger(cls.__name__)


class JSONIO(MutableMapping):
    """Base class JSON input/output actions.

    :param path: Path to data file.
    """

    def __init__(self, path: _Path) -> None:
        super().__init__()
        self.path = path

    def read(self) -> None:
        """Read from file to object."""
        if self.path.is_file():
            try:
                self.update(_json.loads(self.path.read_text()))
            except _json.decoder.JSONDecodeError:
                pass

    def write(self) -> None:
        """Write data to file."""
        self.path.write_text(_json.dumps(dict(self), separators=(",", ":")))
