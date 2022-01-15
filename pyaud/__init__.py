"""Plugin architecture for auditing Python packages."""
from . import config, exceptions, parsers, plugins
from ._environ import Environ, environ, initialize_dirs
from ._indexing import HashMapping, files
from ._objects import BasePlugin
from ._utils import (
    branch,
    get_commit_hash,
    get_packages,
    git,
    package,
    working_tree_clean,
)
from ._version import __version__

__all__ = [
    "BasePlugin",
    "Environ",
    "HashMapping",
    "__version__",
    "branch",
    "config",
    "environ",
    "exceptions",
    "files",
    "get_commit_hash",
    "get_packages",
    "git",
    "initialize_dirs",
    "package",
    "parsers",
    "plugins",
    "working_tree_clean",
]
