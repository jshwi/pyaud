"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments,too-few-public-methods
# pylint: disable=protected-access,no-member
from __future__ import annotations

import datetime
import subprocess
import typing as t
from pathlib import Path
from subprocess import CalledProcessError

import git
import pytest

import pyaud

from . import (
    AUDIT,
    INIT,
    KEY,
    PARAMS,
    STRFTIME,
    TESTS,
    UNPATCH_REGISTER_DEFAULT_PLUGINS,
    VALUE,
    FixtureMain,
    FixtureMakeTree,
    FixtureMockActionPluginFactory,
    FixtureMockSpallSubprocessOpenProcess,
    MockAudit,
    PluginTuple,
    Tracker,
    plugin_class,
    plugin_name,
    python_file,
)

# noinspection PyProtectedMember


def test_register_plugin_name_conflict_error(
    mock_action_plugin_factory: FixtureMockActionPluginFactory,
) -> None:
    """Test ``NameConflictError`` is raised when same name provided.

    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    unique = "test-register-plugin-name-conflict-error"
    plugin_one, plugin_two = mock_action_plugin_factory(
        PluginTuple(plugin_class[1]), PluginTuple(plugin_class[2])
    )
    pyaud.plugins.register(name=unique)(plugin_one)
    with pytest.raises(pyaud.exceptions.NameConflictError) as err:
        pyaud.plugins.register(name=unique)(plugin_two)

    assert str(err.value) == pyaud.messages.NAME_CONFLICT_ERROR.format(
        plugin=plugin_class[2], name=unique
    )


@pytest.mark.parametrize(
    "klass",
    [
        type("NotSubclassed", (), {}),
        type("Subclassed", (type("NotSubclassed", (), {}),), {}),
    ],
    ids=["base", "child"],
)
def test_register_invalid_type(klass: type) -> None:
    """Test correct error is displayed when registering unknown type.

    :param klass: Invalid type.
    """
    with pytest.raises(TypeError) as err:
        pyaud.plugins.register(
            name=datetime.datetime.now().strftime(STRFTIME)
        )(
            klass  # type: ignore
        )

    assert "can only register one of the following:" in str(err.value)


def test_plugin_mro(
    mock_action_plugin_factory: FixtureMockActionPluginFactory,
) -> None:
    """Assert that plugins can inherit other plugins.

    Prior to this commit ``PluginType``s were only permitted, and not
    children of ``PluginType``s.

    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    plugin_one, plugin_two = mock_action_plugin_factory(
        PluginTuple(plugin_name[1]), PluginTuple(plugin_name[2])
    )
    pyaud.plugins.register(name=plugin_name[1])(plugin_one)
    pyaud.plugins.register(name=plugin_name[2])(plugin_two)
    assert "plugin-1" in pyaud.plugins.mapping()
    assert "plugin-2" in pyaud.plugins.mapping()


def test_audit_error_did_no_pass_all_checks(
    main: FixtureMain,
    mock_action_plugin_factory: FixtureMockActionPluginFactory,
) -> None:
    """Test raising of ``AuditError``.

    :param main: Patch package entry point.
    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """

    def action(_, *__: int, **___: bool) -> int:
        raise subprocess.CalledProcessError(1, "returned non-zero exit status")

    plugins = mock_action_plugin_factory(
        PluginTuple(plugin_name[1], action=action)
    )
    path = Path.cwd() / python_file[1]
    path.touch()
    pyaud.plugins.register(name=plugin_name[1])(plugins[0])
    pyaud.files.append(path)
    returncode = main(plugin_name[1])
    assert returncode == 1


def test_no_exe_provided(
    mock_spall_subprocess_open_process: FixtureMockSpallSubprocessOpenProcess,
) -> None:
    """Test default value for exe property.

    :param mock_spall_subprocess_open_process: Patch
        ``spall.Subprocess._open_process`` returncode.
    """
    unique = datetime.datetime.now().strftime(STRFTIME)
    mock_spall_subprocess_open_process(1)
    pyaud.plugins.register(name=unique)(MockAudit)
    assert pyaud.plugins.get(unique).exe == []


@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
def test_modules(main: FixtureMain, capsys: pytest.CaptureFixture) -> None:
    """Test expected output for help after plugins have been loaded.

    Test no positional argument for json array of keys.
    Test ``audit`` positional argument and docstring display.
    Test all and display of all module docstrings.

    :param main: Patch package entry point.
    :param capsys: Capture sys out and err.
    """
    returncode = main("modules")
    std = capsys.readouterr()
    assert (
        "\naudit   -- Read from [audit] key in config\n"
        "modules -- Display all available plugins and their documentation\n"
    ) in std.out
    assert returncode == 0


@pytest.mark.parametrize(
    "expected_returncode,expected_output", [(0, "Success"), (1, "Failed")]
)
@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
def test_audit(
    main: FixtureMain,
    capsys: pytest.CaptureFixture,
    expected_returncode: int,
    expected_output: str,
) -> None:
    """Test when audit passes and fails.

    :param main: Patch package entry point.
    :param capsys: Capture sys out and err.
    :param expected_returncode: Returncode to mock.
    :param expected_output: Expected output.
    """

    class _MockAudit(pyaud.plugins.Audit):
        def audit(self, *_: str, **__: bool) -> int:
            return expected_returncode

    path = Path.cwd() / python_file[1]
    path.touch()
    pyaud.plugins.register(plugin_name[1])(_MockAudit)
    pyaud.files.append(path)
    returncode = main(AUDIT, f"--audit={plugin_name[1]}")
    assert returncode == expected_returncode
    assert expected_output in capsys.readouterr()[expected_returncode]


@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
def test_audit_raise(main: FixtureMain) -> None:
    """Test when audit fails with raised error.

    :param main: Patch package entry point.
    """

    class _MockAudit(pyaud.plugins.Audit):
        def audit(self, *_: str, **__: bool) -> int:
            raise CalledProcessError(1, "command")

    path = Path.cwd() / python_file[1]
    path.touch()
    pyaud.plugins.register(plugin_name[1])(_MockAudit)
    pyaud.files.append(path)
    returncode = main(AUDIT, f"--audit={plugin_name[1]}")
    assert returncode == 1


def test_parametrize(
    main: FixtureMain,
    capsys: pytest.CaptureFixture,
    mock_action_plugin_factory: FixtureMockActionPluginFactory,
) -> None:
    """Test class for running multiple plugins.

    :param main: Patch package entry point.
    :param capsys: Capture sys out and err.
    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """

    class _Params(pyaud.plugins.Parametrize):
        def plugins(self) -> list[str]:
            """List of plugin names to run.

            :return: List of plugin names, as defined in ``@register``.
            """
            return [plugin_name[1], plugin_name[2]]

    plugin_one, plugin_two = mock_action_plugin_factory(
        PluginTuple(plugin_name[1]), PluginTuple(plugin_name[2])
    )
    pyaud.plugins.register(name=plugin_name[1])(plugin_one)
    pyaud.plugins.register(name=plugin_name[2])(plugin_two)
    pyaud.plugins.register(name=PARAMS)(_Params)
    returncode = main(PARAMS)
    std = capsys.readouterr()
    assert returncode == 0
    assert f"pyaud {plugin_name[1]}" in std.out
    assert f"pyaud {plugin_name[2]}" in std.out


@pytest.mark.usefixtures("unpatch_plugins_load")
def test_imports(
    monkeypatch: pytest.MonkeyPatch, make_tree: FixtureMakeTree
) -> None:
    """Test imports from relative plugin dir.

    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree: Create directory tree from dict mapping.
    """
    tracker = Tracker()
    iter_modules = [
        (None, "pyaud_underscore", None),
        (None, "pyaud-dash", None),
    ]
    monkeypatch.setattr("pyaud.plugins._importlib.import_module", tracker)
    monkeypatch.setattr(
        "pyaud.plugins._pkgutil.iter_modules", lambda: iter_modules
    )
    make_tree(Path.cwd(), {"plugins": {INIT: None, python_file[1]: None}})
    pyaud.plugins.load()
    assert tracker.was_called()
    assert tracker.args == [("pyaud_underscore",), ("pyaud-dash",)]
    assert tracker.kwargs == [{}, {}]


@pytest.mark.parametrize(
    "classname,expected",
    [
        ("Const", "const"),
        ("Coverage", "coverage"),
        ("Deploy", "deploy"),
        ("DeployCov", "deploy-cov"),
        ("DeployDocs", "deploy-docs"),
        ("Docs", "docs"),
        ("Files", "files"),
        ("Format", "format"),
        ("FormatDocs", "format-docs"),
        ("FormatFString", "format-f-string"),
        ("Imports", "imports"),
        ("Lint", "lint"),
        ("Readme", "readme"),
        ("Requirements", "requirements"),
        ("Tests", TESTS),
        ("Toc", "toc"),
        ("TypeCheck", "type-check"),
        ("Unused", "unused"),
        ("Whitelist", "whitelist"),
    ],
)
def test_autoname(classname: str, expected: str) -> None:
    """Test names are automatically added as they should be.

    :param classname: Name of registered class.
    :param expected: Expected name of registered plugin.
    """

    class Plugin(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    Plugin.__name__ = classname
    pyaud.plugins.register()(Plugin)
    assert expected in pyaud.plugins.registered()


@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
def test_default_plugin(capsys: pytest.CaptureFixture) -> None:
    """Test invalid module name provided.

    :param capsys: Capture sys out and err.
    """
    pyaud.pyaud("not-a-module")
    std = capsys.readouterr()
    assert pyaud.messages.NOT_FOUND.format(name="not-a-module") in std.err


def test_parametrize_fail(
    main: FixtureMain,
    mock_action_plugin_factory: FixtureMockActionPluginFactory,
) -> None:
    """Test class for running multiple plugins.

    :param main: Patch package entry point.
    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """

    class _Params(pyaud.plugins.Parametrize):
        def plugins(self) -> list[str]:
            """List of plugin names to run.

            :return: List of plugin names, as defined in ``@register``.
            """
            return [plugin_name[1]]

    plugins = mock_action_plugin_factory(
        PluginTuple(plugin_name[1], "not_a_command", lambda x, *y, **z: 1)
    )
    pyaud.plugins.register(name=plugin_name[1])(plugins[0])
    pyaud.plugins.register(name=PARAMS)(_Params)
    returncode = main(PARAMS)
    assert returncode == 1


def test_subprocess(
    mock_action_plugin_factory: FixtureMockActionPluginFactory,
) -> None:
    """Test registering a subprocess.

    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    plugins = mock_action_plugin_factory(
        PluginTuple(
            plugin_class[1],
            "command",
            lambda x, *y, **z: x.subprocess[x.exe_str].call(*y, **z),
        )
    )
    pyaud.plugins.register(plugin_name[1])(plugins[0])
    exe = pyaud.plugins.get(plugin_name[1])
    assert (
        str(exe.subprocess)
        == "<Subprocesses {'command': <Subprocess (command)>}>"
    )


def test_del_key_in_context() -> None:
    """Confirm there is no error raised when deleting temp key-value."""
    obj: t.Dict[str, str] = {}
    with pyaud.plugins._TempEnvVar(obj, key=VALUE):
        assert obj[KEY] == VALUE
        del obj[KEY]


def test_default_key() -> None:
    """Test setting and restoring of existing dict keys."""
    obj = {KEY: "default_value"}
    with pyaud.plugins._TempEnvVar(obj, **{KEY: "temp_value"}):
        assert obj[KEY] == "temp_value"

    assert obj[KEY] == "default_value"


def test_plugins_call() -> None:
    """Get coverage on ``Plugin.__call__.``"""
    assert pyaud.plugins.Plugin("name")() == 0


def test_not_a_valid_git_repository(
    monkeypatch: pytest.MonkeyPatch, main: FixtureMain
) -> None:
    """Test exit when not in a git repository.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """

    def _populate(_: str | None = None):
        raise git.InvalidGitRepositoryError

    monkeypatch.setattr("pyaud.files.populate", _populate)
    with pytest.raises(SystemExit) as err:
        assert main("") == 1

    assert pyaud.messages.INVALID_REPOSITORY.split(":", maxsplit=1)[0] in str(
        err.value
    )


def test_staged_file_removed(main: FixtureMain) -> None:
    """Test run blocked when staged file removed.

    Without this, files that do not exist could be passed to plugin
    args.

    :param main: Patch package entry point.
    """

    class _MockAudit(pyaud.plugins.Audit):
        def audit(self, *_: str, **__: bool) -> int:  # type: ignore
            """Nothing to do."""

    pyaud.plugins.register(plugin_name[1])(_MockAudit)
    pyaud.files.append(Path.cwd() / python_file[1])
    with pytest.raises(SystemExit) as err:
        main(AUDIT, f"--audit={plugin_name[1]}")

    assert pyaud.messages.REMOVED_FILES in str(err.value)


def test_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch, main: FixtureMain
) -> None:
    """Test commandline ``KeyboardInterrupt``.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """

    def _pyaud(*_: str, **__: bool) -> t.Any:
        raise KeyboardInterrupt

    monkeypatch.setattr("pyaud._main._pyaud", _pyaud)
    with pytest.raises(SystemExit) as err:
        main(plugin_name[1])

    assert pyaud.messages.KEYBOARD_INTERRUPT in str(err.value)
