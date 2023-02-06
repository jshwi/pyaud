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

import git
import pytest

import pyaud

# noinspection PyProtectedMember
import pyaud._objects as pc

from . import (
    AUDIT,
    COMMIT,
    CONFPY,
    DOCS,
    FILE,
    FILES,
    FORMAT,
    FORMAT_DOCS,
    INIT,
    KEY,
    LINT,
    MODULES,
    NAME,
    PLUGIN_CLASS,
    PLUGIN_NAME,
    PYAUD_FILES_POPULATE,
    REPO,
    SP_OPEN_PROC,
    TESTS,
    TYPE_ERROR,
    UNPATCH_REGISTER_DEFAULT_PLUGINS,
    VALUE,
    FixtureMockRepo,
    MakeTreeType,
    MockActionPluginFactoryType,
    MockAudit,
    MockMainType,
    NoColorCapsys,
    NotSubclassed,
    Tracker,
)


def test_mapping_class() -> None:
    """Get coverage on ``Mapping`` abstract methods."""
    pc.toml.clear()
    assert repr(pc.toml) == "<_Toml {}>"
    pc.toml.update({KEY: VALUE})
    assert len(pc.toml) == 1
    for key in pc.toml:
        assert key == KEY

    del pc.toml[KEY]
    assert KEY not in pc.toml


def test_register_plugin_name_conflict_error(
    mock_action_plugin_factory: MockActionPluginFactoryType,
) -> None:
    """Test ``NameConflictError`` is raised when same name provided.

    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    unique = "test-register-plugin-name-conflict-error"
    plugin_one, plugin_two = mock_action_plugin_factory(
        {NAME: PLUGIN_CLASS[1]}, {NAME: PLUGIN_CLASS[2]}
    )
    pyaud.plugins.register(name=unique)(plugin_one)
    with pytest.raises(pyaud.exceptions.NameConflictError) as err:
        pyaud.plugins.register(name=unique)(plugin_two)

    assert str(err.value) == f"plugin name conflict at Plugin_2: '{unique}'"


def test_register_invalid_type() -> None:
    """Test correct error is displayed when registering unknown type."""
    unique = "test-register-invalid-type"
    with pytest.raises(TypeError) as err:
        pyaud.plugins.register(name=unique)(NotSubclassed)  # type: ignore

    assert TYPE_ERROR in str(err.value)


def test_plugin_assign_non_type_value() -> None:
    """Test assigning of incompatible type to `_Plugin` instance."""
    unique = "test-plugin-assign-non-type-value"
    with pytest.raises(TypeError) as err:
        pyaud.plugins.register(name=unique)(NotSubclassed)  # type: ignore

    assert TYPE_ERROR in str(err.value)


def test_plugin_assign_non_type_key() -> None:
    """Test assigning of incompatible type to `_Plugin` instance."""
    unique = "test-plugin-assign-non-type-key"
    with pytest.raises(TypeError) as err:

        class Plugin(NotSubclassed):
            """Nothing to do."""

            def __call__(self, *args: t.Any, **kwargs: bool) -> t.Any:
                """Nothing to do."""

        pyaud.plugins.register(name=unique)(Plugin)  # type: ignore

    assert TYPE_ERROR in str(err.value)


def test_plugin_mro(
    mock_action_plugin_factory: MockActionPluginFactoryType,
) -> None:
    """Assert that plugins can inherit other plugins.

    Prior to this commit ``PluginType``s were only permitted, and not
    children of ``PluginType``s.

    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    plugin_one, plugin_two = mock_action_plugin_factory(
        {NAME: PLUGIN_CLASS[1]}, {NAME: PLUGIN_CLASS[2]}
    )
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugin_one)
    pyaud.plugins.register(name=PLUGIN_NAME[2])(plugin_two)
    assert "plugin-1" in pyaud.plugins.mapping()
    assert "plugin-2" in pyaud.plugins.mapping()


def test_print_version(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test printing of version on commandline.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    monkeypatch.setattr("pyaud._config.__version__", "1.0.0")
    with pytest.raises(SystemExit):
        main("--version")

    out = nocolorcapsys.stdout().strip()
    assert out == "1.0.0"


def test_no_request(main: MockMainType, nocolorcapsys: NoColorCapsys) -> None:
    """Test continuation of regular ``argparse`` process.

    If ``IndexError`` is not captured with
    ``pyaud._core._version_request`` then an error message is displayed,
    and not ``argparse``'s help menu on non-zero exit status.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    with pytest.raises(SystemExit):
        main()

    assert (
        "pyaud: error: the following arguments are required: MODULE"
        in nocolorcapsys.stderr()
    )


def test_get_commit_hash_pass(mock_repo: FixtureMockRepo) -> None:
    """Test output from passing ``pyaud._utils.get_commit_hash``.

    :param mock_repo: Mock ``git.Repo`` class.
    """
    mock_repo(rev_parse=lambda _: COMMIT)
    assert pyaud._utils.get_commit_hash() == COMMIT


def test_get_commit_hash_fail(mock_repo: FixtureMockRepo) -> None:
    """Test output from failing ``pyaud._utils.get_commit_hash``.

    :param mock_repo: Mock ``git.Repo`` class.
    """

    def _raise(_: str) -> None:
        raise git.GitCommandError("rev_parse")

    mock_repo(rev_parse=_raise)
    assert pyaud._utils.get_commit_hash() is None


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
    mock_action_plugin_factory: MockActionPluginFactoryType,
) -> None:
    """Test ``CommandNotFoundError`` warning with ``Subprocess``.

    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    plugins = mock_action_plugin_factory(
        {
            NAME: PLUGIN_CLASS[1],
            "exe": "not_a_command",
            "action": lambda x, *y, **z: x.subprocess[x.exe_str].call(*y, **z),
        }
    )
    pyaud.plugins.register("test-command-not-found-error")(plugins[0])
    exe = pyaud.plugins.get("test-command-not-found-error")
    with pytest.warns(
        RuntimeWarning, match="not_a_command: Command not found"
    ):
        exe()


def test_warn_no_fix(
    monkeypatch: pytest.MonkeyPatch, main: MockMainType
) -> None:
    """Test error when audit fails and cannot be fixed.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """

    class _Lint(pyaud.plugins.Audit):
        """Lint code with ``pylint``."""

        pylint = "pylint"

        @property
        def exe(self) -> list[str]:
            return [self.pylint]

        def audit(self, *args: str, **kwargs: bool) -> int:
            return self.subprocess[self.pylint].call(*args, **kwargs)

    pyaud.plugins.register(name=LINT)(_Lint)
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    pyaud.files.append(Path.cwd() / FILE)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda *_: None)
    with pytest.raises(pyaud.exceptions.AuditError):
        main(LINT)


def test_check_command_no_files_found(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test plugin output when no files are found.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    pyaud.plugins.register(PLUGIN_NAME[1])(MockAudit)
    main(PLUGIN_NAME[1])
    assert nocolorcapsys.stdout().strip() == "No files found"


def test_check_command_fail_on_suppress(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    make_tree: MakeTreeType,
) -> None:
    """Test plugin output when process fails while crash suppressed.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param make_tree: Create directory tree from dict mapping.
    """
    pyaud.plugins.register(PLUGIN_NAME[1])(MockAudit)
    make_tree(Path.cwd(), {FILES: None, "docs": {CONFPY: None}})
    pyaud.files.append(Path.cwd() / FILES)
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda *_: None)
    main(PLUGIN_NAME[1], "--suppress")
    assert "Failed: returned non-zero exit status" in nocolorcapsys.stderr()


def test_audit_error_did_no_pass_all_checks(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    mock_action_plugin_factory: MockActionPluginFactoryType,
) -> None:
    """Test raising of ``AuditError``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """

    def action(_, *__: int, **___: bool) -> int:
        raise subprocess.CalledProcessError(1, "returned non-zero exit status")

    plugins = mock_action_plugin_factory(
        {NAME: PLUGIN_CLASS[1], "action": action}
    )
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugins[0])
    pyaud.files.append(Path.cwd() / FILES)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda *_: None)
    with pytest.raises(pyaud.exceptions.AuditError):
        main(PLUGIN_NAME[1])


def test_no_exe_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default value for exe property.

    :param monkeypatch: Mock patch environment and attributes.
    """
    unique = datetime.datetime.now().strftime("%d%m%YT%H%M%S")
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    pyaud.files.append(Path.cwd() / FILES)
    pyaud.plugins.register(name=unique)(MockAudit)
    assert pyaud.plugins.get(unique).exe == []


def test_environ_repo() -> None:
    """Test returning of repo name with env."""
    assert Path.cwd().name == Path.cwd().name


@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
def test_modules(main: MockMainType, nocolorcapsys: NoColorCapsys) -> None:
    """Test expected output for help after plugins have been loaded.

    Test no positional argument for json array of keys.
    Test ``audit`` positional argument and docstring display.
    Test all and display of all module docstrings.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    main(MODULES)
    out = nocolorcapsys.stdout()
    assert out == (
        "\naudit   -- Read from [audit] key in config\n"
        "modules -- Display all available plugins and their documentation\n"
    )


@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
def test_suppress(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    make_tree: MakeTreeType,
) -> None:
    """Test that audit proceeds through errors with ``--suppress``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param make_tree: Create directory tree from dict mapping.
    """
    pyaud.plugins.register(PLUGIN_NAME[1])(MockAudit)
    make_tree(Path.cwd(), {FILE: None, DOCS: {CONFPY: None}})
    pyaud.files.append(Path.cwd() / FILE)
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda *_: None)
    main(AUDIT, f"--audit={PLUGIN_NAME[1]}", "--suppress")
    assert "Failed: returned non-zero exit status" in nocolorcapsys.stderr()


def test_parametrize(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    mock_action_plugin_factory: MockActionPluginFactoryType,
) -> None:
    """Test class for running multiple plugins.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
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
        {NAME: PLUGIN_CLASS[1]}, {NAME: PLUGIN_CLASS[2]}
    )
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugin_one)
    pyaud.plugins.register(name=PLUGIN_NAME[2])(plugin_two)
    pyaud.plugins.register(name="params")(_Params)
    main("params")
    out = nocolorcapsys.stdout()
    assert f"pyaud {PLUGIN_NAME[1]}" in out
    assert f"pyaud {PLUGIN_NAME[2]}" in out


@pytest.mark.usefixtures("unpatch_plugins_load")
def test_imports(
    monkeypatch: pytest.MonkeyPatch, make_tree: MakeTreeType
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
    assert "no plugin named `not-a-module` found" in std.err
