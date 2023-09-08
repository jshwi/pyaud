"""
pyaud.exceptions
================

Exceptions for use within the module.

All exceptions made public for if they need to be reraised or excepted.

Exceptions are already built into the architecture but can be used in
new plugins as well.
"""
from . import messages as _messages


class NameConflictError(Exception):
    """Raise if adding plugin whose name is not unique.

    :param plugin: Plugin which could not be registered.
    :param name: Name which clashes with another.
    """

    def __init__(self, plugin: str, name: str) -> None:
        super().__init__(
            _messages.NAME_CONFLICT_ERROR.format(plugin=plugin, name=name)
        )
