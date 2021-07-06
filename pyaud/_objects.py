"""
pyaud.objects
=============
"""
from collections.abc import MutableMapping as _MutableMapping
from collections.abc import MutableSequence as _MutableSequence
from pathlib import Path as _Path
from typing import Any as _Any
from typing import Dict as _Dict
from typing import Iterator as _Iterator
from typing import List as _List


class MutableSequence(_MutableSequence):  # pylint: disable=too-many-ancestors
    """Inherit to replicate subclassing of ``list`` objects."""

    def __init__(self) -> None:
        self._list: _List[_Any] = list()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._list}>"

    def __len__(self) -> int:
        return self._list.__len__()

    def __delitem__(self, key: _Any) -> None:
        self._list.__delitem__(key)

    def __setitem__(self, index: _Any, value: _Any) -> None:
        self._list.__setitem__(index, value)

    def __getitem__(self, index: _Any) -> _Any:
        return self._list.__getitem__(index)

    def insert(self, index: int, value: str) -> None:
        """Insert values into ``_list`` object.

        :param index:   ``list`` index to insert ``value``.
        :param value:   Value to insert into list.
        """
        self._list.insert(index, value)


class MutableMapping(_MutableMapping):  # pylint: disable=too-many-ancestors
    """Inherit to replicate subclassing of ``dict`` objects."""

    def __init__(self) -> None:
        self._dict: _Dict[str, _Any] = dict()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._dict}>"

    def __len__(self) -> int:
        return self._dict.__len__()

    def __delitem__(self, key: _Any) -> None:
        self._dict.__delitem__(key)

    def __setitem__(self, index: _Any, value: _Any) -> None:
        self._dict = self._nested_update(self._dict, {index: value})

    def __getitem__(self, index: _Any) -> _Any:
        return self._dict.__getitem__(index)

    def __iter__(self) -> _Iterator:
        return iter(self._dict)

    def _nested_update(
        self, obj: _Dict[str, _Any], update: _Dict[str, _Any]
    ) -> _Dict[str, _Any]:
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
