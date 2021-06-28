"""
pyaud.plugins
=============

Main module used for public API.
"""
from typing import Any, Callable

from .exceptions import NameConflictError
from .objects import MutableMapping


class _Plugins(MutableMapping):  # pylint: disable=too-many-ancestors
    """Holds registered plugins."""

    def __setitem__(self, name: str, plugin: Any) -> None:
        # only unique names to be set in `plugins` object
        # if name is not unique raise `NameConflictError`
        if name in self:
            raise NameConflictError(plugin.__name__, name)

        super().__setitem__(name, plugin)


plugins = _Plugins()


def register(name: str) -> Callable[..., Any]:
    """Register subclassed plugin to collection.

    :param name:    Name to register plugin as.
    :return:        Return registered plugin to call.
    """

    def _register(plugin: Any):
        plugins[name] = plugin
        return plugin

    return _register
