"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments,cell-var-from-loop
# pylint: disable=too-few-public-methods,unused-variable
import configparser
import copy
import datetime
import logging
import logging.config as logging_config
import os
from pathlib import Path
from typing import Any, Dict, Tuple

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
    INFO,
    INIT,
    INITIAL_COMMIT,
    OS_GETCWD,
    README,
    REAL_REPO,
    REPO,
    WARNING,
)


def test_get_branch_unique(monkeypatch: Any) -> None:
    """Test that ``get_branch`` returns correct branch.

    :param monkeypatch: Mock patch environment and attributes.
    """
    cwd = str(Path.cwd())
    monkeypatch.undo()
    monkeypatch.setattr(OS_GETCWD, lambda: cwd)
    Path(Path.cwd() / README).touch()
    branch = datetime.datetime.now().strftime("%d%m%YT%H%M%S")
    pyaud.utils.git.add(".", devnull=True)  # type: ignore
    pyaud.utils.git.commit("-m", INITIAL_COMMIT, devnull=True)  # type: ignore
    pyaud.utils.git.checkout("-b", branch, devnull=True)  # type: ignore
    assert pyaud.utils.get_branch() == branch


def test_get_branch_initial_commit(monkeypatch: Any) -> None:
    """Test that ``get_branch`` returns None.

    Test when run from a commit with no parent commits i.e. initial
    commit.

    :param monkeypatch: Mock patch environment and attributes.
    """
    cwd = str(Path.cwd())
    monkeypatch.undo()
    monkeypatch.setattr(OS_GETCWD, lambda: cwd)
    Path(Path.cwd() / README).touch()
    pyaud.utils.git.add(".")  # type: ignore
    pyaud.utils.git.commit("-m", INITIAL_COMMIT)  # type: ignore
    pyaud.utils.git.rev_list(  # type: ignore
        "--max-parents=0", "HEAD", capture=True
    )
    pyaud.utils.git.checkout(pyaud.utils.git.stdout()[0])  # type: ignore
    assert pyaud.utils.get_branch() is None


def test_pipe_to_file() -> None:
    """Test that the ``Subprocess`` class correctly writes file.

    When the ``file`` keyword argument is used stdout should be piped to
    the filename provided.
    """
    path = Path.cwd() / FILES
    pyaud.utils.git.init(file=path)  # type: ignore
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
    monkeypatch.setattr("os.getcwd", lambda: cwd)
    monkeypatch.setattr("setuptools.find_packages", lambda *_, **__: [])
    with pytest.raises(EnvironmentError) as err:
        pyaud.environ.find_package()

    assert str(err.value) == "no packages found"


@pytest.mark.parametrize(
    "change,expected",
    [(False, True), (True, False)],
    ids=["no_change", "change"],
)
def test_hash_file(make_tree: Any, change: Any, expected: Any) -> None:
    """Test that ``HashCap`` can properly determine changes.

    :param make_tree:   Create directory tree from dict mapping.
    :param change:      True or False: Change the file.
    :param expected:    Expected result from ``cap.compare``.
    """
    path = Path.cwd() / pyaud.environ.DOCS / f"{REPO}.rst"
    make_tree(Path.cwd(), {"docs": {path.name: None}})
    with pyaud.utils.HashCap(path) as cap:
        if change:
            with open(path, "w") as fin:
                fin.write("changed")

    assert cap.compare == expected


@pytest.mark.parametrize(
    "make_relative_file,assert_relative_item,assert_true",
    [
        (FILES, FILES, True),
        (Path("nested") / "python" / "file" / FILES, "nested", True),
        ("whitelist.py", "whitelist.py", False),
    ],
    ids=["file", "nested", "exclude"],
)
def test_get_pyfiles(
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
    pyaud.utils.git.add(".")  # type: ignore
    pyaud.utils.tree.populate()
    if assert_true:
        assert make_item in pyaud.utils.tree.reduce()
    else:
        assert make_item not in pyaud.utils.tree.reduce()


def test_pyitems_exclude_venv(make_tree: Any) -> None:
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
    with open(project_dir / ".gitignore", "w") as fout:
        fout.write("venv\n")

    pyaud.utils.tree.clear()
    pyaud.utils.tree.populate()
    assert set(pyaud.utils.tree.reduce()) == set()


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
    pyaud.utils.git.clone(  # type: ignore
        "--depth", "1", "--branch", "v1.1.0", REAL_REPO, path
    )
    assert (
        nocolorcapsys.stdout().strip()
        == "<_Git (git)> clone --depth 1 --branch v1.1.0 {} {}".format(
            REAL_REPO, path
        )
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
    with open(pyaud.config.CONFIGDIR / pyaud.config.TOMLFILE, "w") as fout:
        pyaud.config.toml.dump(fout)

    # dummy call to non-existing plugin to evaluate multiple -v
    # arguments
    monkeypatch.setattr(
        "pyaud.main.plugins", {"module": lambda *_, **__: None}
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
    with pyaud.environ.TempEnvVar(obj, key="value"):
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
    monkeypatch.setattr("pyaud.main.plugins", mocked_plugins)
    with pytest.raises(SystemExit):
        main("modules", arg)

    # index 0 returns stdout from ``readouterr`` and 1 returns stderr
    out = nocolorcapsys.readouterr()[index]
    assert any(i in out for i in expected)


def test_seq() -> None:
    """Get coverage on ``Seq`` abstract methods."""
    pyaud.utils.tree.append("key")
    assert pyaud.utils.tree[0] == "key"
    pyaud.utils.tree[0] = "value"
    assert pyaud.utils.tree[0] == "value"
    del pyaud.utils.tree[0]
    assert not pyaud.utils.tree
    assert repr(pyaud.utils.tree) == "<_Tree []>"


def test_temp_env_var_iskey() -> None:
    """Test ``TempEnvVar`` sets environment variable.

    Test existing variable's value is as it originally was once the
    context action is done.
    """
    obj = copy.deepcopy(os.environ)
    assert "BUILDDIR" in obj
    builddir = obj["BUILDDIR"]
    with pyaud.environ.TempEnvVar(obj, BUILDDIR="True"):
        assert "BUILDDIR" in obj and obj["BUILDDIR"] == "True"

    assert "BUILDDIR" in obj and obj["BUILDDIR"] == builddir


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

    pyaud.environ.load_namespace()
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
    """Assert "$HOME/.config/pyaud.utils.toml" is created and loaded.

    Create "$HOME/.pyaudrc" and "$PROJECT_DIR/.pyaudrc" load them,
    ensuring that each level up overrides changes from lower level
    configs whilst, keeping the remaining changes. Create
    "$PROJECT_DIR/pyproject.toml" and test the same, which will override
    all previous configs.
    """
    # base config is created and loaded
    # =================================
    project_dir = Path.cwd()
    project_rc = project_dir / pyaud.config.RCFILE
    pyproject_path = project_dir / pyaud.config.PYPROJECT
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
    with open(Path.home() / pyaud.config.RCFILE, "w") as fout:
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


def test_config_ini_integration() -> None:
    """Test config ini edits override global toml."""
    tomlfile = pyaud.config.CONFIGDIR / pyaud.config.TOMLFILE
    inifile = pyaud.config.CONFIGDIR / f"{pyaud.__name__}.ini"
    config_parser = configparser.ConfigParser()

    # write default test ini file
    # ===========================
    default_ini_config = dict(
        CLEAN={"exclude": "*.egg*,\n  .mypy_cache,\n  .env,\n  instance,"}
    )
    config_parser.read_dict(default_ini_config)
    with open(inifile, "w") as fout:
        config_parser.write(fout)

    # ini ``CLEAN`` matches toml ``clean``
    # ====================================
    pyaud.config.configure_global()
    with open(tomlfile) as fin:
        assert (
            '[clean]\nexclude = ["*.egg*", ".mypy_cache", ".env", "instance"]'
        ) in fin.read()

    # remove toml to write global again
    # =================================
    os.remove(tomlfile)

    # write updated test ini file
    # ===========================
    default_ini_config["CLEAN"] = {
        "exclude": "*.egg*,\n  .env,\n  instance,\n  .coverage"
    }
    config_parser.read_dict(default_ini_config)
    with open(inifile, "w") as fout:
        config_parser.write(fout)

    # ini ``CLEAN`` matches toml ``clean``
    # ====================================
    pyaud.config.configure_global()
    with open(tomlfile) as fin:
        assert (
            '[clean]\nexclude = ["*.egg*", ".env", "instance", ".coverage"]'
        ) in fin.read()


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
    with open(pyaud.config.CONFIGDIR / pyaud.config.TOMLFILE) as fin:
        pyaud.config.toml.load(fin)  # base key-values

    assert dict(pyaud.config.toml) == pyaud.config.DEFAULT_CONFIG
    with open(Path.home() / pyaud.config.RCFILE, "w") as fout:
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
    configfile = pyaud.config.CONFIGDIR / pyaud.config.TOMLFILE
    backupfile = pyaud.config.CONFIGDIR / f".{pyaud.config.TOMLFILE}.bak"

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

    @pyaud.plugins.register(name=unique)
    def plugin_one():  # pylint: disable=unused-variable
        """Nothing to do."""

    with pytest.raises(pyaud.exceptions.NameConflictError) as err:

        @pyaud.plugins.register(name=unique)
        def plugin_two():  # pylint: disable=unused-variable
            """Nothing to do."""

    assert str(err.value) == f"plugin name conflict at plugin_two: '{unique}'"
