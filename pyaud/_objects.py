"""
pyaud._objects
==============
"""
import json as _json
import logging as _logging
import typing as _t
from abc import ABC as _ABC
from pathlib import Path as _Path

_KT = _t.TypeVar("_KT")
_VT = _t.TypeVar("_VT")
_T_co = _t.TypeVar("_T_co", covariant=True)


class MutableMapping(_t.MutableMapping[_KT, _VT]):
    """Inherit to replicate subclassing of ``dict`` objects."""

    def __init__(self) -> None:
        self._dict: _t.Dict[_KT, _VT] = {}

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
        self, obj: _t.Dict[_KT, _t.Any], update: _t.Dict[_KT, _t.Any]
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


class BasePlugin(_ABC):  # pylint: disable=too-few-public-methods
    """Base type for all plugins."""

    #: If set to True then indexed files will be monitored for change.
    cache = False

    #: Only matters if ``cache`` is set to True.
    #: If False (default) then audit will cache on a file-by-file basis.
    #: If True, then no changes can be made to any file for a cache-hit
    #: to be valid.
    cache_all = False

    #: set a single cache file for plugin subclass.
    cache_file: _t.Optional[_t.Union[str, _Path]] = None

    @classmethod
    def logger(cls) -> _logging.Logger:
        """Assign an audit logger dynamically, post logging config.

        :return: ``Logger`` object.
        """
        return _logging.getLogger(cls.__name__)


class JSONIO(MutableMapping):
    """Base class JSON input/output actions."""

    def read(self, path: _Path) -> None:
        """Read from file to object.

        :param path: Path to json file.
        """
        if path.is_file():
            try:
                self.update(_json.loads(path.read_text()))
            except _json.decoder.JSONDecodeError:
                pass

    def write(self, path: _Path) -> None:
        """Write data to file.

        :param path: Path to json file.
        """
        path.write_text(_json.dumps(dict(self), separators=(",", ":")))
