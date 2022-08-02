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

import appdirs as _appdirs

# noinspection PyUnresolvedReferences
import toml.decoder as _toml_decoder

# noinspection PyUnresolvedReferences
import toml.encoder as _toml_encoder

from . import _typing as _pt
from ._locations import NAME as _NAME
from ._locations import AppFiles as _AppFiles
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
                "filename": str(
                    _Path(_appdirs.user_log_dir(_NAME)) / f"{_NAME}.log"
                ),
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


class _TomlArrayEncoder(_toml_encoder.TomlEncoder):
    """Pass to ``toml.encoder`` functions (dump and dumps).

    Set rule for string encoding so arrays are collapsed if they exceed
    line limit.
    """

    def dump_list(self, v: _t.Iterable[object]) -> str:
        """Rule for dumping arrays.

        :param v: Array from toml file.
        :return: toml encoded to str.
        """
        start, stop = (4 * " ", "\n") if len(str(v)) > 79 else ("", "")
        retval = f"[{stop}"
        for item in v:
            retval += f"{start}{self.dump_value(item)}, {stop}"

        return f"{retval[:-2] if retval.endswith(', ') else retval}]"


class _Toml(_MutableMapping):  # pylint: disable=too-many-ancestors
    """Base class for all ``toml`` object interaction."""

    _encoder = _TomlArrayEncoder()

    def _format_dump(self, obj: _t.MutableMapping) -> _t.MutableMapping:
        for key, value in obj.items():
            if isinstance(value, dict):
                value = self._format_dump(value)

            if isinstance(value, str):
                value = value.replace(str(_Path.home()), "~")

            obj[key] = value

        return obj

    def dumps(self, obj: _t.Optional[_t.MutableMapping] = None) -> str:
        """Native ``dump(from)s(tr)`` method to include encoder.

        :param obj: Mutable mapping dict-like object.
        :return: str object in toml encoded form.
        """
        return _toml_encoder.dumps(
            self._format_dump(dict(self) if obj is None else dict(obj)),
            encoder=self._encoder,
        )

    def load(self, fin: _t.TextIO, *args: str) -> None:
        """Native ``load (from file)`` method.

        :param fin: File stream.
        """
        obj = _toml_decoder.load(fin)
        for arg in args:
            obj = obj.get(arg, obj)

        self.update(obj)

    def loads(self, string: str) -> None:
        """Native ``load (from file)`` method.

        :param string: Toml as str.
        """
        self.update(_toml_decoder.loads(string))


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


def configure_global(app_files: _AppFiles) -> None:
    """Setup object with default config settings.

    Create config file with default config settings if one does not
    already exist.

    Load base config file which may, or may not, still have the default
    settings configured.

    :param app_files: App file locations object.
    """
    default_config = _copy.deepcopy(DEFAULT_CONFIG)
    toml.update(default_config)
    if app_files.global_config_file.is_file():
        while True:
            try:
                toml.loads(app_files.global_config_file.read_text())
                _shutil.copyfile(
                    app_files.global_config_file,
                    app_files.global_config_file_backup,
                )
                break

            except _toml_decoder.TomlDecodeError:
                if app_files.global_config_file_backup.is_file():
                    _os.rename(
                        app_files.global_config_file_backup,
                        app_files.global_config_file,
                    )
                else:
                    break

    app_files.global_config_file.write_text(toml.dumps())


def load_config(
    app_files: _AppFiles, opt: _t.Optional[_t.Union[str, _os.PathLike]] = None
) -> None:
    """Load configs in order, each one overriding the previous.

    :param app_files: App file locations object.
    :param opt: Optional extra path which will override all others.
    """
    files = [
        app_files.global_config_file,
        app_files.home_config_file,
        app_files.project_config_file,
        app_files.pyproject_toml,
    ]
    if opt is not None:
        files.append(_Path(opt))

    for file in files:
        if file.is_file():
            with open(file, encoding="utf-8") as fin:
                toml.load(fin, "tool", _NAME)


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
