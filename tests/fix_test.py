"""
tests.fix_test
==============
"""
from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError

import pytest

import pyaud

from . import FILE, FIX, FIX_ALL, FIX_FILE, FIXER, MockMainType


def _get_pass_fixer(
    base: type[pyaud.plugins.BaseFix],
) -> type[pyaud.plugins.BaseFix]:
    class _PassFixer(base):  # type: ignore
        def audit(self, *_: str, **__: bool) -> int:
            """Return 0."""
            return 0

        def fix(self, *_: str, **__: bool) -> int:  # type: ignore
            """Nothing to do."""

    return _PassFixer


def _get_fail_fixer(
    base: type[pyaud.plugins.BaseFix],
) -> type[pyaud.plugins.BaseFix]:
    class _FailFixer(base):  # type: ignore
        def audit(self, *args: str, **kwargs: bool) -> int:
            """Raise ``CalledProcessError``."""
            raise CalledProcessError(1, "cmd")

        def fix(self, *_: str, **__: bool) -> int:
            """Nothing to do."""
            return 0

    return _FailFixer


class _BaseFileFixer(pyaud.plugins.FixFile):
    def fail_condition(self) -> bool | None:
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
    def fail_condition(self) -> bool | None:
        return True


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
                pyaud.messages.SUCCESS_FILE,
            ),
            (
                _get_pass_fixer(pyaud.plugins.FixAll),  # type: ignore
                pyaud.messages.SUCCESS_FILES.format(len=1),
            ),
            (_PassFileFixer, pyaud.messages.SUCCESS_FILES.format(len=1)),
        ],
        ids=[FIX, FIX_ALL, FIX_FILE],
    )
    def test_on_pass(
        self,
        main: MockMainType,
        capsys: pytest.CaptureFixture,
        plugin: pyaud.plugins.PluginType,
        expected: str,
    ) -> None:
        """Test plugin on pass when using the fix class.

        :param main: Patch package entry point.
        :param capsys: Capture sys out and err.
        :param plugin: Plugin to test.
        :param expected: Expected result.
        """
        pyaud.files.append(Path.cwd() / FILE)
        pyaud.files[0].touch()
        self._register_fixer(plugin)
        main(self.plugin_name)
        std = capsys.readouterr()
        assert expected in std.out

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
        self, main: MockMainType, plugin: pyaud.plugins.PluginType
    ) -> None:
        """Test plugin on fail when using the fix class.

        :param main: Patch package entry point.
        :param plugin: Plugin type object.
        """
        pyaud.files.append(Path.cwd() / FILE)
        pyaud.files[0].touch()
        self._register_fixer(plugin)
        main(self.plugin_name)

    @pytest.mark.parametrize(
        "plugin,expected",
        [
            (
                _get_fail_fixer(pyaud.plugins.Fix),  # type: ignore
                pyaud.messages.SUCCESS_FILE,
            ),
            (
                _get_fail_fixer(pyaud.plugins.FixAll),  # type: ignore
                pyaud.messages.SUCCESS_FILES.format(len=1),
            ),
            (_FailFileFixer, pyaud.messages.SUCCESS_FILES.format(len=1)),
        ],
        ids=[FIX, FIX_ALL, FIX_FILE],
    )
    def test_with_fix(
        self,
        main: MockMainType,
        capsys: pytest.CaptureFixture,
        plugin: pyaud.plugins.PluginType,
        expected: str,
    ) -> None:
        """Test plugin when using the fix class with ``-f/--fix``.

        :param main: Patch package entry point.
        :param capsys: Capture sys out and err.
        :param plugin: Plugin type object.
        :param expected: Expected result.
        """
        pyaud.files.append(Path.cwd() / FILE)
        pyaud.files[0].touch()
        self._register_fixer(plugin)
        main(self.plugin_name, "--fix")
        std = capsys.readouterr()
        assert expected in std.out
