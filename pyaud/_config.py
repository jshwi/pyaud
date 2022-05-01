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

import copy as _copy
import importlib as _importlib
import inspect as _inspect
import logging as _logging
import logging.config as _logging_config
import os as _os
import shutil as _shutil
import typing as _t
from pathlib import Path as _Path

import tomli as _tomli
import tomli_w as _tomli_w

from . import _typing as _pt
from ._environ import environ as _e
from ._objects import MutableMapping as _MutableMapping

DEFAULT_CONFIG: _t.Dict[str, _t.Any] = dict(
    clean={"exclude": ["*.egg*", ".mypy_cache", ".env", "instance"]},
    logging={
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
            }
        },
        "handlers": {
            "default": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "standard",
                "when": "d",
                "backupCount": 60,
                "filename": str(_e.LOG_FILE),
            }
        },
        "root": {"level": "INFO", "handlers": ["default"], "propagate": False},
    },
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
    addopts=["timed"],
)


class _Toml(_MutableMapping):
    """Base class for all ``toml`` object interaction."""

    def _key_update(self, __obj: _t.Dict[_t.Any, _t.Any], *args: str) -> None:
        for arg in args:
            __obj = __obj.get(arg, __obj)

        self.update(__obj)

    def dumps(self, __obj: _t.Optional[_t.Dict[str, _t.Any]] = None) -> str:
        """Native ``dump(from)s(tr)`` method to include encoder.

        :param __obj: Mutable mapping dict-like object.
        :return: str object in toml encoded form.
        """
        return _tomli_w.dumps(dict(self) if __obj is None else dict(__obj))

    def loads(self, __s: str, *args: str) -> None:
        """Native ``load (from file)`` method.

        :param __s: Toml as str.
        :param args: Keys to search for.
        """
        self._key_update(_tomli.loads(__s), *args)


class TempEnvVar:
    """Temporarily set a mutable mapping key-value pair.

    Set key-value whilst working within the context manager. If key
    already exists then change the key back to its original value. If
    key does not already exist then delete it so the environment is
    returned to its original state.

    :param obj: Mutable mapping to temporarily change.
    :param key: Key to temporarily change in supplied object.
    :param value: Value to temporarily change in supplied object.
    """

    def __init__(self, obj: _t.MutableMapping, **kwargs: str) -> None:
        self._obj = obj
        self._default = {k: obj.get(k) for k in kwargs}
        self._obj.update(kwargs)

    def __enter__(self) -> TempEnvVar:
        return self

    def __exit__(
        self, exc_type: _pt.Exc, exc_val: _pt.ExcVal, exc_tb: _pt.ExcTB
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


def configure_global() -> None:
    """Setup object with default config settings.

    Create config file with default config settings if one does not
    already exist.

    Load base config file which may, or may not, still have the default
    settings configured.
    """
    default_config = _copy.deepcopy(DEFAULT_CONFIG)
    toml.update(default_config)
    if _e.GLOBAL_CONFIG_FILE.is_file():
        while True:
            try:
                toml.loads(_e.GLOBAL_CONFIG_FILE.read_text(_e.ENCODING))
                _shutil.copyfile(
                    _e.GLOBAL_CONFIG_FILE, _e.GLOBAL_CONFIG_BAK_FILE
                )
                break

            except _tomli.TOMLDecodeError:
                if _e.GLOBAL_CONFIG_BAK_FILE.is_file():
                    _os.rename(
                        _e.GLOBAL_CONFIG_BAK_FILE, _e.GLOBAL_CONFIG_FILE
                    )
                else:
                    break

    _e.CONFIGDIR.mkdir(exist_ok=True, parents=True)
    _e.GLOBAL_CONFIG_FILE.write_text(toml.dumps(), _e.ENCODING)


def load_config(opt: _t.Optional[_t.Union[str, _os.PathLike]] = None) -> None:
    """Load configs in order, each one overriding the previous.

    :param opt: Optional extra path which will override all others.
    """
    files = [
        _e.GLOBAL_CONFIG_FILE,
        _e.USER_CONFIG_FILE,
        _e.PROJECT_CONFIG_FILE,
        _e.PYPROJECT,
    ]
    if opt is not None:
        files.append(_Path(opt))

    for file in files:
        if file.is_file():
            toml.loads(file.read_text(_e.ENCODING), "tool", _e.NAME)


def _extract_logger(default: _t.Dict[str, _t.Any]) -> _logging.Logger:
    # return the logging object
    parts = default["class"].split(".")
    module = _importlib.import_module(".".join(parts[:-1]))
    return getattr(module, parts[-1])


def _filter_default(
    default: _t.Dict[str, _t.Any], logger: _logging.Logger
) -> _t.Dict[str, _t.Any]:
    # filter out any invalid kwargs for logging config

    # this will be invalid, so re-add after
    cls = default["class"]
    formatter = default["formatter"]

    # inspect logger's signature for kwargs that it can take
    filter_keys = [
        param.name
        for param in _inspect.signature(
            logger  # type: ignore
        ).parameters.values()
        if param.kind == param.POSITIONAL_OR_KEYWORD
    ]

    # delete all the keys from the default section that are not valid
    for key in dict(default):
        if key not in filter_keys:
            del default[key]

    # re-add the str representation of the configured class
    default.update({"class": cls, "formatter": formatter})

    return default


def configure_logging(verbose: int = 0) -> None:
    """Set loglevel.

    If ``-v`` flag passed to commandline decrease runtime loglevel for
    every repeat occurrence.

    ``-vvvv`` will always set logging to ``DEBUG``.

    Default loglevel is set in the toml config and overridden by
    environment variable if there is one.

    :param verbose: Level to raise log verbosity by.
    """
    levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    config = dict(toml["logging"])
    default = config["handlers"]["default"]
    filename = default.get("filename")

    # get the logger object to filter out any invalid kwargs
    logger = _extract_logger(default)
    _filter_default(default, logger)

    # create logging dir and it's parents if they do not exist already
    if filename is not None:
        _Path(filename).expanduser().parent.mkdir(exist_ok=True, parents=True)

    # tweak loglevel if commandline argument is provided
    config["root"]["level"] = levels[
        max(0, levels.index(config["root"]["level"]) - verbose)
    ]

    # load values to ``logging``
    _logging_config.dictConfig(config)


toml = _Toml()
configure_global()
