"""
pyaud.environ
=============

Set up the environment variables for the current project.
"""
import os
from collections.abc import MutableMapping
from typing import Any

import dotenv
import setuptools

NAME = __name__.split(".")[0]
README = "README.rst"
TESTS = "tests"
DOCS = "docs"
DOCS_CONF = os.path.join(DOCS, "conf.py")
PIPFILE_LOCK = "Pipfile.lock"


def find_package() -> str:
    """Find the relative path of the package to the project root.

    :return: Relative path to the package.
    """
    packages = setuptools.find_packages(where=os.getcwd(), exclude=["tests"])
    if not packages:
        raise EnvironmentError("no packages found")

    return packages[0]


def load_namespace() -> None:
    """Load key-value pairs."""
    os.environ.update(
        PYAUD_WHITELIST="whitelist.py",
        PYAUD_COVERAGE_XML="coverage.xml",
        PYAUD_REQUIREMENTS="requirements.txt",
        BUILDDIR=str(os.path.join(DOCS, "_build")),
        PYAUD_GH_NAME=os.environ.get("GITHUB_REPOSITORY_OWNER", ""),
        PYAUD_GH_EMAIL=os.environ.get("PYAUD_GH_EMAIL", ""),
        PYAUD_GH_TOKEN=os.environ.get("PYAUD_GH_TOKEN", ""),
        CODECOV_TOKEN=os.environ.get("CODECOV_TOKEN", ""),
        PYAUD_DOCS=DOCS,
        PYAUD_PIPFILE_LOCK=PIPFILE_LOCK,
        PYAUD_TOC=os.path.join(DOCS, f"{find_package()}.rst"),
    )
    dotenv.load_dotenv(dotenv.find_dotenv(), override=True)
    if "PYAUD_GH_REMOTE" not in os.environ:
        os.environ[
            "PYAUD_GH_REMOTE"
        ] = "https://{}:{}@github.com/{}/{}.git".format(
            os.environ["PYAUD_GH_NAME"],
            os.environ["PYAUD_GH_TOKEN"],
            os.environ["PYAUD_GH_NAME"],
            find_package(),
        )


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
