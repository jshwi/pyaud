"""
pyaud.config
============

Includes constants, functions, and singleton for Toml config parsing.

``toml`` can be used with the external API for retrieving parsed config.

    Configs are parsed in the following order:
        | ~/.config/pyaud/pyaud.toml
        | ~/.pyaudrc
        | .pyaudrc
        | pyproject.toml

The following methods can be called with ``toml``:

    .. code-block:: python

        toml.dump(
            self, fout: TextIO, obj: Optional[MutableMapping] = None
        ) -> str:

    Dump dict object to open file.

    If Optional[MutableMapping] is not provided, toml will use its
    own key-values.

    .. code-block:: python

        toml.dumps(self, obj: Optional[MutableMapping] = None) -> str

    Return dict object from open file as toml str.

    If Optional[MutableMapping] is not provided, toml will use its
    own key-values.

    .. code-block:: python

        toml.load(self, fin: TextIO, *args: Any) -> None

    Load dict object from open file.
"""
from __future__ import annotations

import typing as _t
from types import TracebackType as _TracebackType

import tomli as _tomli

from ._locations import NAME as _NAME
from ._locations import AppFiles as _AppFiles
from ._objects import MutableMapping as _MutableMapping

DEFAULT_CONFIG: _t.Dict[str, _t.Any] = dict(
    indexing={"exclude": ["whitelist.py", "conf.py", "setup.py"]},
    packages={"exclude": ["tests"]},
    audit={
        "modules": [
            "format",
            "format-docs",
            "format-str",
            "imports",
            "typecheck",
            "unused",
            "lint",
            "coverage",
            "readme",
            "docs",
        ]
    },
)


class _Toml(_MutableMapping):
    """Base class for all ``toml`` object interaction."""

    def loads(self, __s: str, *args: str) -> None:
        """Native ``load (from file)`` method.

        :param __s: Toml as str.
        :param args: Keys to search for.
        """
        obj = _tomli.loads(__s)
        for arg in args:
            obj = obj.get(arg, obj)

        self.update(obj)


class TempEnvVar:
    """Temporarily set a mutable mapping key-value pair.

    Set key-value whilst working within the context manager. If key
    already exists then change the key back to its original value. If
    key does not already exist then delete it so the environment is
    returned to its original state.

    :param obj: Mutable mapping to temporarily change.
    :param kwargs: Key-values to temporarily change in supplied object.
    """

    def __init__(self, obj: _t.MutableMapping, **kwargs: str) -> None:
        self._obj = obj
        self._default = {k: obj.get(k) for k in kwargs}
        self._obj.update(kwargs)

    def __enter__(self) -> TempEnvVar:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: _TracebackType | None,
    ) -> None:
        for key, value in self._default.items():
            if value is None:
                try:
                    del self._obj[key]
                except KeyError:
                    # in the case that key gets deleted within context
                    pass
            else:
                self._obj[key] = self._default[key]


def load_config(app_files: _AppFiles) -> None:
    """Load configs in order, each one overriding the previous.

    :param app_files: App file locations object.
    """
    file = app_files.pyproject_toml
    toml.update(DEFAULT_CONFIG)
    if file.is_file():
        toml.loads(file.read_text(), "tool", _NAME)


toml = _Toml()
load_config(_AppFiles())
