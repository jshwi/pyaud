"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments,too-few-public-methods
# pylint: disable=protected-access
import copy
import datetime
import json
import os
import subprocess
import time
import typing as t
from pathlib import Path

import pytest

import pyaud

# noinspection PyProtectedMember
import pyaud._config as pc

from . import (
    AUDIT,
    CLEAN,
    COMMIT,
    CONFPY,
    DOCS,
    EXCLUDE,
    FILE,
    FILES,
    FORMAT,
    FORMAT_DOCS,
    GITIGNORE,
    INDEXING,
    INIT,
    INITIAL_COMMIT,
    KEY,
    LINT,
    MODULE,
    MODULES,
    NAME,
    OS_GETCWD,
    PACKAGE,
    PLUGIN_CLASS,
    PLUGIN_NAME,
    PYAUD_FILES_POPULATE,
    PYAUD_PLUGINS_PLUGINS,
    README,
    REPO,
    SP_OPEN_PROC,
    SRC,
    TESTS,
    TYPE_ERROR,
    UNPATCH_REGISTER_DEFAULT_PLUGINS,
    VALUE,
    WHITELIST_PY,
    AppFiles,
    MakeTreeType,
    MockActionPluginFactoryType,
    MockAudit,
    MockCallStatusType,
    MockMainType,
    NoColorCapsys,
    NotSubclassed,
    Tracker,
    git,
)


@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
@pytest.mark.parametrize(
    "arg,index,expected",
    [
        (
            "",
            0,
            (
                "modules = [\n",
                '    "audit",\n',
                '    "clean",\n',
                '    "generate-rcfile"\n',
                "]",
            ),
        ),
        (
            "all",
            0,
            (
                "audit           -- Read from [audit] key in config",
                "clean           -- Remove all unversioned package files "
                "recursively",
                "generate-rcfile -- Print rcfile to stdout",
            ),
        ),
        ("not-a-module", 1, ("No such module: not-a-module",)),
    ],
    ids=["no-pos", "all-modules", "invalid-pos"],
)
def test_help(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    arg: str,
    index: int,
    expected: t.Tuple[str, ...],
) -> None:
    """Test expected output for help with no default plugins.

    Test no positional argument for json array of plugins.
    Test ``audit`` positional argument and docstring display for
    assortment of plugins.
    Test all and display of all module docstrings for assortment of
    test plugins.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param arg: Positional argument for ```pyaud modules``.
    :param index: Index 0 returns stdout from ``readouterr`` and 1
        returns stderr.
    :param expected: Expected result when calling command.
    """
    monkeypatch.setattr("pyaud.plugins.load", lambda: None)
    with pytest.raises(SystemExit):
        main(MODULES, arg)

    # index 0 returns stdout from ``readouterr`` and 1 returns stderr
    out = nocolorcapsys.readouterr()[index]
    assert all(i in out for i in expected)


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


def test_files_populate_proc(make_tree: MakeTreeType) -> None:
    """Test that populating an index is quicker when there are commits.

    Once there is a committed index we can index the paths from the
    repository, rather than compiling all files in the working dir and
    filtering out the non-versioned files later.

    :param make_tree: Create directory tree from dict mapping.
    """
    make_tree(
        Path.cwd(),
        {
            REPO: {SRC: {INIT: None}},
            "venv": {
                "pyvenv.cfg": None,
                "bin": {},
                "include": {},
                "share": {},
                SRC: {},
                "lib": {"python3.8": {"site-packages": {"six.py": None}}},
                "lib64": "lib",
            },
        },
    )

    # add venv to .gitignore
    gitignore = Path.cwd() / GITIGNORE
    gitignore.write_text("venv\n")

    def _old_files_populate():
        indexed = []
        for path in Path.cwd().rglob("*.py"):
            if path.name not in pc.DEFAULT_CONFIG[INDEXING][
                EXCLUDE
            ] and not git.ls_files(
                "--error-unmatch", path, file=os.devnull, suppress=True
            ):
                indexed.append(path)

        return indexed

    git.add(".")
    start = time.process_time()
    no_commit_files = _old_files_populate()
    stop = time.process_time()
    time_no_commit = stop - start
    pyaud.files.clear()
    start = time.process_time()
    pyaud.files.populate()
    commit_files = list(pyaud.files)
    stop = time.process_time()
    time_commit = stop - start
    assert time_no_commit > time_commit
    assert no_commit_files == commit_files


@pytest.mark.usefixtures("unpatch_setuptools_find_packages")
def test_get_packages(
    monkeypatch: pytest.MonkeyPatch, make_tree: t.Any
) -> None:
    """Test process when searching for project's package.

    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree: Create directory tree from dict mapping.
    """
    # undo patch to ``setuptools``
    # ============================
    cwd = os.getcwd()
    monkeypatch.undo()
    monkeypatch.setattr(OS_GETCWD, lambda: cwd)

    # search for only package
    # =======================
    make_tree(Path.cwd(), {PACKAGE[1]: {INIT: None}})
    assert pyaud._utils.get_packages() == [PACKAGE[1]]
    assert pyaud.package() == PACKAGE[1]

    # search for ambiguous package
    # ============================
    make_tree(Path.cwd(), {PACKAGE[2]: {INIT: None}, PACKAGE[3]: {INIT: None}})
    assert pyaud._utils.get_packages() == [PACKAGE[1], PACKAGE[2], PACKAGE[3]]
    assert pyaud.package() is None

    # search for package with the same name as repo
    # =============================================
    make_tree(Path.cwd(), {REPO: {INIT: None}})
    assert pyaud._utils.get_packages() == [
        PACKAGE[1],
        PACKAGE[2],
        PACKAGE[3],
        REPO,
    ]
    assert pyaud.package() == REPO

    # search for configured package
    # =============================
    pc.toml["packages"]["name"] = PACKAGE[2]
    assert pyaud.package() == PACKAGE[2]


def test_get_subpackages(
    monkeypatch: pytest.MonkeyPatch, make_tree: MakeTreeType
) -> None:
    """Test process when searching for project's package.

    Assert that subdirectories are not returned with import syntax, i.e.
    dot separated, and that only the parent package names are returned.

    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree: Create directory tree from dict mapping.
    """
    # undo patch to ``setuptools``
    # ============================
    cwd = os.getcwd()
    monkeypatch.undo()
    monkeypatch.setattr(OS_GETCWD, lambda: cwd)

    # create a tree of sub-packages with their own __init__.py files.
    make_tree(
        Path.cwd(),
        {
            REPO: {
                INIT: None,
                SRC: {
                    INIT: None,
                    "client": {INIT: None},
                    "server": {INIT: None},
                    "shell": {INIT: None},
                    "stdout": {INIT: None},
                },
            }
        },
    )

    # assert no dot separated packages are returned and that only the
    # parent packages name is returned
    assert pyaud._utils.get_packages() == [REPO]


def test_exclude(make_tree: MakeTreeType) -> None:
    """Test exclusions and inclusions with toml config.

    :param make_tree: Create directory tree from dict mapping.
    """
    webapp = {"_blog.py": None, "_config.py": None, "db.py": None, INIT: None}
    make_tree(
        Path.cwd(),
        {
            WHITELIST_PY: None,
            DOCS: {CONFPY: None},
            "setup.py": None,
            "migrations": {
                "alembic.ini": None,
                "env.py": None,
                "README": None,
                "script.py.mako": None,
                "versions": {
                    "1b62f391f86f_add_adds_post_table.py": None,
                    "2c5aaad1d65e_add_adds_user_table.py": None,
                },
            },
            REPO: webapp,
        },
    )
    exclude = (WHITELIST_PY, CONFPY, "setup.py", "migrations")
    git.add(".")
    pyaud.files.add_exclusions(*exclude)
    pyaud.files.populate()
    assert not any(i in p.parts for i in exclude for p in pyaud.files)
    assert all(Path.cwd() / REPO / p in pyaud.files for p in webapp)


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


def test_get_plugin_logger() -> None:
    """Test logger available through uninstantiated ``BasePlugin``."""
    logger = pyaud.plugins.Plugin.logger()
    assert logger.name == pyaud.plugins.Plugin.__name__


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
    monkeypatch.setattr("pyaud._cli.__version__", "1.0.0")
    with pytest.raises(SystemExit):
        main("--version")

    out = nocolorcapsys.stdout().strip()
    assert out == "1.0.0"


def test_no_request(main: MockMainType, nocolorcapsys: NoColorCapsys) -> None:
    """Test continuation of regular ``argparse`` process.

    If ``IndexError`` is not captured with
    ``pyaud._main._version_request`` then an error message is displayed,
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


@pytest.mark.parametrize(
    "stdout,returncode,expected",
    [([COMMIT], 0, COMMIT), ([], 1, None)],
    ids=["zero", "non-zero"],
)
def test_get_commit_hash(
    monkeypatch: pytest.MonkeyPatch,
    stdout: t.List[str],
    returncode: int,
    expected: t.Optional[str],
) -> None:
    """Test output from ``pyaud._utils.get_commit_hash``.

    :param monkeypatch: Mock patch environment and attributes.
    :param stdout: Mock stdout to be returned from ``git rev-parse``.
    :param returncode: Mock return code from subprocess.
    :param expected: Expected result.
    """
    monkeypatch.setattr(
        "pyaud._utils.git.rev_parse", lambda *_, **__: returncode
    )
    monkeypatch.setattr("pyaud._utils.git.stdout", lambda: stdout)
    assert pyaud._utils.get_commit_hash() == expected


def test_working_tree_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test checker for clean working tree.

    :param tmp_path: Create and return a temporary directory for
        testing.
    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.undo()
    monkeypatch.setattr(OS_GETCWD, lambda: str(tmp_path / REPO))
    assert pyaud._utils.working_tree_clean()
    Path(Path.cwd() / FILE).touch()
    assert not pyaud._utils.working_tree_clean()


def test_time_output(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    mock_action_plugin_factory: MockActionPluginFactoryType,
) -> None:
    """Test tracking of durations in output.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    plugin = mock_action_plugin_factory({NAME: PLUGIN_CLASS[1]})[0]
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugin)
    main(PLUGIN_NAME[1], "-t")
    out = nocolorcapsys.stdout()
    assert "Plugin_1: Execution time:" in out


def test_restore_data_no_json(app_files: AppFiles) -> None:
    """Test pass on restoring empty file.

    No need to run any assertions; checking that no error is raised.

    :param app_files: App file locations object.
    """
    app_files.durations_file.touch()
    # noinspection PyUnresolvedReferences
    time_cache = pyaud._data.Record()
    # noinspection PyUnresolvedReferences
    pyaud._data.read(time_cache, app_files.durations_file)

    # short-cut for testing ``JSONIO.read`` which is basically identical
    # to ``pyaud._data.read``
    time_cache.path = app_files.durations_file  # type: ignore
    pyaud._objects.JSONIO.read(time_cache)  # type: ignore


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


def test_nested_times(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    app_files: AppFiles,
    mock_action_plugin_factory: MockActionPluginFactoryType,
) -> None:
    """Test reading and writing of times within nested processes.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param app_files: App file locations object.
    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    monkeypatch.setattr("pyaud._data._TimeKeeper._starter", lambda x: 0)
    monkeypatch.setattr("pyaud._data._TimeKeeper._stopper", lambda x: 1)
    expected = {
        REPO: {
            "<class 'pyaud._default.Audit'>": [1],
            "<class 'tests._test.test_nested_times.<locals>.P1'>": [1],
            "<class 'tests._test.test_nested_times.<locals>.P2'>": [1],
        }
    }
    default_config = pc.DEFAULT_CONFIG
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(default_config)
    test_default[AUDIT][MODULES] = [PLUGIN_NAME[1], PLUGIN_NAME[2]]
    app_files.global_config_file.write_text(pc.toml.dumps(test_default))
    pyaud.plugins.register(AUDIT)(pyaud._default._Audit)  # type: ignore
    plugin_one, plugin_two = mock_action_plugin_factory(
        {NAME: PLUGIN_CLASS[2]}, {NAME: PLUGIN_CLASS[2]}
    )
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugin_one)
    pyaud.plugins.register(name=PLUGIN_NAME[2])(plugin_two)

    # noinspection PyUnresolvedReferences
    pyaud._data.record.clear()
    assert sorted(pyaud.plugins.registered()) == [
        AUDIT,
        PLUGIN_NAME[1],
        PLUGIN_NAME[2],
    ]
    main(AUDIT)
    actual = json.loads(app_files.durations_file.read_text(encoding="utf-8"))
    assert all(i in actual for i in expected)


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
        def exe(self) -> t.List[str]:
            return [self.pylint]

        def audit(self, *args: t.Any, **kwargs: bool) -> t.Any:
            return self.subprocess[self.pylint].call(*args, **kwargs)

    pyaud.plugins.register(name=LINT)(_Lint)
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    pyaud.files.append(Path.cwd() / FILE)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
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
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
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
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
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


@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
@pytest.mark.parametrize(
    "exclude,expected",
    [
        ([], ""),
        (
            [".env_diff", "instance_diff", ".cache_diff"],
            "Removing .cache_diff\n"
            "Removing .env_diff\n"
            "Removing instance_diff\n",
        ),
    ],
    ids=["no-exclude", EXCLUDE],
)
def test_clean_exclude(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    exclude: t.List[str],
    expected: str,
) -> None:
    """Test clean with and without exclude parameters.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param exclude: Files to exclude from ``git clean``.
    :param expected: Expected output from ``pyaud clean``.
    """
    Path(Path.cwd() / README).touch()
    git.init(file=os.devnull)  # type: ignore
    git.add(".")  # type: ignore
    git.commit("-m", INITIAL_COMMIT, file=os.devnull)  # type: ignore
    for exclusion in exclude:
        Path(Path.cwd() / exclusion).touch()

    main(CLEAN)
    assert nocolorcapsys.stdout() == expected


def test_make_generate_rcfile(nocolorcapsys: NoColorCapsys) -> None:
    """Test for correct output when running ``generate-rcfile``.

    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    pyaud._default.register_default_plugins()  # type: ignore
    pyaud.plugins.get("generate-rcfile")()
    assert (
        nocolorcapsys.stdout().strip()
        == pc.toml.dumps(pc.DEFAULT_CONFIG).strip()
    )


@pytest.mark.parametrize(
    "args,add,first",
    [([], [], ""), (["--clean"], [CLEAN], "pyaud clean")],
    ids=["no-args", CLEAN],
)
def test_audit_modules(
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    main: MockMainType,
    call_status: MockCallStatusType,
    args: t.List[str],
    add: t.List[str],
    first: str,
) -> None:
    """Test that the correct functions are called with ``make_audit``.

    Mock all functions in ``MODULES`` to do nothing so the test can
    confirm that all the functions that are meant to be run are run with
    the output that is displayed to the console in cyan. Confirm what
    the first and last functions being run are with the parametrized
    values.

    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param main: Patch package entry point.
    :param call_status: Patch function to not do anything. Optionally
        returns non-zero exit code (0 by default).
    :param args: Arguments for ``pyaud audit``.
    :param add: Function to add to the ``audit_modules`` list
    :param first: Expected first function executed.
    """
    seq = list(pc.DEFAULT_CONFIG[AUDIT][MODULES])
    seq.extend(add)
    mapping = {i: call_status(i) for i in seq}
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mapping)
    monkeypatch.setattr("pyaud._main._register_default_plugins", lambda: None)
    pyaud.plugins._plugins[AUDIT] = pyaud._default._Audit(  # type: ignore
        AUDIT
    )
    main(AUDIT, *args)
    del mapping[AUDIT]
    assert first in nocolorcapsys.stdout()


def test_environ_repo(app_files: AppFiles) -> None:
    """Test returning of repo name with env.

    :param app_files: App file locations object.
    """
    assert app_files.user_project_dir.name == Path.cwd().name


@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
@pytest.mark.parametrize(
    "arg,expected",
    [
        ("", pyaud.plugins.registered()),
        (AUDIT, ["audit -- Read from [audit] key in config"]),
        ("all", pyaud.plugins.registered()),
    ],
    ids=["no-pos", MODULE, "all-modules"],
)
def test_help_with_plugins(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    arg: str,
    expected: t.Tuple[str, ...],
) -> None:
    """Test expected output for help after plugins have been loaded.

    Test no positional argument for json array of keys.
    Test ``audit`` positional argument and docstring display.
    Test all and display of all module docstrings.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param arg: Positional argument for ```pyaud modules``.
    :param expected: Expected result when calling command.
    """
    with pytest.raises(SystemExit):
        main(MODULES, arg)

    out = nocolorcapsys.stdout()
    assert all(i in out for i in expected)


@pytest.mark.usefixtures(UNPATCH_REGISTER_DEFAULT_PLUGINS)
def test_suppress(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    app_files: AppFiles,
    nocolorcapsys: NoColorCapsys,
    make_tree: MakeTreeType,
) -> None:
    """Test that audit proceeds through errors with ``--suppress``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param app_files: App file locations object.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param make_tree: Create directory tree from dict mapping.
    """
    pyaud.plugins.register(PLUGIN_NAME[1])(MockAudit)
    default_config = pc.DEFAULT_CONFIG
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(default_config)
    test_default[AUDIT][MODULES] = [PLUGIN_NAME[1]]
    app_files.global_config_file.write_text(pc.toml.dumps(test_default))
    make_tree(Path.cwd(), {FILE: None, DOCS: {CONFPY: None}})
    pyaud.files.append(Path.cwd() / FILE)
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main(AUDIT, "--suppress")
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
        def plugins(self) -> t.List[str]:
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
