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
            self, fout: TextIO, obj: Optional[MutableMapping = None
        ) -> str:

    Dump dict object to open file.

    If Optional[MutableMapping] is not provided, toml will use it's
    own key-values.

    .. code-block:: python

        toml.dumps(self, obj: Optional[MutableMapping] = None) -> str

    Return dict object from open file as toml str.

    If Optional[MutableMapping] is not provided, toml will use it's
    own key-values.

    .. code-block:: python

        toml.load(self, fin: TextIO, *args: Any) -> None

    Load dict object from open file.
"""
import copy as _copy
import logging.config as _logging_config
import os as _os
import shutil as _shutil
from pathlib import Path as _Path
from typing import Any as _Any
from typing import Dict as _Dict
from typing import MutableMapping as _ABCMutableMapping
from typing import Optional as _Optional
from typing import TextIO as _TextIO
from typing import Union as _Union

import appdirs as _appdirs
import toml.decoder as _toml_decoder
import toml.encoder as _toml_encoder

from ._environ import NAME as _NAME
from ._objects import MutableMapping as _MutableMapping

CONFIGDIR = _Path(_appdirs.user_config_dir(_NAME))
DEFAULT_CONFIG: _Dict[str, _Any] = dict(
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
)

_TOMLFILE = f"{_NAME}.toml"


class _TomlArrayEncoder(_toml_encoder.TomlEncoder):
    """Pass to ``toml.encoder`` functions (dump and dumps).

    Set rule for string encoding so arrays are collapsed if they exceed
    line limit.
    """

    def dump_list(self, v: _Any) -> str:
        """Rule for dumping arrays.

        :param v:   Array from toml file.
        :return:    toml encoded to str.
        """
        start, stop = (4 * " ", "\n") if len(str(v)) > 79 else ("", "")
        retval = f"[{stop}"
        for item in v:
            retval += f"{start}{self.dump_value(item)}, {stop}"

        return f"{retval[:-2] if retval.endswith(', ') else retval}]"


class _Toml(_MutableMapping):  # pylint: disable=too-many-ancestors
    """Base class for all ``toml`` object interaction."""

    _encoder = _TomlArrayEncoder()

    def _format_dump(self, obj: _Dict[str, _Any]) -> _Dict[str, _Any]:
        for key, value in obj.items():
            if isinstance(value, dict):
                value = self._format_dump(value)

            if isinstance(value, str):
                value = value.replace(str(_Path.home()), "~")

            obj[key] = value

        return obj

    def dump(
        self, fout: _TextIO, obj: _Optional[_ABCMutableMapping] = None
    ) -> str:
        """Native ``dump`` method to include encoder.

        :param fout:    TextIO file stream.
        :param obj:     Mutable mapping dict-like object.
        :return:        str object in toml encoded form.
        """
        return _toml_encoder.dump(
            self._format_dump(dict(self) if obj is None else dict(obj)),
            fout,
            encoder=self._encoder,
        )

    def dumps(self, obj: _Optional[_ABCMutableMapping] = None) -> str:
        """Native ``dump(from)s(tr)`` method to include encoder.

        :param obj: Mutable mapping dict-like object.
        :return:    str object in toml encoded form.
        """
        return _toml_encoder.dumps(
            self._format_dump(dict(self) if obj is None else dict(obj)),
            encoder=self._encoder,
        )

    def load(self, fin: _TextIO, *args: _Any) -> None:
        """Native ``load (from file)`` method.

        :param fin: File stream.
        """
        obj = _toml_decoder.load(fin)
        for arg in args:
            obj = obj.get(arg, obj)

        self.update(obj)


def _recursive_update(
    current: _ABCMutableMapping, default: _ABCMutableMapping
) -> _ABCMutableMapping:
    for key, value in default.items():
        if isinstance(value, _ABCMutableMapping):
            if key not in current:
                current[key] = _recursive_update(current.get(key, {}), value)
        else:
            current[key] = value

    return current


def configure_global() -> None:
    """Setup object with default config settings.

    Create config file with default config settings if one does not
    already exist.

    Load base config file which may, or may not, still have the default
    settings configured.
    """
    configfile = CONFIGDIR / _TOMLFILE
    backupfile = CONFIGDIR / f".{_TOMLFILE}.bak"
    default_config = _copy.deepcopy(DEFAULT_CONFIG)
    if configfile.is_file():
        while True:
            with open(configfile) as fin:
                try:
                    toml.load(fin)
                    _shutil.copyfile(configfile, backupfile)
                    break

                except _toml_decoder.TomlDecodeError:
                    if backupfile.is_file():
                        _os.rename(backupfile, configfile)
                    else:
                        break

    toml.update(_recursive_update(toml, default_config))
    CONFIGDIR.mkdir(exist_ok=True, parents=True)
    with open(configfile, "w") as fout:
        toml.dump(fout)


def load_config(opt: _Optional[_Union[str, _os.PathLike]] = None):
    """Load configs in order, each one overriding the previous.

    :param opt: Optional extra path which will override all others.
    """
    rcfile = f".{_NAME}rc"
    files = [
        CONFIGDIR / _TOMLFILE,
        _Path.home() / rcfile,
        _Path.cwd() / rcfile,
        _Path.cwd() / "pyproject.toml",
    ]
    if opt is not None:
        files.append(_Path(opt))

    for file in files:
        if file.is_file():
            with open(file) as fin:
                toml.load(fin, "tool", _NAME)


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
    config = toml["logging"]

    # create logging dir and it's parents if they do not exist already
    _Path(config["handlers"]["default"]["filename"]).expanduser().parent.mkdir(
        exist_ok=True, parents=True
    )

    # tweak loglevel if commandline argument is provided
    config["root"]["level"] = levels[
        max(0, levels.index(config["root"]["level"]) - verbose)
    ]

    # load values to ``logging``
    _logging_config.dictConfig(toml["logging"])


toml = _Toml()
configure_global()
