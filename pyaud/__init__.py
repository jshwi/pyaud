"""Plugin architecture for auditing Python packages."""
from . import config, exceptions, parsers, plugins
from ._environ import environ
from ._indexing import files
from ._objects import BasePlugin
from ._subprocess import git
from ._utils import (
    branch,
    get_commit_hash,
    get_packages,
    package,
    working_tree_clean,
)
from ._version import __version__

__all__ = [
    "BasePlugin",
    "__version__",
    "branch",
    "config",
    "environ",
    "exceptions",
    "files",
    "get_commit_hash",
    "get_packages",
    "git",
    "package",
    "parsers",
    "plugins",
    "working_tree_clean",
]
