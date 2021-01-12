"""
pyaud.src.config
=================

Config module for ini parsing.
"""
import configparser
import os
from typing import List

from . import environ


class ConfigParser(
    configparser.ConfigParser
):  # pylint: disable=too-many-ancestors
    """ConfigParser inherited class with some tweaks."""

    default = dict(
        CLEAN={"exclude": "*.egg*,\n  .mypy_cache,\n  .env,\n  instance,"},
    )

    def __init__(self) -> None:
        super().__init__(default_section="")
        self.configfile = environ.env["CONFIG_FILE"]
        self._resolve()

    def _read_proxy(self) -> None:
        self.read(self.configfile)
        for section in self.sections():
            for key in self[section]:
                self[section][key] = os.path.expandvars(self[section][key])

    def _resolve(self) -> None:
        while True:
            if os.path.isfile(self.configfile):
                self._read_proxy()
                break

            self.read_dict(self.default)
            with open(self.configfile, "w") as fout:
                self.write(fout)

    def getlist(self, section, key) -> List[str]:
        """Return a comma separated ini list as a Python list.

        :param section: Section containing the key-value pair.
        :param key:     The key who's comma separated list will be
                        parsed.
        :return:        Python list parsed from command separated
                        values.
        """
        return [e.strip() for e in self[section][key].split(",") if e != ""]
