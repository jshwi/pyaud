"""
tests.fix_test
==============
"""
# pylint: disable=no-self-use
import typing as t
from pathlib import Path
from subprocess import CalledProcessError

import pytest

import pyaud

from . import FIX, FIX_ALL, FIX_FILE, FIXER, NO_ISSUES, NoColorCapsys


def _get_pass_fixer(
    base: t.Type[pyaud.plugins.BaseFix],
) -> t.Type[pyaud.plugins.BaseFix]:
    class _PassFixer(base):  # type: ignore
        def audit(self, *_: t.Any, **__: bool) -> int:
            """Return 0."""
            return 0

        def fix(self, *_: t.Any, **__: bool) -> int:
            """Nothing to do."""

    return _PassFixer


def _get_fail_fixer(
    base: t.Type[pyaud.plugins.BaseFix],
) -> t.Type[pyaud.plugins.BaseFix]:
    class _FailFixer(base):  # type: ignore
        def audit(self, *args: t.Any, **kwargs: bool) -> int:
            """Raise ``CalledProcessError``."""
            raise CalledProcessError(1, "cmd")

        def fix(self, *args: t.Any, **kwargs: bool) -> int:
            """Nothing to do."""

    return _FailFixer


class _BaseFileFixer(pyaud.plugins.FixFile):
    def fail_condition(self) -> t.Optional[bool]:
        """Nothing to do."""

    def audit(self, file: Path, **kwargs: bool) -> int:
        """Nothing to do."""
        return 0

    def fix(self, file: Path, **kwargs: bool) -> int:
        """Nothing to do."""
        return 0


class _PassFileFixer(_BaseFileFixer):
    """Nothing to do."""


class _FailFileFixer(_BaseFileFixer):
    def fail_condition(self) -> t.Optional[bool]:
        return True


@pytest.mark.usefixtures("bump_index")
class TestFix:
    """Test various implementations of ``pyaud.plugins.FixAll``."""

    plugin_name = FIXER

    def _register_fixer(self, fixer: pyaud.plugins.PluginType) -> None:
        pyaud.plugins.register(self.plugin_name)(fixer)

    @pytest.mark.parametrize(
        "plugin,expected",
        [
            (
                _get_pass_fixer(pyaud.plugins.Fix),  # type: ignore
                "Success: no issues found in file",
            ),
            (_get_pass_fixer(pyaud.plugins.FixAll), NO_ISSUES),  # type: ignore
            (_PassFileFixer, NO_ISSUES),
        ],
        ids=[FIX, FIX_ALL, FIX_FILE],
    )
    def test_on_pass(
        self,
        main: t.Any,
        nocolorcapsys: NoColorCapsys,
        plugin: pyaud.plugins.PluginType,
        expected: str,
    ) -> None:
        """Test plugin on pass when using the fix class.

        :param main: Patch package entry point.
        :param nocolorcapsys: Capture system output while stripping ANSI
            color codes.
        """
        pyaud.files[0].touch()
        self._register_fixer(plugin)
        main(self.plugin_name)
        assert expected in nocolorcapsys.stdout()

    @pytest.mark.parametrize(
        "plugin",
        [
            _get_fail_fixer(pyaud.plugins.Fix),  # type: ignore
            _get_fail_fixer(pyaud.plugins.FixAll),  # type: ignore
            _FailFileFixer,
        ],
        ids=[FIX, FIX_ALL, FIX_FILE],
    )
    def test_on_fail(
        self, main: t.Any, plugin: pyaud.plugins.PluginType
    ) -> None:
        """Test plugin on fail when using the fix class.

        :param main: Patch package entry point.
        """
        pyaud.files[0].touch()
        self._register_fixer(plugin)
        with pytest.raises(pyaud.exceptions.AuditError) as err:
            main(self.plugin_name)

        assert (
            f"{pyaud.__name__} {self.plugin_name} did not pass all checks"
            in str(err.value)
        )

    @pytest.mark.parametrize(
        "plugin,expected",
        [
            (
                _get_fail_fixer(pyaud.plugins.Fix),  # type: ignore
                "Success: no issues found in file",
            ),
            (_get_fail_fixer(pyaud.plugins.FixAll), NO_ISSUES),  # type: ignore
            (_FailFileFixer, NO_ISSUES),
        ],
        ids=[FIX, FIX_ALL, FIX_FILE],
    )
    def test_with_fix(
        self,
        main: t.Any,
        nocolorcapsys: NoColorCapsys,
        plugin: pyaud.plugins.PluginType,
        expected: str,
    ) -> None:
        """Test plugin when using the fix class with ``-f/--fix``.

        :param main: Patch package entry point.
        :param nocolorcapsys: Capture system output while stripping ANSI
            color codes.
        """
        pyaud.files[0].touch()
        self._register_fixer(plugin)
        main(self.plugin_name, "--fix")
        assert expected in nocolorcapsys.stdout()
