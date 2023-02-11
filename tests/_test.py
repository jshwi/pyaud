"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments,too-few-public-methods
# pylint: disable=protected-access,no-member
from __future__ import annotations

import copy
import datetime
import subprocess
import typing as t
from pathlib import Path
from subprocess import CalledProcessError

import git
import pytest

import pyaud

# noinspection PyProtectedMember
import pyaud._config as pc

from . import (
    DEFAULT_KEY,
    DOCS,
    FILE,
    FILES,
    FORMAT,
    FORMAT_DOCS,
    INIT,
    KEY,
    LINT,
    MODULES,
    PARAMS,
    PLUGIN_CLASS,
    PLUGIN_NAME,
    REPO,
    STRFTIME,
    TESTS,
    UNPATCH_REGISTER_DEFAULT_PLUGINS,
    VALUE,
    FixtureMain,
    FixtureMakeTree,
    FixtureMockActionPluginFactory,
    FixtureMockRepo,
    FixtureMockSpallSubprocessOpenProcess,
    MockAudit,
    PluginTuple,
    Tracker,
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
        PluginTuple(PLUGIN_CLASS[1]), PluginTuple(PLUGIN_CLASS[2])
    )
    pyaud.plugins.register(name=unique)(plugin_one)
    with pytest.raises(pyaud.exceptions.NameConflictError) as err:
        pyaud.plugins.register(name=unique)(plugin_two)

    assert str(err.value) == pyaud.messages.NAME_CONFLICT_ERROR.format(
        plugin=PLUGIN_CLASS[2], name=unique
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
        PluginTuple(PLUGIN_NAME[1]), PluginTuple(PLUGIN_NAME[2])
    )
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugin_one)
    pyaud.plugins.register(name=PLUGIN_NAME[2])(plugin_two)
    assert "plugin-1" in pyaud.plugins.mapping()
    assert "plugin-2" in pyaud.plugins.mapping()


def test_get_commit_hash_fail(mock_repo: FixtureMockRepo) -> None:
    """Test output from failing ``pyaud._utils.get_commit_hash``.

    :param mock_repo: Mock ``git.Repo`` class.
    """

    def _raise(_: str) -> None:
        raise git.GitCommandError("rev_parse")

    mock_repo(rev_parse=_raise)
    # noinspection PyUnresolvedReferences
    assert pyaud._cache._get_commit_hash() is None


def test_plugin_deepcopy_with_new() -> None:
    """Test that ``TypeError`` is not raised.

    No assertions run; test passes if the following is not raised:
    TypeError: __new__() missing 1 required positional argument: 'name'
    """
    copy.deepcopy(pyaud.plugins._plugins)
    assert isinstance(
        pyaud.plugins.Plugin(  # pylint: disable=unnecessary-dunder-call
            REPO
        ).__deepcopy__(REPO),
        pyaud.plugins.Plugin,
    )


def test_command_not_found_error(
    mock_action_plugin_factory: FixtureMockActionPluginFactory,
) -> None:
    """Test ``CommandNotFoundError`` warning with ``Subprocess``.

    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    plugins = mock_action_plugin_factory(
        PluginTuple(
            PLUGIN_CLASS[1],
            "not_a_command",
            lambda x, *y, **z: x.subprocess[x.exe_str].call(*y, **z),
        )
    )
    pyaud.plugins.register("test-command-not-found-error")(plugins[0])
    exe = pyaud.plugins.get("test-command-not-found-error")
    with pytest.warns(
        RuntimeWarning, match="not_a_command: Command not found"
    ):
        exe()


def test_check_command_no_files_found(
    main: FixtureMain, capsys: pytest.CaptureFixture
) -> None:
    """Test plugin output when no files are found.

    :param main: Patch package entry point.
    :param capsys: Capture sys out and err.
    """
    pyaud.plugins.register(PLUGIN_NAME[1])(MockAudit)
    returncode = main(PLUGIN_NAME[1])
    std = capsys.readouterr()
    assert returncode == 0
    assert "No files found" in std.out


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
        PluginTuple(PLUGIN_NAME[1], action=action)
    )
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugins[0])
    pyaud.files.append(Path.cwd() / FILES)
    returncode = main(PLUGIN_NAME[1])
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
    pyaud.files.append(Path.cwd() / FILES)
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
    returncode = main(MODULES)
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

    pyaud.plugins.register(PLUGIN_NAME[1])(_MockAudit)
    pyaud.files.append(Path.cwd() / FILE)
    returncode = main("audit", f"--audit={PLUGIN_NAME[1]}")
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

    pyaud.plugins.register(PLUGIN_NAME[1])(_MockAudit)
    pyaud.files.append(Path.cwd() / FILE)
    returncode = main("audit", f"--audit={PLUGIN_NAME[1]}")
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
            return [PLUGIN_NAME[1], PLUGIN_NAME[2]]

    plugin_one, plugin_two = mock_action_plugin_factory(
        PluginTuple(PLUGIN_NAME[1]), PluginTuple(PLUGIN_NAME[2])
    )
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugin_one)
    pyaud.plugins.register(name=PLUGIN_NAME[2])(plugin_two)
    pyaud.plugins.register(name=PARAMS)(_Params)
    returncode = main(PARAMS)
    std = capsys.readouterr()
    assert returncode == 0
    assert f"pyaud {PLUGIN_NAME[1]}" in std.out
    assert f"pyaud {PLUGIN_NAME[2]}" in std.out


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
    make_tree(Path.cwd(), {"plugins": {INIT: None, FILE: None}})
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
        ("Docs", DOCS),
        ("Files", FILES),
        ("Format", FORMAT),
        ("FormatDocs", FORMAT_DOCS),
        ("FormatFString", "format-f-string"),
        ("Imports", "imports"),
        ("Lint", LINT),
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
            return [PLUGIN_NAME[1]]

    plugins = mock_action_plugin_factory(
        PluginTuple(PLUGIN_NAME[1], "not_a_command", lambda x, *y, **z: 1)
    )
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugins[0])
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
            PLUGIN_CLASS[1],
            "command",
            lambda x, *y, **z: x.subprocess[x.exe_str].call(*y, **z),
        )
    )
    pyaud.plugins.register(PLUGIN_NAME[1])(plugins[0])
    exe = pyaud.plugins.get(PLUGIN_NAME[1])
    assert (
        str(exe.subprocess)
        == "<_SubprocessFactory {'command': <Subprocess (command)>}>"
    )


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
