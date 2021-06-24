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


def find_package() -> str:
    """Find the relative path of the package to the project root.

    :return: Relative path to the package.
    """
    package = setuptools.find_packages(
        where=os.environ["PROJECT_DIR"], exclude=["tests"]
    )

    if not package:
        raise EnvironmentError("Unable to find a Python package")

    return package[0]


def load_namespace() -> None:
    """Load key-value pairs."""
    project_dir = os.environ.get("PROJECT_DIR", os.getcwd())
    os.environ["PROJECT_DIR"] = project_dir
    pkg = find_package()
    pkg_path = str(os.path.join(os.environ["PROJECT_DIR"], pkg))
    docs = os.path.join(project_dir, "docs")
    docs_build = os.path.join(docs, "_build")
    os.environ.update(
        PYAUD_PKG=pkg,
        PYAUD_PKG_PATH=pkg_path,
        PYAUD_DOCS=docs,
        PYAUD_COVERAGE_XML=os.path.join(project_dir, "coverage.xml"),
        PYAUD_DOCS_CONF=os.path.join(docs, "conf.py"),
        PYAUD_PIPFILE_LOCK=os.path.join(project_dir, "Pipfile.lock"),
        PYAUD_README_RST=os.path.join(project_dir, "README.rst"),
        PYAUD_REQUIREMENTS=os.path.join(project_dir, "requirements.txt"),
        PYAUD_TESTS=os.path.join(project_dir, "tests"),
        PYAUD_WHITELIST=os.path.join(project_dir, "whitelist.py"),
        PYAUD_TOC=os.path.join(docs, f"{pkg}.rst"),
        PYAUD_GH_NAME=os.environ.get("GITHUB_REPOSITORY_OWNER", ""),
        PYAUD_GH_EMAIL=os.environ.get("PYAUD_GH_EMAIL", ""),
        PYAUD_GH_TOKEN=os.environ.get("PYAUD_GH_TOKEN", ""),
        CODECOV_TOKEN=os.environ.get("CODECOV_TOKEN", ""),
        BUILDDIR=docs_build,
        PYLINTRC=os.path.join(project_dir, ".pylintrc"),
        MYPY_CACHE_DIR=os.path.join(os.environ["PROJECT_DIR"], ".mypy_cache"),
    )
    dotenv.load_dotenv(dotenv.find_dotenv(), override=True)
    if "PYAUD_GH_REMOTE" not in os.environ:
        os.environ[
            "PYAUD_GH_REMOTE"
        ] = "https://{}:{}@github.com/{}/{}.git".format(
            os.environ["PYAUD_GH_NAME"],
            os.environ["PYAUD_GH_TOKEN"],
            os.environ["PYAUD_GH_NAME"],
            os.environ["PYAUD_PKG"],
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
