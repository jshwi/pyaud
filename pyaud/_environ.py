"""
pyaud.environ
=============

Set up the environment variables for the current project.
"""
# pylint: disable=invalid-name,too-many-public-methods
from environs import Env as _Env

from ._locations import NAME as _NAME


class Environ(_Env):
    """Package's environment variables."""

    @property
    def PREFIX(self) -> str:
        """Prefix for variables which may turn out to be ambiguous."""
        return f"{_NAME.upper()}_"

    @property
    def TIMED(self) -> bool:
        """Set ``timed`` to True without needing to pass arg."""
        with self.prefixed(self.PREFIX):
            return self.bool("TIMED", default=False)

    @property
    def FIX(self) -> bool:
        """Set ``fix`` to True without needing to pass arg."""
        with self.prefixed(self.PREFIX):
            return self.bool("FIX", default=False)


#: package environment, both parsed from .env file (with set defaults
#: for missing keys), and static values
environ = Environ()
