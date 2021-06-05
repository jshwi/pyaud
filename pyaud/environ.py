"""
pyaud.environ
=============

Set up the environment variables for the current project.
"""
import os
from collections.abc import MutableMapping
from typing import Any, Iterator, Union

import appdirs
import setuptools

NAME = __name__.split(".")[0]
NAMESPACE = NAME.upper()


class Environ(MutableMapping):
    """Dictionary class to take the place of ``os.``.

    Converts strings when settings and to the correct type when getting.
    Prefixes input keys with the namespace prefix.
    """

    _values = {
        True: ("yes", "y", "true"),
        False: ("no", "n", "false"),
        None: ("none", ""),
    }

    def __init__(self) -> None:
        self.store = os.environ
        self.namespace = NAMESPACE

    def _key_proxy(self, key: str) -> str:
        if not key.startswith(self.namespace):
            return f"{self.namespace}_{key}"

        return key

    def _values_proxy(self, key: str) -> str:
        try:
            return self.store[self._key_proxy(key)]

        except KeyError:
            return self.store[key]

    def __getitem__(self, key: str) -> Any:
        value = self._values_proxy(key)
        if value.isdigit():
            return int(value)

        for _type, values in self._values.items():
            if value.casefold() in values:
                return _type

        return value

    def __setitem__(self, key: str, value: Any) -> None:
        key = self._key_proxy(key)
        self.store[key] = str(value)

    def __delitem__(self, key: str) -> None:
        try:
            del self.store[self._key_proxy(key)]

        except KeyError:
            del self.store[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.store)

    def __len__(self) -> int:
        return len(self.store)


env = Environ()


def find_package() -> str:
    """Find the relative path of the package to the project root.

    :return: Relative path to the package.
    """
    package = setuptools.find_packages(
        where=env["PROJECT_DIR"], exclude=["tests"]
    )

    if not package:
        raise EnvironmentError("Unable to find a Python package")

    return package[0]


def init_environ() -> None:
    """Write default environment variables.

    ``~/.config/pyaud/<PACKAGENAME>/environ`` file and then write the
    file free to be configured and loaded (overriding the below) later.
    """
    mapping = dict(
        COVERAGE_XML="${PROJECT_DIR}/coverage.xml",
        DOCS="${PROJECT_DIR}/docs",
        DOCS_BUILD="${PROJECT_DIR}/docs/_build",
        DOCS_CONF="${PROJECT_DIR}/docs/conf.py",
        ENV="${PROJECT_DIR}/.env",
        PIPFILE_LOCK="${PROJECT_DIR}/Pipfile.lock",
        PYLINTRC="${PROJECT_DIR}/.pylintrc",
        README_RST="${PROJECT_DIR}/README.rst",
        REQUIREMENTS="${PROJECT_DIR}/requirements.txt",
        TESTS="${PROJECT_DIR}/tests",
        WHITELIST="${PROJECT_DIR}/whitelist.py",
    )
    if not os.path.isfile(env["ENVIRON_FILE"]):
        with open(env["ENVIRON_FILE"], "w") as fout:
            for key, value in mapping.items():
                env[key] = os.path.expandvars(value)
                fout.write(f"{key}={value}\n")


def read_env(file: Union[bytes, str, os.PathLike]) -> None:
    """Read ent variables into ``os.environ``.

    Not using ``dotenv`` as it would not allow keys to be named before
    being set in the ent.

    :param file. Env file to read from.
    """
    with open(file) as fin:
        lines = fin.read().strip().splitlines()
        for line in lines:
            parts = line.split("=")
            key = parts[0]
            val = parts[1].replace('"', "").replace("'", "")
            env[key] = os.path.expandvars(val)


def load_namespace() -> None:
    """Load key-value pairs."""
    project_dir = env["PROJECT_DIR"]
    pkg = find_package()
    pkg_path = str(os.path.join(env["PROJECT_DIR"], pkg))
    config_dir = os.path.join(appdirs.user_config_dir(NAME), pkg)
    log_dir = os.path.join(appdirs.user_log_dir(NAME))
    docs = os.path.join(project_dir, "docs")
    docs_build = os.path.join(docs, "_build")
    env.update(
        dict(
            PROJECT_DIR=project_dir,
            PKG=pkg,
            PKG_PATH=pkg_path,
            PKG_MAIN=os.path.join(pkg_path, "__main__.py"),
            CONFIG_DIR=config_dir,
            LOG_DIR=log_dir,
            ENVIRON_FILE=os.path.join(str(config_dir), "environ"),
            ENV=os.path.join(project_dir, ".env"),
            DOCS=docs,
            CONFIG_FILE=os.path.join(config_dir, "config.ini"),
            COVERAGE_XML=os.path.join(project_dir, "coverage.xml"),
            DOCS_BUILD=docs_build,
            DOCS_BUILD_HTML=os.path.join(docs_build, "html"),
            DOCS_CONF=os.path.join(docs, "conf.py"),
            PIPFILE_LOCK=os.path.join(project_dir, "Pipfile.lock"),
            PYLINTRC=os.path.join(project_dir, ".pylintrc"),
            README_RST=os.path.join(project_dir, "README.rst"),
            REQUIREMENTS=os.path.join(project_dir, "requirements.txt"),
            TESTS=os.path.join(project_dir, "tests"),
            WHITELIST=os.path.join(project_dir, "whitelist.py"),
            TOC=os.path.join(docs, f"{pkg}.rst"),
        )
    )
    for _dir in (log_dir, config_dir):
        try:
            os.makedirs(_dir)

        except FileExistsError:
            pass

    if os.path.isfile(env["ENVIRON_FILE"]):
        read_env(env["ENVIRON_FILE"])
    else:
        init_environ()


class TempEnvVar:
    """Temporarily set a mutable mapping key-value pair.

    Set key-value whilst working within the context manager. If key
    already exists then change the key back to it's original value. If
    key does not already exist then delete it so the environment is
    returned back to it's original state.

    :param obj:     Mutable mapping to temporarily change.
    :param key:     Key to temporarily change in supplied object.
    :param value:   Value to temporarily change in supplied object.
    """

    def __init__(self, obj: MutableMapping, **kwargs: Any) -> None:
        self._obj = obj
        self._kwargs = kwargs
        self._default = {k: obj.get(k) for k in kwargs}

    def __enter__(self) -> None:
        self._obj.update(self._kwargs)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        for key, value in self._default.items():
            if value is None:
                try:
                    del self._obj[key]
                except KeyError:

                    # in the case that key gets deleted within context
                    pass
            else:
                self._obj[key] = self._default[key]
