"""
tests.config_test
=================
"""
# pylint: disable=protected-access
import typing as t

# noinspection PyProtectedMember
from pyaud import _config as pc

from . import DEFAULT_KEY, KEY, VALUE


def test_del_key_in_context() -> None:
    """Confirm there is no error raised when deleting temp key-value."""
    obj: t.Dict[str, str] = {}
    with pc.TempEnvVar(obj, key=VALUE):
        assert obj[KEY] == VALUE
        del obj[KEY]


def test_default_key() -> None:
    """Test setting and restoring of existing dict keys."""
    obj = {DEFAULT_KEY: "default_value"}
    with pc.TempEnvVar(obj, default_key="temp_value"):
        assert obj[DEFAULT_KEY] == "temp_value"

    assert obj[DEFAULT_KEY] == "default_value"
