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
import time
import typing as t
from pathlib import Path
from subprocess import CalledProcessError

import pytest

import pyaud

from . import (
    COMMIT,
    CRITICAL,
    DEBUG,
    ERROR,
    FILES,
    GH_EMAIL,
    GH_NAME,
    GH_TOKEN,
    GITIGNORE,
    INFO,
    INIT,
    INITIAL_COMMIT,
    OS_GETCWD,
    PYAUD_PLUGINS_PLUGINS,
    PYPROJECT,
    RCFILE,
    README,
    REAL_REPO,
    REPO,
    TOMLFILE,
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
    pyaud.git.add(".", devnull=True)  # type: ignore
    pyaud.git.commit("-m", INITIAL_COMMIT, devnull=True)  # type: ignore
    pyaud.git.checkout("-b", branch, devnull=True)  # type: ignore
    assert pyaud._utils.branch() == branch  # pylint: disable=protected-access


def test_get_branch_initial_commit() -> None:
    """Test that ``get_branch`` returns None.

    Test when run from a commit with no parent commits i.e. initial
    commit.
    """
    Path(Path.cwd() / README).touch()
    pyaud.git.add(".")  # type: ignore
    pyaud.git.commit("-m", INITIAL_COMMIT)  # type: ignore
    pyaud.git.rev_list("--max-parents=0", "HEAD", capture=True)  # type: ignore
    pyaud.git.checkout(pyaud.git.stdout()[0])  # type: ignore
    assert pyaud._utils.branch() is None  # pylint: disable=protected-access


def test_pipe_to_file() -> None:
    """Test that the ``Subprocess`` class correctly writes file.

    When the ``file`` keyword argument is used stdout should be piped to
    the filename provided.
    """
    path = Path.cwd() / FILES
    pyaud.git.init(file=path)  # type: ignore
    with open(path, encoding="utf-8") as fin:
        assert (
            fin.read().strip()
            == "Reinitialized existing Git repository in {}{}".format(
                Path.cwd() / ".git", os.sep
            )
        )


def test_find_package(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test error is raised if no Python file exists in project root.

    :param monkeypatch: Mock patch environment and attributes.
    """
    cwd = os.getcwd()
    monkeypatch.undo()
    monkeypatch.setattr(OS_GETCWD, lambda: cwd)
    monkeypatch.setattr("setuptools.find_packages", lambda *_, **__: [])
    with pytest.raises(EnvironmentError) as err:
        pyaud.package()

    assert str(err.value) == "no packages found"


@pytest.mark.parametrize(
    "make_relative_file,assert_relative_item,assert_true",
    [
        (FILES, FILES, True),
        (Path("nested") / "python" / "file" / FILES, "nested", True),
        (WHITELIST_PY, "whitelist.py", False),
    ],
    ids=["file", "nested", "exclude"],
)
def test_get_files(
    make_relative_file: str, assert_relative_item: str, assert_true: bool
) -> None:
    """Test ``get_files``.

    Test for standard files, nested directories (only return the
    directory root) or files that are excluded.

    :param make_relative_file: Relative path to Python file.
    :param assert_relative_item: Relative path to Python item to check
        for.
    :param assert_true: Assert True or assert False.
    """
    project_dir = Path.cwd()
    make_file = project_dir / make_relative_file
    make_item = project_dir / assert_relative_item
    make_file.parent.mkdir(exist_ok=True, parents=True)
    make_file.touch()
    pyaud.git.add(".")  # type: ignore
    pyaud.files.add_exclusions(WHITELIST_PY)
    pyaud.files.populate()
    if assert_true:
        assert make_item in pyaud.files.reduce()
    else:
        assert make_item not in pyaud.files.reduce()


def test_files_exclude_venv(make_tree: t.Any) -> None:
    """Test that virtualenv dir is excluded.

     Test when indexing with ``PythonItems.items``.

    :param make_tree: Create directory tree from dict mapping.
    """
    project_dir = Path.cwd()
    make_tree(
        project_dir,
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
    with open(project_dir / GITIGNORE, "w", encoding="utf-8") as fout:
        fout.write("venv\n")

    pyaud.files.clear()
    pyaud.files.populate()
    assert set(pyaud.files.reduce()) == set()


def test_arg_order_clone(
    tmp_path: Path, nocolorcapsys: NoColorCapsys, patch_sp_print_called: t.Any
) -> None:
    """Test that the clone destination is always the last argument.

    :param tmp_path: Create and return a temporary directory for
        testing.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    """
    patch_sp_print_called()
    path = tmp_path / REPO
    pyaud.git.clone(  # type: ignore
        "--depth", "1", "--branch", "v1.1.0", REAL_REPO, path
    )
    assert (
        nocolorcapsys.stdout().strip()
        == f"<_Git (git)> clone --depth 1 --branch v1.1.0 {REAL_REPO} {path}"
    )


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
    with open(
        pyaud.config.CONFIGDIR / TOMLFILE, "w", encoding="utf-8"
    ) as fout:
        pyaud.config.toml.dump(fout)

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


@pytest.mark.parametrize(
    "arg,index,expected",
    [
        (
            "",
            0,
            (
                "modules = [\n",
                '    "plugin1",\n',
                '    "plugin2",\n',
                '    "plugin3"\n',
                "]",
            ),
        ),
        (
            "all",
            0,
            (
                "plugin1 -- Docstring for plugin1",
                "plugin2 -- Docstring for plugin2",
                "plugin3 -- Docstring for plugin3",
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

    def plugin1():
        """Docstring for plugin1."""

    def plugin2():
        """Docstring for plugin2."""

    def plugin3():
        """Docstring for plugin3."""

    mocked_plugins = {
        "plugin1": plugin1,
        "plugin2": plugin2,
        "plugin3": plugin3,
    }
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mocked_plugins)
    with pytest.raises(SystemExit):
        main("modules", arg)

    # index 0 returns stdout from ``readouterr`` and 1 returns stderr
    out = nocolorcapsys.readouterr()[index]
    assert any(i in out for i in expected)


def test_seq() -> None:
    """Get coverage on ``Seq`` abstract methods."""
    pyaud.files.append("key")
    assert pyaud.files[0] == "key"
    pyaud.files[0] = "value"
    assert pyaud.files[0] == "value"
    del pyaud.files[0]
    assert not pyaud.files
    assert repr(pyaud.files) == "<_Files []>"


@pytest.mark.usefixtures("init_remote")
def test_gen_default_remote(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test ``PYAUD_GH_REMOTE`` is properly loaded from .env variables.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.delenv("PYAUD_GH_REMOTE")
    with open(Path.cwd() / ".env", "w", encoding="utf-8") as fout:
        fout.write(f"PYAUD_GH_NAME={GH_NAME}\n")
        fout.write(f"PYAUD_GH_EMAIL={GH_EMAIL}\n")
        fout.write(f"PYAUD_GH_TOKEN={GH_TOKEN}\n")

    # noinspection PyProtectedMember
    assert (
        pyaud.environ.GH_REMOTE
        == f"https://{GH_NAME}:{GH_TOKEN}@github.com/{GH_NAME}/{REPO}.git"
    )


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
    project_dir = Path.cwd()
    project_rc = project_dir / RCFILE
    pyproject_path = project_dir / PYPROJECT
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
    with open(Path.home() / RCFILE, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout, home_rcfile)

    # reset the dict to the test default
    # ==================================
    # test the the changes made to clean are inherited through the
    # config hierarchy but not configured in this dict
    project_rcfile = dict(test_default)
    project_rcfile["logging"]["version"] = 3
    with open(project_rc, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout, project_rcfile)

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
    with open(pyproject_path, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout, pyproject_dict)

    # load "$HOME/.pyaudrc" and then "$PROJECT_DIR/.pyaudrc"
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
    with open(opt_rc, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout, pos)

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
    with open(pyaud.config.CONFIGDIR / TOMLFILE, encoding="utf-8") as fin:
        pyaud.config.toml.load(fin)  # base key-values

    assert dict(pyaud.config.toml) == pyaud.config.DEFAULT_CONFIG
    with open(Path.home() / RCFILE, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout, {"logging": {"root": {"level": "INFO"}}})

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
    configfile = pyaud.config.CONFIGDIR / TOMLFILE
    backupfile = pyaud.config.CONFIGDIR / f".{TOMLFILE}.bak"

    def _corrupt_file(_configfile_contents: str) -> None:
        # make a non-parsable change to the configfile (corrupt it)
        _lines = _configfile_contents.splitlines()
        _string = 'format = "%(asctime)s %(levelname)s %(name)s %(message)s"'
        for _count, _line in enumerate(list(_lines)):
            if _line == _string:
                _lines.insert(_count, _string[-6:])

        with open(configfile, "w", encoding="utf-8") as _fout:
            _fout.write("\n".join(_lines))

    # initialisation
    # ==============
    # originally there is no backup file (not until configure_global is
    # run)
    default_config = dict(pyaud.config.toml)
    assert not backupfile.is_file()

    # assert corrupt configfile with no backup will simply reset
    with open(configfile, encoding="utf-8") as fin:
        configfile_contents = fin.read()

    _corrupt_file(configfile_contents)
    pyaud.config.configure_global()
    with open(configfile, encoding="utf-8") as fin:
        pyaud.config.toml.load(fin)

    # assert corrupt configfile is no same as default
    assert dict(pyaud.config.toml) == default_config

    # create backupfile
    pyaud.config.configure_global()
    assert backupfile.is_file()

    # ensure backupfile is a copy of the original config file
    # (overridden at every initialisation in the case of a change)
    with open(configfile, encoding="utf-8") as cfin, open(
        backupfile, encoding="utf-8"
    ) as bfin:
        configfile_contents = cfin.read()
        backupfile_contents = bfin.read()

    assert configfile_contents == backupfile_contents

    # change to config
    # ================
    # this setting, by default, is True
    pyaud.config.toml["logging"]["disable_existing_loggers"] = False
    with open(configfile, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout)

    # now that there is a change the backup should be different to the
    # original until configure_global is run again
    # read configfile as only that file has been changed
    with open(configfile, encoding="utf-8") as fin:
        configfile_contents = fin.read()

    assert configfile_contents != backupfile_contents
    pyaud.config.configure_global()

    # read both, as both have been changed
    with open(configfile, encoding="utf-8") as cfin, open(
        backupfile, encoding="utf-8"
    ) as bfin:
        configfile_contents = cfin.read()
        backupfile_contents = bfin.read()

    assert configfile_contents == backupfile_contents

    # resolve corrupt file
    # ====================
    _corrupt_file(configfile_contents)

    # read configfile as only that file has been changed
    with open(configfile, encoding="utf-8") as fin:
        configfile_contents = fin.read()

    # only configfile is corrupt, so check backup is not the same
    assert configfile_contents != backupfile_contents

    # resolve corruption
    # ==================
    pyaud.config.configure_global()
    with open(configfile, encoding="utf-8") as cfin, open(
        backupfile, encoding="utf-8"
    ) as bfin:
        configfile_contents = cfin.read()
        backupfile_contents = bfin.read()

    # configfile should equal the backup file and all changes should be
    # retained
    assert configfile_contents == backupfile_contents
    with open(configfile, encoding="utf-8") as fin:
        pyaud.config.toml.load(fin)

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

        # noinspection PyUnusedLocal
        @pyaud.plugins.register(name=unique)  # type: ignore
        class NotSubclassed:
            """Nothing to do."""

    assert TYPE_ERROR in str(err.value)


def test_plugin_assign_non_type_value() -> None:
    """Test assigning of incompatible type to `_Plugin` instance."""
    unique = "test-plugin-assign-non-type-value"
    with pytest.raises(TypeError) as err:

        # noinspection PyUnusedLocal
        @pyaud.plugins.register(name=unique)  # type: ignore
        class _NonType:
            """Nothing to do."""

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


def test_args_reduce(make_tree: t.Any) -> None:
    """Demonstrate why the ``reduce`` argument should be deprecated.

    No longer considered depreciated.

    :param make_tree: Create directory tree from dict mapping.
    """
    # ignore the bundle dir, including containing python files
    with open(Path.cwd() / GITIGNORE, "w", encoding="utf-8") as fout:
        fout.write("bundle")

    make_tree(
        Path.cwd(),
        {
            "dotfiles": {
                "vim": {
                    "bundle": {  # this dir should be ignored
                        "ctags": {
                            "Units": {
                                "parse-python.r": {
                                    "python-dot-in-import.d": {
                                        "input.py": None
                                    }
                                }
                            }
                        }
                    }
                },
                "ipython_config.py": None,
            },
            "src": {"__init__.py": None},
        },
    )
    pyaud.git.add(".")  # type: ignore
    pyaud.files.populate()
    normal = pyaud.files.args()
    reduced = pyaud.files.args(reduce=True)

    # if reduce is used, then all of $PROJECT_DIR/dotfiles will be
    # scanned (as $PROJECT_DIR/dotfiles/ipython_config.py is not
    # ignored) therefore the .gitignore rule will not apply to
    # ``bundle``
    assert all(
        i in reduced
        for i in (str(Path.cwd() / "dotfiles"), str(Path.cwd() / "src"))
    )

    # therefore, the ``reduce`` argument should be used sparingly as in
    # this example the bundle dir will not be scanned
    assert all(
        i in normal
        for i in (
            str(Path.cwd() / "src" / "__init__.py"),
            str(Path.cwd() / "dotfiles" / "ipython_config.py"),
        )
    )


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
    with open(Path.cwd() / GITIGNORE, "w", encoding="utf-8") as fout:
        fout.write("venv\n")

    def _old_files_populate():
        indexed = []
        for path in Path.cwd().rglob("*.py"):
            if path.name not in pyaud.config.DEFAULT_CONFIG["indexing"][
                "exclude"
            ] and not pyaud.git.ls_files(  # type: ignore
                "--error-unmatch", path, devnull=True, suppress=True
            ):
                indexed.append(path)

        return indexed

    pyaud.git.add(".")  # type: ignore
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


def test_not_a_repository_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test error when Git command run in non-repository project.

    :param tmp_path: Create and return a temporary directory for
        testing.
    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(OS_GETCWD, lambda: str(tmp_path))
    with pytest.raises(pyaud.exceptions.NotARepositoryError) as err:
        pyaud.git.add(".")  # type: ignore

    assert str(err.value) == "not a git repository"


def test_called_process_error_with_git() -> None:
    """Test regular Git command error."""
    with pytest.raises(CalledProcessError) as err:
        pyaud.git.commit("-m", "Second initial commit")  # type: ignore

    assert str(err.value) == (
        "Command 'git commit -m Second initial commit' returned non-zero exit "
        "status 1."
    )


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
    with pytest.raises(pyaud.exceptions.PythonPackageNotFoundError) as err:
        pyaud.package()

    assert str(err.value) == "cannot determine primary package"

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


def test_type_error_stdout(patch_sp_output: t.Any) -> None:
    """Subtle bug which appeared to be one test, but was another.

    Error was being raised in ``test_make_unused_fix`` as ``replace``
    could not be used on a list.

    The error was the cause of  ``test_make_whitelist`` as a dummy patch
    was used to override output (empty list: unnecessary - removed).

    Would not fail test every run, but with ``pytest-randomly`` it
    appears to have been caused when ``test_make_whitelist`` came
    before ``test_make_unused_fix``.

    Error was not caused by any bug in the program,
    just the monkeypatch.

    Not clear yet how exactly the two tests are related.

    :param patch_sp_output: Patch ``Subprocess`` so that ``call`` sends
        expected stdout out to self.
    """
    with pytest.raises(TypeError) as err:
        patch_sp_output([])
        pyaud.plugins.get("whitelist")()

    assert (
        str(err.value)
        == "stdout received as 'list': only str instances allowed"
    )


def test_exclude_loads_at_main(main: t.Any) -> None:
    """Confirm project config is loaded with ``main``.

    :param main: Patch package entry point.
    """
    default_config = copy.deepcopy(pyaud.config.DEFAULT_CONFIG)
    project_config = copy.deepcopy(default_config)
    project_config["indexing"]["exclude"].append("project")
    test_project_toml_object = (
        pyaud.config._Toml()  # pylint: disable=protected-access
    )
    test_project_toml_object.update(project_config)
    with open(Path.cwd() / ".pyaudrc", "w", encoding="utf-8") as fout:
        test_project_toml_object.dump(fout)

    assert "project" not in pyaud.config.toml["indexing"]["exclude"]

    main("typecheck")

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
    pyaud.git.add(".")  # type: ignore
    pyaud.files.add_exclusions(*exclude)
    pyaud.files.populate()
    assert not any(i in p.parts for i in exclude for p in pyaud.files)
    assert all(Path.cwd() / "repo" / p in pyaud.files for p in webapp)


# noinspection DuplicatedCode
def test_filter_logging_config_kwargs() -> None:
    """Test that no errors are raised for additional config kwargs."""
    project_dir = Path.cwd()
    project_rc = project_dir / RCFILE
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(
        pyaud.config.DEFAULT_CONFIG
    )

    # patch `DEFAULT_CONFIG` for `TimedRotatingFileHandler`
    logfile = str(Path.cwd() / ".cache" / "pyaud" / "log" / "pyaud.log")
    test_default["logging"]["handlers"]["default"]["filename"] = logfile
    rcfile = dict(test_default)
    with open(project_rc, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout, rcfile)

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
    with open(project_rc, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout, rcfile)

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


def test_files_extend_no_dupes() -> None:
    """Test files extend does not index duplicates."""
    files_before = sorted(
        [
            Path.cwd() / "dir" / "file1.py",
            Path.cwd() / "dir" / "file1.py",
            Path.cwd() / "file2.py",
        ]
    )
    files_after = sorted(
        [Path.cwd() / Path("dir", "file1.py"), Path.cwd() / Path("file2.py")]
    )
    pyaud.files.extend(files_before)
    assert sorted(pyaud.files) == files_after


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
    monkeypatch.setattr("pyaud._main.__version__", "1.0.0")
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
    "stdout,returncode,expected", [([COMMIT], 0, COMMIT), ([], 1, None)]
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
    main("format", "-t")
    out = nocolorcapsys.stdout()
    assert "Format: Execution time:" in out


# noinspection PyUnresolvedReferences
def test_restore_data_no_json() -> None:
    """Test pass on restoring empty file.

    No need to run any assertions; checking that no error is raised.
    """
    path = Path(
        Path.cwd()
        / pyaud.environ.DATADIR
        / pyaud._wraps.ClassDecorator.DURATIONS
    )
    path.touch()
    time_cache = pyaud._data.Record()
    pyaud._data.read(time_cache, path)

    # short-cut for testing ``JSONIO.read`` which is basically identical
    # to ``pyaud._data.read``
    time_cache.path = path  # type: ignore
    pyaud._objects.JSONIO.read(time_cache)  # type: ignore


def test_plugin_deepcopy_with_new() -> None:
    """Test that ``TypeError`` is not raised.

    No assertions run; test passes if the following is not raised:
    TypeError: __new__() missing 1 required positional argument: 'name'
    """
    copy.deepcopy(pyaud.plugins._plugins)


# noinspection PyUnusedLocal
def test_nested_times(monkeypatch: pytest.MonkeyPatch, main: t.Any) -> None:
    """Test reading and writing of times within nested processes.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """
    times = [1, 5, 2, 3, 1, 0]
    configfile = pyaud.config.CONFIGDIR / "pyaud.toml"
    # noinspection PyUnresolvedReferences
    datafile = pyaud.environ.DATADIR / "durations.json"
    monkeypatch.setattr("pyaud._wraps._package", lambda: REPO)
    monkeypatch.setattr("pyaud._data._time", times.pop)
    expected = {
        "repo": {
            "<class 'pyaud_plugins.modules.Audit'>": [1],
            "<class 'tests._test.test_nested_times.<locals>.P1'>": [2],
            "<class 'tests._test.test_nested_times.<locals>.P2'>": [3],
        }
    }
    default_config = pyaud.config.DEFAULT_CONFIG
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(default_config)
    test_default["audit"]["modules"] = ["plugin_1", "plugin_2"]
    with open(configfile, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout, test_default)

    @pyaud.plugins.register(name="plugin_1")
    class P1(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    @pyaud.plugins.register(name="plugin_2")
    class P2(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    # noinspection PyUnresolvedReferences
    pyaud._data.record.clear()
    main("audit")
    actual = json.loads(datafile.read_text(encoding="utf-8"))
    assert all(i in actual for i in expected)


def test_del_key_config_runtime(main: t.Any) -> None:
    """Test a key can be removed and will be replaced if essential.

    :param main: Patch package entry point.
    """
    tomlfile = Path.home() / pyaud.config.CONFIGDIR / pyaud.config._TOMLFILE

    # check config file for essential key
    with open(tomlfile, encoding="utf-8") as fin:
        pyaud.config.toml.load(fin)

    assert "filename" in pyaud.config.toml["logging"]["handlers"]["default"]

    del pyaud.config.toml["logging"]["handlers"]["default"]["filename"]

    with open(tomlfile, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout)

    # check config file to confirm essential key was removed
    with open(tomlfile, encoding="utf-8") as fin:
        pyaud.config.toml.load(fin)

    assert (
        "filename" not in pyaud.config.toml["logging"]["handlers"]["default"]
    )

    with open(tomlfile, "w", encoding="utf-8") as fout:
        pyaud.config.toml.dump(fout)

    pyaud.config.configure_global()
    main("format")

    # confirm after running main that no crash occurred and that the
    # essential key was replaced with a default
    with open(tomlfile, encoding="utf-8") as fin:
        pyaud.config.toml.load(fin)

    assert "filename" in pyaud.config.toml["logging"]["handlers"]["default"]


def test_call_m2r_on_markdown(
    monkeypatch: pytest.MonkeyPatch, main: t.Any
) -> None:
    """Test creation of an RST README when only markdown is present.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """
    path = Path.cwd() / "README.md"
    path.touch()
    tracker = Tracker()
    tracker.return_values.append("rst text")
    monkeypatch.setattr("pyaud.parsers._m2r.parse_from_file", tracker)
    main("docs")
    assert tracker.was_called()
    assert Path.cwd() / "README.md" in tracker.args[0]
    assert tracker.kwargs == [{}]


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
