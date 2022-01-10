"""
tests.fix_test
==============
"""
import typing as t
from pathlib import Path
from subprocess import CalledProcessError

import pytest

import pyaud

from . import NoColorCapsys


class _BaseFixer(pyaud.plugins.Fix):
    def audit(self, *args: t.Any, **kwargs: bool) -> int:
        """Nothing to do."""

    def fix(self, *args: t.Any, **kwargs: bool) -> int:
        """Nothing to do."""


class _PassFixer(_BaseFixer):
    def audit(self, *args: t.Any, **kwargs: bool) -> int:
        return 0


class _FailFixer(_BaseFixer):
    def audit(self, *args: t.Any, **kwargs: bool) -> int:
        raise CalledProcessError(1, "cmd")


class _BaseFileFixer(pyaud.plugins.FixFile):
    def fail_condition(self) -> t.Optional[bool]:
        """Nothing to do."""

    def audit(self, file: Path, **kwargs: bool) -> None:
        """Nothing to do."""

    def fix(self, file: Path, **kwargs: bool) -> None:
        """Nothing to do."""


class _PassFileFixer(_BaseFileFixer):
    """Nothing to do."""


class _FailFileFixer(_BaseFileFixer):
    def fail_condition(self) -> t.Optional[bool]:
        return True


@pytest.mark.usefixtures("bump_index")
class TestFix:
    """Test various implementations of ``pyaud.plugins.Fix``."""

    plugin_name = "fixer"

    def _register_fixer(self, fixer: pyaud.plugins.PluginType) -> None:
        pyaud.plugins.register(self.plugin_name)(fixer)

    @pytest.mark.parametrize("plugin", (_PassFixer, _PassFileFixer))
    def test_fix_on_pass(
        self,
        main: t.Any,
        nocolorcapsys: NoColorCapsys,
        plugin: pyaud.plugins.PluginType,
    ) -> None:
        """Test plugin on pass when using the fix class.

        :param main: Patch package entry point.
        :param nocolorcapsys: Capture system output while stripping ANSI
            color codes.
        """
        pyaud.files[0].touch()
        self._register_fixer(plugin)
        main(self.plugin_name)
        assert (
            "Success: no issues found in 1 source files"
            in nocolorcapsys.stdout()
        )

    @pytest.mark.parametrize("plugin", (_FailFixer, _FailFileFixer))
    def test_fix_on_fail(
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

    @pytest.mark.parametrize("plugin", (_FailFixer, _FailFileFixer))
    def test_fix_with_fix(
        self,
        main: t.Any,
        nocolorcapsys: NoColorCapsys,
        plugin: pyaud.plugins.PluginType,
    ) -> None:
        """Test plugin when using the fix class with ``-f/--fix``.

        :param main: Patch package entry point.
        :param nocolorcapsys: Capture system output while stripping ANSI
            color codes.
        """
        pyaud.files[0].touch()
        self._register_fixer(plugin)
        main(self.plugin_name, "--fix")
        assert (
            "Success: no issues found in 1 source files"
            in nocolorcapsys.stdout()
        )
