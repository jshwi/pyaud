"""Select module with commandline arguments.

The word ``function`` and ``module`` are used interchangeably in this
package.
"""
from . import config, exceptions, plugins
from ._environ import package
from ._utils import branch, files, git

__version__ = "2.0.0"

__all__ = [
    "branch",
    "config",
    "exceptions",
    "files",
    "git",
    "package",
    "plugins",
]
