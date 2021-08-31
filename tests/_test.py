"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments,cell-var-from-loop
# pylint: disable=too-few-public-methods,unused-variable
import copy
import datetime
import logging
import logging.config as logging_config
import os
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Tuple

import dotenv
import pytest

import pyaud

from . import (
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
    with open(path) as fin:
        assert (
            fin.read().strip()
            == "Reinitialized existing Git repository in {}{}".format(
                Path.cwd() / ".git", os.sep
            )
        )


def test_find_package(monkeypatch: Any) -> None:
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
        ("whitelist.py", "whitelist.py", False),
    ],
    ids=["file", "nested", "exclude"],
)
def test_get_files(
    make_relative_file: str, assert_relative_item: str, assert_true: bool
) -> None:
    """Test ``get_files``.

    Test for standard files, nested directories (only return the
    directory root) or files that are excluded.

    :param make_relative_file:      Relative path to Python file.
    :param assert_relative_item:    Relative path to Python item to
                                    check for.
    :param assert_true:             Assert True or assert False.
    """
    project_dir = Path.cwd()
    make_file = project_dir / make_relative_file
    make_item = project_dir / assert_relative_item
    make_file.parent.mkdir(exist_ok=True, parents=True)
    make_file.touch()
    pyaud.git.add(".")  # type: ignore
    pyaud.files.populate()
    if assert_true:
        assert make_item in pyaud.files.reduce()
    else:
        assert make_item not in pyaud.files.reduce()


def test_files_exclude_venv(make_tree: Any) -> None:
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
    with open(project_dir / GITIGNORE, "w") as fout:
        fout.write("venv\n")

    pyaud.files.clear()
    pyaud.files.populate()
    assert set(pyaud.files.reduce()) == set()


def test_arg_order_clone(
    tmp_path: Path, nocolorcapsys: Any, patch_sp_print_called: Any
) -> None:
    """Test that the clone destination is always the last argument.

    :param tmp_path:                Create and return a temporary
                                    directory for testing.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
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
    monkeypatch: Any, main: Any, default: str, flag: str
) -> None:
    """Test the right loglevel is set when parsing the commandline.

    :param monkeypatch: Mock patch environment and attributes.
    :param main:        Patch package entry point.
    :param default:     Default loglevel configuration.
    :param flag:        Verbosity level commandline flag.
    """
    levels = {
        "": [CRITICAL, ERROR, WARNING, INFO, DEBUG],
        "-v": [ERROR, WARNING, INFO, DEBUG, DEBUG],
        "-vv": [WARNING, INFO, DEBUG, DEBUG, DEBUG],
        "-vvv": [INFO, DEBUG, DEBUG, DEBUG, DEBUG],
        "-vvvv": [DEBUG, DEBUG, DEBUG, DEBUG, DEBUG],
    }
    pyaud.config.toml["logging"]["root"]["level"] = default
    with open(pyaud.config.CONFIGDIR / TOMLFILE, "w") as fout:
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
    with pyaud._environ.TempEnvVar(  # pylint: disable=protected-access
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
    monkeypatch: Any,
    main: Any,
    nocolorcapsys: Any,
    arg: str,
    index: int,
    expected: Tuple[str, ...],
) -> None:
    """Test expected output for help with no default plugins.

    Test no positional argument for json array of plugins.
    Test ``audit`` positional argument and docstring display for
    assortment of plugins.
    Test all and display of all module docstrings for assortment of
    test plugins.

    :param monkeypatch:     Mock patch environment and attributes.
    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param arg:             Positional argument for ```pyaud modules``.
    :param index:           Index 0 returns stdout from ``readouterr``
                            and 1 returns stderr.
    :param expected:        Expected result when calling command.
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
def test_gen_default_remote(monkeypatch: Any) -> None:
    """Test ``PYAUD_GH_REMOTE`` is properly loaded from .env variables.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.delenv("PYAUD_GH_REMOTE")
    with open(dotenv.find_dotenv(), "w") as fout:
        fout.write(f"PYAUD_GH_NAME={GH_NAME}\n")
        fout.write(f"PYAUD_GH_EMAIL={GH_EMAIL}\n")
        fout.write(f"PYAUD_GH_TOKEN={GH_TOKEN}\n")

    # noinspection PyProtectedMember
    pyaud._environ.load_namespace()  # pylint: disable=protected-access
    assert (
        os.environ["PYAUD_GH_REMOTE"]
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
    test_default: Dict[Any, Any] = copy.deepcopy(pyaud.config.DEFAULT_CONFIG)
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
    with open(Path.home() / RCFILE, "w") as fout:
        pyaud.config.toml.dump(fout, home_rcfile)

    # reset the dict to the test default
    # ==================================
    # test the the changes made to clean are inherited through the
    # config hierarchy but not configured in this dict
    project_rcfile = dict(test_default)
    project_rcfile["logging"]["version"] = 3
    with open(project_rc, "w") as fout:
        pyaud.config.toml.dump(fout, project_rcfile)

    # load "$HOME/.pyaudrc" and then "$PROJECT_DIR/.pyaudrc"
    # ======================================================
    # override "$HOME/.pyaudrc"
    pyaud.config.load_config()
    subtotal: Dict[str, Any] = dict(home_rcfile)
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
    with open(pyproject_path, "w") as fout:
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
    with open(opt_rc, "w") as fout:
        pyaud.config.toml.dump(fout, pos)

    # load "$HOME/.pyaudrc" and then "$Path.cwd()/.pyaudrc"
    # ======================================================
    # override "$HOME/.pyaudrc"
    pyaud.config.load_config(opt_rc)
    subtotal["audit"] = {"modules": ["files", "format", "format-docs"]}
    assert dict(pyaud.config.toml) == subtotal


def test_toml_no_override_all(monkeypatch: Any) -> None:
    """Confirm error not raised for entire key being overridden.

     Test for when implementing hierarchical config loading.

        def configure(self):
            '''Do the configuration.'''

            config = self.config
            if 'version' not in config:
    >           raise ValueError("dictionary doesn't specify a version")
    E           ValueError: dictionary doesn't specify a version

    :param monkeypatch:     Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud.config.DEFAULT_CONFIG",
        copy.deepcopy(pyaud.config.DEFAULT_CONFIG),
    )
    pyaud.config.toml.clear()
    pyaud.config.load_config()  # base key-values
    with open(pyaud.config.CONFIGDIR / TOMLFILE) as fin:
        pyaud.config.toml.load(fin)  # base key-values

    assert dict(pyaud.config.toml) == pyaud.config.DEFAULT_CONFIG
    with open(Path.home() / RCFILE, "w") as fout:
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
    # so on it's own is an assertion
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

        with open(configfile, "w") as _fout:
            _fout.write("\n".join(_lines))

    # initialisation
    # ==============
    # originally there is no backup file (not until configure_global is
    # run)
    default_config = dict(pyaud.config.toml)
    assert not backupfile.is_file()

    # assert corrupt configfile with no backup will simply reset
    with open(configfile) as fin:
        configfile_contents = fin.read()

    _corrupt_file(configfile_contents)
    pyaud.config.configure_global()
    with open(configfile) as fin:
        pyaud.config.toml.load(fin)

    # assert corrupt configfile is no same as default
    assert dict(pyaud.config.toml) == default_config

    # create backupfile
    pyaud.config.configure_global()
    assert backupfile.is_file()

    # ensure backupfile is a copy of the original config file
    # (overridden at every initialisation in the case of a change)
    with open(configfile) as cfin, open(backupfile) as bfin:
        configfile_contents = cfin.read()
        backupfile_contents = bfin.read()

    assert configfile_contents == backupfile_contents

    # change to config
    # ================
    # this setting, by default, is True
    pyaud.config.toml["logging"]["disable_existing_loggers"] = False
    with open(configfile, "w") as fout:
        pyaud.config.toml.dump(fout)

    # now that there is a change the backup should be different to the
    # original until configure_global is run again
    # read configfile as only that file has been changed
    with open(configfile) as fin:
        configfile_contents = fin.read()

    assert configfile_contents != backupfile_contents
    pyaud.config.configure_global()

    # read both, as both have been changed
    with open(configfile) as cfin, open(backupfile) as bfin:
        configfile_contents = cfin.read()
        backupfile_contents = bfin.read()

    assert configfile_contents == backupfile_contents

    # resolve corrupt file
    # ====================
    _corrupt_file(configfile_contents)

    # read configfile as only that file has been changed
    with open(configfile) as fin:
        configfile_contents = fin.read()

    # only configfile is corrupt, so check backup is not the same
    assert configfile_contents != backupfile_contents

    # resolve corruption
    # ==================
    pyaud.config.configure_global()
    with open(configfile) as cfin, open(backupfile) as bfin:
        configfile_contents = cfin.read()
        backupfile_contents = bfin.read()

    # configfile should equal the backup file and all changes should be
    # retained
    assert configfile_contents == backupfile_contents
    with open(configfile) as fin:
        pyaud.config.toml.load(fin)

    assert pyaud.config.toml["logging"]["disable_existing_loggers"] is False


def test_register_plugin_name_conflict_error() -> None:
    """Test ``NameConflictError`` is raised when same name provided."""
    unique = "test-register-plugin-name-conflict-error"

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name=unique)
    class PluginOne(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: Any, **kwargs: bool) -> Any:
            """Nothing to do."""

    with pytest.raises(pyaud.exceptions.NameConflictError) as err:

        # noinspection PyUnusedLocal
        @pyaud.plugins.register(name=unique)
        class PluginTwo(pyaud.plugins.Action):
            """Nothing to do."""

            def action(self, *args: Any, **kwargs: bool) -> Any:
                """Nothing to do."""

    assert str(err.value) == f"plugin name conflict at PluginTwo: '{unique}'"


def test_register_invalid_type() -> None:
    """Test correct error is displayed when registering unknown type."""
    unique = "test-register-invalid-type"
    with pytest.raises(TypeError) as err:

        # noinspection PyUnusedLocal
        @pyaud.plugins.register(name=unique)
        class NotSubclassed:
            """Nothing to do."""

    assert TYPE_ERROR in str(err.value)


def test_plugin_assign_non_type_value() -> None:
    """Test assigning of incompatible type to `_Plugin` instance."""
    unique = "test-plugin-assign-non-type-value"
    with pytest.raises(TypeError) as err:

        # noinspection PyUnusedLocal
        @pyaud.plugins.register(name=unique)
        def plugin():
            """Nothing to do."""

    assert TYPE_ERROR in str(err.value)


def test_plugin_assign_non_type_key() -> None:
    """Test assigning of incompatible type to `_Plugin` instance."""
    unique = "test-plugin-assign-non-type-key"

    class Parent:
        """Nothing to do."""

    with pytest.raises(TypeError) as err:

        # noinspection PyUnusedLocal
        @pyaud.plugins.register(name=unique)
        class Plugin(Parent):
            """Nothing to do."""

            def __call__(self, *args: Any, **kwargs: bool) -> Any:
                """Nothing to do."""

    assert TYPE_ERROR in str(err.value)


def test_args_reduce(make_tree: Any) -> None:
    """Demonstrate why the ``reduce`` argument should be deprecated.

    No longer considered depreciated.

    :param make_tree: Create directory tree from dict mapping.
    """
    # ignore the bundle dir, including containing python files
    with open(Path.cwd() / GITIGNORE, "w") as fout:
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

    # therefore the ``reduce`` argument should be used sparingly as in
    # this example the bundle dir will not be scanned
    assert all(
        i in normal
        for i in (
            str(Path.cwd() / "src" / "__init__.py"),
            str(Path.cwd() / "dotfiles" / "ipython_config.py"),
        )
    )


def test_files_populate_proc(make_tree: Any) -> None:
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
    with open(Path.cwd() / GITIGNORE, "w") as fout:
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


def test_not_a_repository_error(monkeypatch: Any, tmp_path: Path) -> None:
    """Test error when Git command run in non-repository project.

    :param tmp_path:    Create and return a temporary directory for
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


def test_command_not_found_error() -> None:
    """Test ``CommandNotFoundError`` with ``Subprocess``."""
    not_a_command = "not-a-command"
    with pytest.raises(pyaud.exceptions.CommandNotFoundError) as err:

        # noinspection PyUnusedLocal
        @pyaud.plugins.register("test-command-not-found-error")
        class Plugin(pyaud.plugins.Action):
            """Test ``CommandNotFoundError``."""

            @property
            def exe(self) -> List[str]:
                """Non-existing command."""
                return ["not-a-command"]

            def action(self, *args: Any, **kwargs: bool) -> Any:
                """Nothing to do."""

    assert str(err.value) == f"{not_a_command}: command not found..."


def test_get_packages(monkeypatch: Any, make_tree: Any) -> None:
    """Test process when searching for project's package.

    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree:   Create directory tree from dict mapping.
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


def test_get_subpackages(monkeypatch: Any, make_tree: Any) -> None:
    """Test process when searching for project's package.

    Assert that subdirectories are not returned with import syntax, i.e.
    dot separated, and that only the parent package names are returned.

    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree:   Create directory tree from dict mapping.
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


def test_type_error_stdout(patch_sp_output: Any) -> None:
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


def test_exclude_loads_at_main(main: Any) -> None:
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
    with open(Path.cwd() / ".pyaudrc", "w") as fout:
        test_project_toml_object.dump(fout)

    assert "project" not in pyaud.config.toml["indexing"]["exclude"]

    main("typecheck")

    assert "project" in pyaud.config.toml["indexing"]["exclude"]
