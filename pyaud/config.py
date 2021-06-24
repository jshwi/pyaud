"""
pyaud.config
============

Config module for ini parsing.
"""
import copy
import logging.config as logging_config
import os
from collections.abc import MutableMapping
from configparser import ConfigParser as _ConfigParser
from typing import Any, Dict, Iterator, List, Optional, TextIO

import appdirs
import toml.decoder as toml_decoder
import toml.encoder as toml_encoder

from .environ import NAME

RCFILE = f".{NAME}rc"
TOMLFILE = f"{NAME}.toml"
PYPROJECT = "pyproject.toml"
CONFIGDIR = appdirs.user_config_dir(NAME)
DEBUG = "DEBUG"
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"
CRITICAL = "CRITICAL"
LEVELS = [DEBUG, INFO, WARNING, ERROR, CRITICAL]
DEFAULT_CONFIG: Dict[str, Any] = dict(
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
                "filename": os.path.join(
                    appdirs.user_log_dir(NAME), f"{NAME}.log"
                ),
            }
        },
        "root": {"level": "INFO", "handlers": ["default"], "propagate": False},
    },
)


class ConfigParser(_ConfigParser):  # pylint: disable=too-many-ancestors
    """ConfigParser inherited class with some tweaks."""

    def __init__(self) -> None:
        super().__init__(default_section="")
        self.configfile = os.path.join(CONFIGDIR, f"{NAME}.ini")
        self._resolve()

    def _read_proxy(self) -> None:
        self.read(self.configfile)
        for section in self.sections():
            for key in self[section]:
                self[section][key] = os.path.expandvars(self[section][key])

    def _resolve(self) -> None:
        if os.path.isfile(self.configfile):
            self._read_proxy()

    def getlist(self, section: str, key: str) -> List[str]:
        """Return a comma separated ini list as a Python list.

        :param section: Section containing the key-value pair.
        :param key:     The key who's comma separated list will be
                        parsed.
        :return:        Python list parsed from command separated
                        values.
        """
        retval = []
        if section in self:
            retval.extend(
                [e.strip() for e in self[section][key].split(",") if e != ""]
            )

        return retval


class _MutableMapping(MutableMapping):  # pylint: disable=too-many-ancestors
    """Inherit to replicate subclassing of ``dict`` objects."""

    def __init__(self) -> None:
        self._dict: Dict[str, Any] = dict()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._dict}>"

    def __len__(self) -> int:
        return self._dict.__len__()

    def __delitem__(self, key: Any) -> None:
        self._dict.__delitem__(key)

    def __setitem__(self, index: Any, value: Any) -> None:
        self._dict = self._nested_update(self._dict, {index: value})

    def __getitem__(self, index: Any) -> Any:
        return self._dict.__getitem__(index)

    def __iter__(self) -> Iterator:
        return iter(self._dict)

    def _nested_update(
        self, obj: Dict[str, Any], update: Dict[str, Any]
    ) -> Dict[str, Any]:
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
                value = os.path.expanduser(value)

            obj[key] = value

        return obj


class _TomlArrayEncoder(toml_encoder.TomlEncoder):
    """Pass to ``toml.encoder`` functions (dump and dumps).

    Set rule for string encoding so arrays are collapsed if they exceed
    line limit.
    """

    def dump_list(self, v: Any) -> str:
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

    def _format_dump(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in obj.items():
            if isinstance(value, dict):
                value = self._format_dump(value)

            if isinstance(value, str):
                value = value.replace(os.path.expanduser("~"), "~")

            obj[key] = value

        return obj

    def dump(self, fout: TextIO, obj: Optional[MutableMapping] = None) -> str:
        """Native ``dump`` method to include encoder.

        :param fout:    TextIO file stream.
        :param obj:     Mutable mapping dict-like object.
        :return:        str object in toml encoded form.
        """
        return toml_encoder.dump(
            self._format_dump(dict(self) if obj is None else dict(obj)),
            fout,
            encoder=self._encoder,
        )

    def dumps(self, obj: Optional[MutableMapping] = None) -> str:
        """Native ``dump(from)s(tr)`` method to include encoder.

        :param obj: Mutable mapping dict-like object.
        :return:    str object in toml encoded form.
        """
        return toml_encoder.dumps(
            self._format_dump(dict(self) if obj is None else dict(obj)),
            encoder=self._encoder,
        )

    def load(self, fin: TextIO, *args: Any) -> None:
        """Native ``load (from file)`` method.

        :param fin: File stream.
        """
        obj = toml_decoder.load(fin)
        for arg in args:
            obj = obj.get(arg, obj)

        self.update(obj)


def configure_global() -> None:
    """Setup object with default config settings.

    Create config file with default config settings if one does not
    already exist. Load base config file which may or may not still have
    the default settings configured.
    """
    configfile = os.path.join(CONFIGDIR, TOMLFILE)
    default_config = copy.deepcopy(DEFAULT_CONFIG)
    config = ConfigParser()
    if os.path.isfile(configfile):
        with open(configfile) as fin:
            toml.load(fin)

    for key in default_config:
        if key not in toml:
            toml[key] = default_config[key]

    exclude = config.getlist("CLEAN", "exclude")
    if exclude:
        toml["clean"]["exclude"] = exclude

    os.makedirs(os.path.dirname(configfile), exist_ok=True)
    with open(configfile, "w") as fout:
        toml.dump(fout)


def load_config():
    """Load configs in order, each one overriding the previous."""
    files = [
        os.path.join(CONFIGDIR, TOMLFILE),
        os.path.join(os.path.expanduser("~"), RCFILE),
        os.path.join(os.environ["PROJECT_DIR"], RCFILE),
        os.path.join(os.environ["PROJECT_DIR"], PYPROJECT),
    ]
    for file in files:
        if os.path.isfile(file):
            with open(file) as fin:
                toml.load(fin, "tool", NAME)


def generate_rcfile():
    """Print default config file in ``Toml`` format."""
    print(toml.dumps(DEFAULT_CONFIG), end="")


def configure_logging(verbose: int = 0) -> None:
    """Set loglevel via commandline.

    Override environment variable if loglevel has already been set.

    :param verbose: Level to raise log verbosity by.
    """
    config = toml["logging"]

    # create logging dir and it's parents if they do not exist already
    os.makedirs(
        os.path.dirname(
            os.path.expanduser(config["handlers"]["default"]["filename"])
        ),
        exist_ok=True,
    )

    # tweak loglevel if commandline argument is provided
    config["root"]["level"] = LEVELS[
        max(0, LEVELS.index(config["root"]["level"]) - verbose)
    ]

    # load values to ``logging``
    logging_config.dictConfig(toml["logging"])


toml = _Toml()
configure_global()
