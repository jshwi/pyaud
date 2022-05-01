"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments,cell-var-from-loop
# pylint: disable=too-few-public-methods,unused-variable,protected-access
import copy
import datetime
import json
import logging
import logging.config as logging_config
import logging.handlers as logging_handlers
import os
import subprocess
import time
import typing as t
from pathlib import Path
from subprocess import CalledProcessError

import pytest

import pyaud
from pyaud import environ as pe

from . import (
    COMMIT,
    CONFPY,
    CRITICAL,
    DEBUG,
    ERROR,
    FILES,
    GITIGNORE,
    INFO,
    INIT,
    INITIAL_COMMIT,
    OS_GETCWD,
    PYAUD_FILES_POPULATE,
    PYAUD_PLUGINS_PLUGINS,
    README,
    REPO,
    SP_OPEN_PROC,
    TYPE_ERROR,
    WARNING,
    WHITELIST_PY,
    NoColorCapsys,
    Tracker,
)


def test_get_branch_unique() -> None:
    """Test that ``get_branch`` returns correct branch."""
    Path(Path.cwd() / README).touch()
    branch = datetime.datetime.now().strftime("%d%m%YT%H%M%S")
    pyaud.git.add(".", devnull=True)
    pyaud.git.commit("-m", INITIAL_COMMIT, devnull=True)
    pyaud.git.checkout("-b", branch, devnull=True)
    assert pyaud._utils.branch() == branch  # pylint: disable=protected-access


def test_get_branch_initial_commit() -> None:
    """Test that ``get_branch`` returns None.

    Test when run from a commit with no parent commits i.e. initial
    commit.
    """
    Path(Path.cwd() / README).touch()
    pyaud.git.add(".")
    pyaud.git.commit("-m", INITIAL_COMMIT)
    pyaud.git.rev_list("--max-parents=0", "HEAD", capture=True)
    pyaud.git.checkout(pyaud.git.stdout()[0])
    assert pyaud._utils.branch() is None  # pylint: disable=protected-access


@pytest.mark.parametrize("default", [CRITICAL, ERROR, WARNING, INFO, DEBUG])
@pytest.mark.parametrize("flag", ["", "-v", "-vv", "-vvv", "-vvvv"])
def test_loglevel(
    monkeypatch: pytest.MonkeyPatch, main: t.Any, default: str, flag: str
) -> None:
    """Test the right loglevel is set when parsing the commandline.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param default: Default loglevel configuration.
    :param flag: Verbosity level commandline flag.
    """
    levels = {
        "": [CRITICAL, ERROR, WARNING, INFO, DEBUG],
        "-v": [ERROR, WARNING, INFO, DEBUG, DEBUG],
        "-vv": [WARNING, INFO, DEBUG, DEBUG, DEBUG],
        "-vvv": [INFO, DEBUG, DEBUG, DEBUG, DEBUG],
        "-vvvv": [DEBUG, DEBUG, DEBUG, DEBUG, DEBUG],
    }
    pyaud.config.toml["logging"]["root"]["level"] = default
    pe.GLOBAL_CONFIG_FILE.write_text(pyaud.config.toml.dumps())

    # dummy call to non-existing plugin to evaluate multiple -v
    # arguments
    monkeypatch.setattr(
        PYAUD_PLUGINS_PLUGINS, {"module": lambda *_, **__: None}
    )
    pyaud.config.configure_global()
    main("module", flag)
    assert (
        logging.getLevelName(logging.root.level)
        == levels[flag][levels[""].index(default)]
    )


def test_del_key_in_context():
    """Confirm there is no error raised when deleting temp key-value."""
    obj = {}
    # noinspection PyProtectedMember
    with pyaud.config.TempEnvVar(  # pylint: disable=protected-access
        obj, key="value"
    ):
        assert obj["key"] == "value"
        del obj["key"]


@pytest.mark.usefixtures("unpatch_register_default_plugins")
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
    main: t.Any,
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
        main("modules", arg)

    # index 0 returns stdout from ``readouterr`` and 1 returns stderr
    out = nocolorcapsys.readouterr()[index]
    assert all(i in out for i in expected)


def test_mapping_class() -> None:
    """Get coverage on ``Mapping`` abstract methods."""
    pyaud.config.toml.clear()
    assert repr(pyaud.config.toml) == "<_Toml {}>"
    pyaud.config.toml.update({"key": "value"})
    assert len(pyaud.config.toml) == 1
    for key in pyaud.config.toml:
        assert key == "key"

    del pyaud.config.toml["key"]
    assert "key" not in pyaud.config.toml


def test_toml() -> None:
    """Assert "$HOME/.config/pyaud.toml" is created and loaded.

    Create "$HOME/.pyaudrc" and "$PROJECT_DIR/.pyaudrc" load them,
    ensuring that each level up overrides changes from lower level
    configs whilst, keeping the remaining changes. Create
    "$PROJECT_DIR/pyproject.toml" and test the same, which will override
    all previous configs.
    """
    # base config is created and loaded
    # =================================
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(
        pyaud.config.DEFAULT_CONFIG
    )
    assert dict(pyaud.config.toml) == test_default

    # instantiate a new dict object
    # =============================
    # preserve the test default config
    home_rcfile = dict(test_default)
    home_rcfile["clean"]["exclude"].append("_build")
    home_rcfile["logging"]["handlers"]["default"].update(
        {"class": "logging.handlers.StreamHandler"}
    )
    home_rcfile["logging"]["version"] = 2
    pe.USER_CONFIG_FILE.write_text(
        pyaud.config.toml.dumps(home_rcfile), pe.ENCODING
    )

    # reset the dict to the test default
    # ==================================
    # test the the changes made to clean are inherited through the
    # config hierarchy but not configured in this dict
    project_rcfile = dict(test_default)
    project_rcfile["logging"]["version"] = 3
    pe.PROJECT_CONFIG_FILE.write_text(
        pyaud.config.toml.dumps(project_rcfile), pe.ENCODING
    )

    # load "$HOME/.pyaudrc" and then "$PROJECT_DIR/.pyaudrc"
    # ======================================================
    # override "$HOME/.pyaudrc"
    pyaud.config.load_config()
    subtotal: t.Dict[str, t.Any] = dict(home_rcfile)
    subtotal["logging"]["version"] = 3
    subtotal["logging"]["handlers"]["default"]["filename"] = str(
        Path(
            subtotal["logging"]["handlers"]["default"]["filename"]
        ).expanduser()
    )
    assert dict(pyaud.config.toml) == subtotal

    # load pyproject.toml
    # ===================
    # pyproject.toml tools start with [tool.<PACKAGE_REPO>]
    pyproject_dict = {"tool": {pyaud.__name__: test_default}}
    changes = {"clean": {"exclude": []}, "logging": {"version": 4}}
    pyproject_dict["tool"][pyaud.__name__].update(changes)
    pe.PYPROJECT.write_text(
        pyaud.config.toml.dumps(pyproject_dict), pe.ENCODING
    )

    # ======================================================
    # override "$HOME/.pyaudrc"
    pyaud.config.load_config()
    subtotal["clean"]["exclude"] = []
    subtotal["logging"]["version"] = 4
    assert dict(pyaud.config.toml) == subtotal

    # load optional rcfile
    # ====================
    # this will override all others when passed to the commandline
    pos = {"audit": {"modules": ["files", "format", "format-docs"]}}
    opt_rc = Path.cwd() / "opt_rc"
    opt_rc.write_text(pyaud.config.toml.dumps(pos), pe.ENCODING)

    # load "$HOME/.pyaudrc" and then "$Path.cwd()/.pyaudrc"
    # ======================================================
    # override "$HOME/.pyaudrc"
    pyaud.config.load_config(opt_rc)
    subtotal["audit"] = {"modules": ["files", "format", "format-docs"]}
    assert dict(pyaud.config.toml) == subtotal


def test_toml_no_override_all(monkeypatch: pytest.MonkeyPatch) -> None:
    """Confirm error not raised for entire key being overridden.

     Test for when implementing hierarchical config loading.

        def configure(self):
            '''Do the configuration.'''

            config = self.config
            if 'version' not in config:
    >           raise ValueError("dictionary doesn't specify a version")
    E           ValueError: dictionary doesn't specify a version

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud.config.DEFAULT_CONFIG",
        copy.deepcopy(pyaud.config.DEFAULT_CONFIG),
    )
    pyaud.config.toml.clear()
    pyaud.config.load_config()  # base key-values
    pyaud.config.toml.loads(pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING))
    assert dict(pyaud.config.toml) == pyaud.config.DEFAULT_CONFIG
    pe.USER_CONFIG_FILE.write_text(
        pyaud.config.toml.dumps({"logging": {"root": {"level": "INFO"}}}),
        pe.ENCODING,
    )

    # should override:
    # {
    #      "version": 1,
    #      "disable_existing_loggers": True,
    #      "formatters": {...},
    #      "handlers": {...},
    #      "root": {
    #          "level": "DEBUG", "handlers": [...], "propagate": False,
    #      },
    # },
    # with:
    # {
    #      "version": 1,
    #      "disable_existing_loggers": True,
    #      "formatters": {...},
    #      "handlers": {...},
    #      "root": {
    #          "level": "INFO", "handlers": [...], "propagate": False,
    #      },
    # },
    # and not reduce it to:
    # {"root": {"level": "INFO"}}
    pyaud.config.load_config()

    # this here would raise a ``ValueError`` if not working as expected,
    # so on its own is an assertion
    logging_config.dictConfig(pyaud.config.toml["logging"])
    pyaud.config.DEFAULT_CONFIG["logging"]["root"]["level"] = "INFO"
    assert dict(pyaud.config.toml) == pyaud.config.DEFAULT_CONFIG


# noinspection DuplicatedCode
def test_backup_toml() -> None:
    """Test backing up of toml config in case file is corrupted."""

    def _corrupt_file(_configfile_contents: str) -> None:
        # make a non-parsable change to the configfile (corrupt it)
        _lines = _configfile_contents.splitlines()
        _string = 'format = "%(asctime)s %(levelname)s %(name)s %(message)s"'
        for _count, _line in enumerate(list(_lines)):
            if _line == _string:
                _lines.insert(_count, _string[-6:])

        pe.GLOBAL_CONFIG_FILE.write_text("\n".join(_lines), pe.ENCODING)

    # initialisation
    # ==============
    # originally there is no backup file (not until configure_global is
    # run)
    default_config = dict(pyaud.config.toml)
    assert not pe.GLOBAL_CONFIG_BAK_FILE.is_file()

    # assert corrupt configfile with no backup will simply reset
    configfile_contents = pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING)

    _corrupt_file(configfile_contents)
    pyaud.config.configure_global()
    pyaud.config.toml.loads(pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING))

    # assert corrupt configfile is no same as default
    assert dict(pyaud.config.toml) == default_config

    # create backupfile
    pyaud.config.configure_global()
    assert pe.GLOBAL_CONFIG_BAK_FILE.is_file()

    # ensure backupfile is a copy of the original config file
    # (overridden at every initialisation in the case of a change)
    configfile_contents = pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING)
    backupfile_contents = pe.GLOBAL_CONFIG_BAK_FILE.read_text(pe.ENCODING)
    assert configfile_contents == backupfile_contents

    # change to config
    # ================
    # this setting, by default, is True
    pyaud.config.toml["logging"]["disable_existing_loggers"] = False
    pe.GLOBAL_CONFIG_FILE.write_text(pyaud.config.toml.dumps(), pe.ENCODING)

    # now that there is a change the backup should be different to the
    # original until configure_global is run again
    # read configfile as only that file has been changed
    configfile_contents = pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING)
    assert configfile_contents != backupfile_contents
    pyaud.config.configure_global()

    # read both, as both have been changed
    configfile_contents = pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING)
    backupfile_contents = pe.GLOBAL_CONFIG_BAK_FILE.read_text(pe.ENCODING)
    assert configfile_contents == backupfile_contents

    # resolve corrupt file
    # ====================
    _corrupt_file(configfile_contents)

    # read configfile as only that file has been changed
    configfile_contents = pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING)

    # only configfile is corrupt, so check backup is not the same
    assert configfile_contents != backupfile_contents

    # resolve corruption
    # ==================
    pyaud.config.configure_global()
    configfile_contents = pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING)
    backupfile_contents = pe.GLOBAL_CONFIG_BAK_FILE.read_text(pe.ENCODING)

    # configfile should equal the backup file and all changes should be
    # retained
    assert configfile_contents == backupfile_contents
    pyaud.config.toml.loads(pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING))
    assert pyaud.config.toml["logging"]["disable_existing_loggers"] is False


def test_register_plugin_name_conflict_error() -> None:
    """Test ``NameConflictError`` is raised when same name provided."""
    unique = "test-register-plugin-name-conflict-error"

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name=unique)
    class PluginOne(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    with pytest.raises(pyaud.exceptions.NameConflictError) as err:

        # noinspection PyUnusedLocal
        @pyaud.plugins.register(name=unique)
        class PluginTwo(pyaud.plugins.Action):
            """Nothing to do."""

            def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
                """Nothing to do."""

    assert str(err.value) == f"plugin name conflict at PluginTwo: '{unique}'"


def test_register_invalid_type() -> None:
    """Test correct error is displayed when registering unknown type."""
    unique = "test-register-invalid-type"
    with pytest.raises(TypeError) as err:

        class NotSubclassed:
            """Nothing to do."""

        pyaud.plugins.register(name=unique)(NotSubclassed)  # type: ignore

    assert TYPE_ERROR in str(err.value)


def test_plugin_assign_non_type_value() -> None:
    """Test assigning of incompatible type to `_Plugin` instance."""
    unique = "test-plugin-assign-non-type-value"
    with pytest.raises(TypeError) as err:

        class _NonType:
            """Nothing to do."""

        pyaud.plugins.register(name=unique)(_NonType)  # type: ignore

    assert TYPE_ERROR in str(err.value)


def test_plugin_assign_non_type_key() -> None:
    """Test assigning of incompatible type to `_Plugin` instance."""
    unique = "test-plugin-assign-non-type-key"

    class Parent:
        """Nothing to do."""

    with pytest.raises(TypeError) as err:

        # noinspection PyUnusedLocal
        @pyaud.plugins.register(name=unique)  # type: ignore
        class Plugin(Parent):
            """Nothing to do."""

            def __call__(self, *args: t.Any, **kwargs: bool) -> t.Any:
                """Nothing to do."""

    assert TYPE_ERROR in str(err.value)


def test_files_populate_proc(make_tree: t.Any) -> None:
    """Test that populating an index is quicker when there are commits.

    Once there is a committed index we can index the paths from the
    repository, rather than compiling all files in the working dir and
    filtering out the non-versioned files later.

    :param make_tree: Create directory tree from dict mapping.
    """
    make_tree(
        Path.cwd(),
        {
            REPO: {"src": {INIT: None}},
            "venv": {
                "pyvenv.cfg": None,
                "bin": {},
                "include": {},
                "share": {},
                "src": {},
                "lib": {"python3.8": {"site-packages": {"six.py": None}}},
                "lib64": "lib",
            },
        },
    )

    # add venv to .gitignore
    Path(Path.cwd() / GITIGNORE).write_text("venv\n", pe.ENCODING)

    def _old_files_populate():
        indexed = []
        for path in Path.cwd().rglob("*.py"):
            if path.name not in pyaud.config.DEFAULT_CONFIG["indexing"][
                "exclude"
            ] and not pyaud.git.ls_files(
                "--error-unmatch", path, devnull=True, suppress=True
            ):
                indexed.append(path)

        return indexed

    pyaud.git.add(".")
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
    make_tree(Path.cwd(), {"first_package": {INIT: None}})
    assert pyaud.get_packages() == ["first_package"]
    assert pyaud.package() == "first_package"

    # search for ambiguous package
    # ============================
    make_tree(
        Path.cwd(),
        {"second_package": {INIT: None}, "third_package": {INIT: None}},
    )
    assert pyaud.get_packages() == [
        "first_package",
        "second_package",
        "third_package",
    ]
    assert pyaud.package() is None

    # search for package with the same name as repo
    # =============================================
    make_tree(Path.cwd(), {"repo": {INIT: None}})
    assert pyaud.get_packages() == [
        "first_package",
        "repo",
        "second_package",
        "third_package",
    ]
    assert pyaud.package() == "repo"

    # search for configured package
    # =============================
    pyaud.config.toml["packages"]["name"] = "second_package"
    assert pyaud.package() == "second_package"


def test_get_subpackages(
    monkeypatch: pytest.MonkeyPatch, make_tree: t.Any
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
            "repo": {
                INIT: None,
                "src": {
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
    assert pyaud.get_packages() == ["repo"]


def test_exclude_loads_at_main(main: t.Any) -> None:
    """Confirm project config is loaded with ``main``.

    :param main: Patch package entry point.
    """

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name="plugin")
    class Plugin(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    default_config = copy.deepcopy(pyaud.config.DEFAULT_CONFIG)
    project_config = copy.deepcopy(default_config)
    project_config["indexing"]["exclude"].append("project")
    test_project_toml_object = (
        pyaud.config._Toml()  # pylint: disable=protected-access
    )
    test_project_toml_object.update(project_config)
    pe.PROJECT_CONFIG_FILE.write_text(
        test_project_toml_object.dumps(), pe.ENCODING
    )
    assert "project" not in pyaud.config.toml["indexing"]["exclude"]

    main("plugin")

    assert "project" in pyaud.config.toml["indexing"]["exclude"]


def test_exclude(make_tree: t.Any) -> None:
    """Test exclusions and inclusions with toml config.

    param make_tree: Create directory tree from dict mapping.
    """
    webapp = {"_blog.py": None, "_config.py": None, "db.py": None, INIT: None}
    make_tree(
        Path.cwd(),
        {
            WHITELIST_PY: None,
            "docs": {"conf.py": None},
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
            "repo": webapp,
        },
    )
    exclude = (WHITELIST_PY, "conf.py", "setup.py", "migrations")
    pyaud.git.add(".")
    pyaud.files.add_exclusions(*exclude)
    pyaud.files.populate()
    assert not any(i in p.parts for i in exclude for p in pyaud.files)
    assert all(Path.cwd() / "repo" / p in pyaud.files for p in webapp)


# noinspection DuplicatedCode
def test_filter_logging_config_kwargs() -> None:
    """Test that no errors are raised for additional config kwargs."""
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(
        pyaud.config.DEFAULT_CONFIG
    )

    # patch `DEFAULT_CONFIG` for `TimedRotatingFileHandler`
    logfile = str(Path.cwd() / ".cache" / "pyaud" / "log" / "pyaud.log")
    test_default["logging"]["handlers"]["default"]["filename"] = logfile
    rcfile = dict(test_default)
    pe.PROJECT_CONFIG_FILE.write_text(
        pyaud.config.toml.dumps(rcfile), pe.ENCODING
    )
    pyaud.config.load_config()
    pyaud.config.configure_logging()
    logger = logging.getLogger("default").root
    handler = logger.handlers[0]
    assert isinstance(handler, logging_handlers.TimedRotatingFileHandler)
    assert handler.when.casefold() == "d"  # type: ignore
    assert handler.backupCount == 60  # type: ignore
    assert handler.stream.buffer.name == logfile  # type: ignore

    # patch `DEFAULT_CONFIG` for `StreamHandler`
    rcfile["logging"]["handlers"]["default"]["class"] = "logging.StreamHandler"
    pe.PROJECT_CONFIG_FILE.write_text(
        pyaud.config.toml.dumps(rcfile), pe.ENCODING
    )
    pyaud.config.load_config()
    pyaud.config.configure_logging()
    logger = logging.getLogger("default").root
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert getattr(handler, "when", None) is None
    assert getattr(handler, "backupCount", None) is None


def test_default_key() -> None:
    """Test setting and restoring of existing dict keys."""
    obj = {"default_key": "default_value"}
    with pyaud.config.TempEnvVar(  # pylint: disable=protected-access
        obj, default_key="temp_value"
    ):
        assert obj["default_key"] == "temp_value"

    assert obj["default_key"] == "default_value"


def test_plugin_mro() -> None:
    """Assert that plugins can inherit other plugins.

    Prior to this commit ``PluginType``s were only permitted, and not
    children of ``PluginType``s.
    """

    @pyaud.plugins.register(name="plugin_1")
    class PluginOne(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name="plugin_2")
    class PluginTwo(PluginOne):
        """Nothing to do."""

    assert "plugin_1" in pyaud.plugins.mapping()
    assert "plugin_2" in pyaud.plugins.mapping()


def test_get_plugin_logger() -> None:
    """Test logger available through uninstantiated ``BasePlugin``."""
    logger = pyaud.plugins.Plugin.logger()
    assert logger.name == pyaud.plugins.Plugin.__name__


def test_print_version(
    monkeypatch: pytest.MonkeyPatch, main: t.Any, nocolorcapsys: NoColorCapsys
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


def test_no_request(main: t.Any, nocolorcapsys: NoColorCapsys) -> None:
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
    monkeypatch.setattr("pyaud.git.rev_parse", lambda *_, **__: returncode)
    monkeypatch.setattr("pyaud.git.stdout", lambda: stdout)
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
    monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / REPO))
    assert pyaud._utils.working_tree_clean()
    Path(Path.cwd() / FILES).touch()
    assert not pyaud._utils.working_tree_clean()


def test_time_output(main: t.Any, nocolorcapsys: t.Any) -> None:
    """Test tracking of durations in output.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name="plugin")
    class Plugin(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    main("plugin", "-t")
    out = nocolorcapsys.stdout()
    assert "Plugin: Execution time:" in out


# noinspection PyUnresolvedReferences
def test_restore_data_no_json() -> None:
    """Test pass on restoring empty file.

    No need to run any assertions; checking that no error is raised.
    """
    pe.DURATIONS_FILE.touch()
    time_cache = pyaud._data.Record()
    pyaud._data.read(time_cache, pe.DURATIONS_FILE)

    # short-cut for testing ``JSONIO.read`` which is basically identical
    # to ``pyaud._data.read``
    time_cache.path = pe.DURATIONS_FILE  # type: ignore
    pyaud._objects.JSONIO.read(time_cache)  # type: ignore


def test_plugin_deepcopy_with_new() -> None:
    """Test that ``TypeError`` is not raised.

    No assertions run; test passes if the following is not raised:
    TypeError: __new__() missing 1 required positional argument: 'name'
    """
    copy.deepcopy(pyaud.plugins._plugins)
    assert isinstance(
        pyaud.plugins.Plugin(REPO).__deepcopy__(REPO), pyaud.plugins.Plugin
    )


def test_nested_times(monkeypatch: pytest.MonkeyPatch, main: t.Any) -> None:
    """Test reading and writing of times within nested processes.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """
    # noinspection PyUnresolvedReferences
    monkeypatch.setattr("pyaud._data._TimeKeeper._starter", lambda x: 0)
    monkeypatch.setattr("pyaud._data._TimeKeeper._stopper", lambda x: 1)
    expected = {
        "repo": {
            "<class 'pyaud._default.Audit'>": [1],
            "<class 'tests._test.test_nested_times.<locals>.P1'>": [1],
            "<class 'tests._test.test_nested_times.<locals>.P2'>": [1],
        }
    }
    default_config = pyaud.config.DEFAULT_CONFIG
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(default_config)
    test_default["audit"]["modules"] = ["plugin_1", "plugin_2"]
    pe.GLOBAL_CONFIG_FILE.write_text(
        pyaud.config.toml.dumps(test_default), pe.ENCODING
    )

    pyaud.plugins.register("audit")(pyaud._default._Audit)

    class P1(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    class P2(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    pyaud.plugins.register(name="plugin_1")(P1)
    pyaud.plugins.register(name="plugin_2")(P2)

    # noinspection PyUnresolvedReferences
    pyaud._data.record.clear()
    assert sorted(pyaud.plugins.registered()) == [
        "audit",
        "plugin_1",
        "plugin_2",
    ]
    main("audit")
    actual = json.loads(pe.DURATIONS_FILE.read_text(encoding=pe.ENCODING))
    assert all(i in actual for i in expected)


def test_del_key_config_runtime(main: t.Any) -> None:
    """Test a key can be removed and will be replaced if essential.

    :param main: Patch package entry point.
    """
    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name="plugin")
    class Plugin(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    # check config file for essential key
    pyaud.config.toml.loads(pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING))

    assert "filename" in pyaud.config.toml["logging"]["handlers"]["default"]

    del pyaud.config.toml["logging"]["handlers"]["default"]["filename"]

    pe.GLOBAL_CONFIG_FILE.write_text(pyaud.config.toml.dumps(), pe.ENCODING)

    # check config file to confirm essential key was removed
    pyaud.config.toml.loads(pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING))

    assert (
        "filename" not in pyaud.config.toml["logging"]["handlers"]["default"]
    )

    pe.GLOBAL_CONFIG_FILE.write_text(pyaud.config.toml.dumps(), pe.ENCODING)

    pyaud.config.configure_global()
    main("plugin")

    # confirm after running main that no crash occurred and that the
    # essential key was replaced with a default
    pyaud.config.toml.loads(pe.GLOBAL_CONFIG_FILE.read_text(pe.ENCODING))

    assert "filename" in pyaud.config.toml["logging"]["handlers"]["default"]


@pytest.mark.parametrize("temp,expected", [(True, False), (False, True)])
def test_call_m2r_on_markdown(
    monkeypatch: pytest.MonkeyPatch, temp: bool, expected: bool
) -> None:
    """Test creation of an RST README when only markdown is present.

    :param monkeypatch: Mock patch environment and attributes.
    :param temp: Is the RST file temporary? True or False.
    :param expected: Expected value of ``Path(...).is_file``.
    """

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name="plugin")
    class Plugin(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    old_path = Path.cwd() / "README.md"
    new_path = Path.cwd() / "README.rst"
    old_path.touch()
    tracker = Tracker()
    tracker.return_values.append("rst text")
    monkeypatch.setattr("pyaud.parsers._m2r.parse_from_file", tracker)
    with pyaud.parsers.Md2Rst(old_path, temp=temp):
        # do stuff here
        pass

    assert tracker
    assert new_path.is_file() == expected


def test_command_not_found_error() -> None:
    """Test ``CommandNotFoundError`` warning with ``Subprocess``."""
    # noinspection PyUnusedLocal
    @pyaud.plugins.register("test-command-not-found-error")
    class Plugin(pyaud.plugins.Action):
        """Test ``CommandNotFoundError``."""

        not_a_command = "not_a_command"

        @property
        def exe(self) -> t.List[str]:
            """Non-existing command."""
            return [self.not_a_command]

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            self.subprocess[self.not_a_command].call(*args, **kwargs)

    exe = pyaud.plugins.get("test-command-not-found-error")
    with pytest.warns(
        RuntimeWarning, match="not_a_command: Command not found"
    ):
        exe()


def test_warn_no_fix(monkeypatch: pytest.MonkeyPatch, main: t.Any) -> None:
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

    pyaud.plugins.register(name="lint")(_Lint)
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    pyaud.files.append(Path.cwd() / FILES)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    with pytest.raises(pyaud.exceptions.AuditError):
        main("lint")


@pytest.mark.usefixtures("register_plugin")
def test_check_command_no_files_found(
    main: t.Any, nocolorcapsys: NoColorCapsys
) -> None:
    """Test plugin output when no files are found.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    # noinspection PyUnresolvedReferences
    main("plugin")
    assert nocolorcapsys.stdout().strip() == "No files found"


@pytest.mark.usefixtures("register_plugin")
def test_check_command_fail_on_suppress(
    main: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    make_tree: t.Any,
) -> None:
    """Test plugin output when process fails while crash suppressed.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param make_tree: Create directory tree from dict mapping.
    """
    make_tree(Path.cwd(), {FILES: None, "docs": {CONFPY: None}})
    pyaud.files.append(Path.cwd() / FILES)
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main("plugin", "--suppress")
    assert "Failed: returned non-zero exit status" in nocolorcapsys.stderr()


def test_audit_error_did_no_pass_all_checks(
    main: t.Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test raising of ``AuditError``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    """
    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name="plugin")
    class Plugin(pyaud.plugins.Action):  # pylint: disable=unused-variable
        """Nothing to do."""

        not_used = "not-used"

        @property
        def exe(self) -> t.List[str]:
            return [self.not_used]

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            raise subprocess.CalledProcessError(
                1, "returned non-zero exit status"
            )

    pyaud.files.append(Path.cwd() / FILES)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    with pytest.raises(pyaud.exceptions.AuditError):
        main("plugin")


def test_readme_replace() -> None:
    """Test that ``LineSwitch`` properly edits a file."""
    path = Path.cwd() / README

    def _test_file_index(title: str, underline: str) -> None:
        lines = path.read_text(pe.ENCODING).splitlines()
        assert lines[0] == title
        assert lines[1] == len(underline) * "="

    repo = "repo"
    readme = "README"
    repo_underline = len(repo) * "="
    readme_underline = len(readme) * "="
    path.write_text(f"{repo}\n{repo_underline}\n", pe.ENCODING)
    _test_file_index(repo, repo_underline)
    with pyaud.parsers.LineSwitch(path, {0: readme, 1: readme_underline}):
        _test_file_index(readme, readme_underline)

    _test_file_index(repo, repo_underline)


def test_no_exe_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default value for exe property.

    :param monkeypatch: Mock patch environment and attributes.
    """
    unique = datetime.datetime.now().strftime("%d%m%YT%H%M%S")
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    pyaud.files.append(Path.cwd() / FILES)

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name=unique)
    class Plugin(pyaud.plugins.Audit):
        """Nothing to do."""

        def audit(self, *args: t.Any, **kwargs: bool) -> int:
            """Nothing to do."""

    assert pyaud.plugins.get(unique).exe == []


@pytest.mark.usefixtures("unpatch_register_default_plugins")
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
    ids=["no-exclude", "exclude"],
)
def test_clean_exclude(
    main: t.Any,
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
    pyaud.git.init(devnull=True)  # type: ignore
    pyaud.git.add(".")  # type: ignore
    pyaud.git.commit("-m", "Initial commit", devnull=True)  # type: ignore
    for exclusion in exclude:
        Path(Path.cwd() / exclusion).touch()

    main("clean")
    assert nocolorcapsys.stdout() == expected


def test_make_generate_rcfile(nocolorcapsys: NoColorCapsys) -> None:
    """Test for correct output when running ``generate-rcfile``.

    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    # noinspection PyUnresolvedReferences
    pyaud.register_default_plugins()  # type: ignore
    pyaud.plugins.get("generate-rcfile")()
    assert (
        nocolorcapsys.stdout().strip()
        == pyaud.config.toml.dumps(pyaud.config.DEFAULT_CONFIG).strip()
    )


@pytest.mark.parametrize(
    "args,add,first",
    [([], [], ""), (["--clean"], ["clean"], "pyaud clean")],
    ids=["no-args", "clean"],
)
def test_audit_modules(
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    main: t.Any,
    call_status: t.Any,
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
    seq = list(pyaud.config.DEFAULT_CONFIG["audit"]["modules"])
    seq.extend(add)
    mapping = {i: call_status(i) for i in seq}
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mapping)
    monkeypatch.setattr("pyaud._main._register_default_plugins", lambda: None)
    pyaud.plugins._plugins["audit"] = pyaud._default._Audit(  # type: ignore
        "audit"
    )
    main("audit", *args)
    del mapping["audit"]
    assert first in nocolorcapsys.stdout()


def test_environ_repo() -> None:
    """Test returning of repo name with env."""
    assert pe.REPO == Path.cwd().name


@pytest.mark.usefixtures("unpatch_register_default_plugins")
@pytest.mark.parametrize(
    "arg,expected",
    [
        ("", pyaud.plugins.registered()),
        ("audit", ["audit -- Read from [audit] key in config"]),
        ("all", pyaud.plugins.registered()),
    ],
    ids=["no-pos", "module", "all-modules"],
)
def test_help_with_plugins(
    main: t.Any,
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
        main("modules", arg)

    out = nocolorcapsys.stdout()
    assert all(i in out for i in expected)


@pytest.mark.usefixtures("register_plugin", "unpatch_register_default_plugins")
def test_suppress(
    main: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    make_tree: t.Any,
) -> None:
    """Test that audit proceeds through errors with ``--suppress``.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree: Create directory tree from dict mapping.
    """
    default_config = pyaud.config.DEFAULT_CONFIG
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(default_config)
    test_default["audit"]["modules"] = ["plugin"]
    pe.GLOBAL_CONFIG_FILE.write_text(
        pyaud.config.toml.dumps(test_default), pe.ENCODING
    )
    make_tree(Path.cwd(), {FILES: None, "docs": {CONFPY: None}})
    pyaud.files.append(Path.cwd() / FILES)
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main("audit", "--suppress")
    assert "Failed: returned non-zero exit status" in nocolorcapsys.stderr()


# noinspection PyUnusedLocal
def test_parametrize(main: t.Any, nocolorcapsys: NoColorCapsys) -> None:
    """Test class for running multiple plugins.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """

    class PluginOne(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    class PluginTwo(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    class _Params(  # pylint: disable=too-few-public-methods
        pyaud.plugins.Parametrize
    ):
        def plugins(self) -> t.List[str]:
            """List of plugin names to run.

            :return: List of plugin names, as defined in ``@register``.
            """
            return ["plugin_1", "plugin_2"]

    pyaud.plugins.register(name="plugin_1")(PluginOne)
    pyaud.plugins.register(name="plugin_2")(PluginTwo)
    pyaud.plugins.register(name="params")(_Params)
    main("params")
    out = nocolorcapsys.stdout()
    assert "pyaud plugin_1" in out
    assert "pyaud plugin_2" in out


# noinspection PyUnusedLocal
def test_fix_on_pass(main: t.Any) -> None:
    """Test plugin on pass when using the fix class."""
    pyaud.files.append(Path.cwd() / FILES)

    class _Fixer(pyaud.plugins.FixAll):
        def audit(self, *args: t.Any, **kwargs: bool) -> int:
            raise CalledProcessError(1, "cmd")

        def fix(self, *args: t.Any, **kwargs: bool) -> int:
            """Nothing to do."""

    pyaud.plugins.register(name="fixer")(_Fixer)
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main("fixer")

    assert "pyaud fixer did not pass all checks" in str(err.value)


# noinspection PyUnusedLocal
def test_fix_on_fail(main: t.Any, nocolorcapsys: NoColorCapsys) -> None:
    """Test plugin on fail when using the fix class.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    pyaud.files.append(Path.cwd() / FILES)

    class _Fixer(pyaud.plugins.FixAll):
        def audit(self, *args: t.Any, **kwargs: bool) -> int:
            return 0

        def fix(self, *args: t.Any, **kwargs: bool) -> int:
            """Nothing to do."""

    pyaud.plugins.register(name="fixer")(_Fixer)
    main("fixer")
    out = nocolorcapsys.stdout()
    assert "Success: no issues found in 1 source files" in out


@pytest.mark.usefixtures("unpatch_plugins_load")
def test_imports(monkeypatch: pytest.MonkeyPatch, make_tree: t.Any) -> None:
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
    make_tree(Path.cwd(), {"plugins": {INIT: None, FILES: None}})
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
        ("Tests", "tests"),
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
