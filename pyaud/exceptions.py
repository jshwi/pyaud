"""
pyaud.exceptions
================

Exceptions for use within the module.

All exceptions made public for if they need to be reraised or excepted.

Exceptions are already built into the architecture but can be used in
new plugins as well.
"""
import typing as _t


class AuditError(Exception):
    """Raise for audit failures that aren't failed subprocesses.

    :param cmd: Command that failed. If no argument provided the value
        will be None.
    """

    def __init__(self, cmd: _t.Optional[str]) -> None:
        super().__init__(f"{cmd} did not pass all checks")


class NameConflictError(Exception):
    """Raise if adding plugin whose name is not unique.

    :param plugin: Plugin which could not be registered.
    :param name: Name which clashes with another.
    """

    def __init__(self, plugin: str, name: str) -> None:
        super().__init__(f"plugin name conflict at {plugin}: '{name}'")


class NotARepositoryError(OSError):
    """Raise if there is an error related to a Git repository."""

    def __init__(self) -> None:
        super().__init__("not a git repository")


class PythonPackageNotFoundError(OSError):
    """Raise if Python package not found in project."""


class CommandNotFoundError(OSError):
    """Raise when subprocess called is not on system."""

    def __init__(self, cmd: str) -> None:
        super().__init__(f"{cmd}: command not found...")
