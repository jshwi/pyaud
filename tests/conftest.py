"""
tests.conftest
==============
"""
# pylint: disable=too-many-arguments,too-many-locals,too-few-public-methods
# pylint: disable=protected-access,no-member,too-many-statements
import os
import typing as t
from configparser import ConfigParser
from pathlib import Path

import pytest
import setuptools

import pyaud

from . import (
    DEBUG,
    FILES,
    GH_EMAIL,
    GH_NAME,
    REPO,
    MakeTreeType,
    MockCallStatusType,
    MockFuncType,
    MockMainType,
    NoColorCapsys,
)

original_hash_mapping_match_file = pyaud.HashMapping.match_file
original_hash_mapping_unpatched_hash_files = pyaud.HashMapping.hash_files
original_pyaud_plugin_load = pyaud.plugins.load
original_pyaud_main_register_default_plugins = pyaud.register_default_plugins
original_setuptools_find_packages = setuptools.find_packages


@pytest.fixture(name="mock_environment", autouse=True)
def fixture_mock_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mock imports to reflect the temporary testing environment.

    :param tmp_path: Create and return temporary directory.
    :param monkeypatch: Mock patch environment and attributes.
    """
    home = tmp_path
    repo_abs = home / REPO
    name = pyaud.__name__

    #: CONFIG
    default_config = dict(pyaud.config.DEFAULT_CONFIG)
    logfile = Path(home / ".cache" / name / "log" / f"{name}.log")
    default_config["logging"]["handlers"]["default"]["filename"] = str(logfile)
    default_config["logging"]["root"]["level"] = DEBUG

    #: DOTENV - prevents lookup of .env file
    current_frame = type("current_frame", (), {})
    current_frame.f_back = type("f_back", (), {})  # type: ignore
    current_frame.f_back.f_code = type("f_code", (), {})  # type: ignore
    current_frame.f_back.f_code.co_filename = str(  # type: ignore
        tmp_path / "_main.py"
    )

    #: GIT CONFIG - prevents git warnings
    config = ConfigParser(default_section="")
    config.read_dict(
        {
            "user": {"name": GH_NAME, "email": GH_EMAIL},
            "advice": {"detachedHead": "false"},
            "init": {"defaultBranch": "master"},
        }
    )

    #: ENV
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODECOV_TOKEN", "")
    monkeypatch.delenv("CODECOV_TOKEN")
    monkeypatch.setenv("PYAUD_GH_REMOTE", str(home / "origin.git"))
    monkeypatch.setenv("PYAUD_DATADIR", str(home / ".local" / "share" / name))
    monkeypatch.setenv("PYAUD_CACHEDIR", str(home / ".cache" / name))
    monkeypatch.setenv("PYAUD_TIMED", "0")
    monkeypatch.setenv("PYAUD_FIX", "0")

    #: ATTRS
    monkeypatch.setattr("os.getcwd", lambda: str(repo_abs))
    monkeypatch.setattr("setuptools.find_packages", lambda *_, **__: [REPO])
    monkeypatch.setattr("inspect.currentframe", lambda: current_frame)
    monkeypatch.setattr("pyaud.config.CONFIGDIR", home / ".config" / name)
    monkeypatch.setattr("pyaud.config.DEFAULT_CONFIG", default_config)
    monkeypatch.setattr("pyaud.git.status", lambda *_, **__: True)
    monkeypatch.setattr("pyaud.git.rev_parse", lambda *_, **__: None)
    monkeypatch.setattr(
        "pyaud._cache.HashMapping.match_file", lambda *_: False
    )
    monkeypatch.setattr("pyaud._cache.HashMapping.hash_files", lambda _: None)
    monkeypatch.setattr("pyaud.plugins._plugins", pyaud.plugins.Plugins())
    monkeypatch.setattr("pyaud.plugins.load", lambda: None)
    monkeypatch.setattr("pyaud._main._register_default_plugins", lambda: None)

    #: RESET
    pyaud.files.clear()
    pyaud.config.toml.clear()

    #: CREATE
    repo_abs.mkdir()
    pyaud.git.init(file=os.devnull)
    with open(home / ".gitconfig", "w", encoding="utf-8") as fout:
        config.write(fout)

    #: MAIN - essential setup tasks
    pyaud.initialize_dirs()
    pyaud.files.populate()
    pyaud.config.configure_global()
    pyaud.config.load_config()
    pyaud.config.configure_logging()


@pytest.fixture(name="nocolorcapsys")
def fixture_nocolorcapsys(capsys: pytest.CaptureFixture) -> NoColorCapsys:
    """Instantiate capsys with the regex method.

    :param capsys: Capture ``sys`` stdout and stderr..
    :return: Instantiated ``NoColorCapsys`` object for capturing output
        stream and sanitizing the string if it contains ANSI escape
        codes.
    """
    return NoColorCapsys(capsys)


@pytest.fixture(name="main")
def fixture_main(monkeypatch: pytest.MonkeyPatch) -> MockMainType:
    """Pass patched commandline arguments to package's main function.

    :param monkeypatch: Mock patch environment and attributes.
    :return: Function for using this fixture.
    """

    def _main(*args: str) -> None:
        """Run main with custom args."""
        # noinspection PyProtectedMember
        # pylint: disable=protected-access,import-outside-toplevel
        from pyaud._main import main

        monkeypatch.setattr("sys.argv", [pyaud.__name__, *args])
        main()

    return _main


@pytest.fixture(name="call_status")
def fixture_call_status() -> MockCallStatusType:
    """Disable all usage of function apart from selected returncode.

    Useful for processes programmed to return a value for the function
    depending on the value of ``__name__``.

    :return: Function for using this fixture.
    """

    def _call_status(module: str, returncode: int = 0) -> MockFuncType:
        def _func(*_: str, **__: bool) -> int:
            return returncode

        _func.__name__ = module
        return _func

    return _call_status


@pytest.fixture(name="make_tree")
def fixture_make_tree() -> MakeTreeType:
    """Recursively create directory tree from dict mapping.

    :return: Function for using this fixture.
    """

    def _make_tree(root: Path, obj: t.Dict[t.Any, t.Any]) -> None:
        for key, value in obj.items():
            fullpath = root / key
            if isinstance(value, dict):
                fullpath.mkdir(exist_ok=True)
                _make_tree(fullpath, value)

            elif isinstance(value, str):
                os.symlink(value, fullpath)
            else:
                fullpath.touch()

    return _make_tree


@pytest.fixture(name="unpatch_hash_mapping_match_file")
def fixture_unpatch_hash_mapping_match_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unpatch ``pyaud._cache.HashMapping.match_file``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud._cache.HashMapping.match_file", original_hash_mapping_match_file
    )


@pytest.fixture(name="unpatch_hash_mapping_hash_files")
def fixture_unpatch_hash_mapping_hash_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unpatch ``pyaud._cache.HashMapping.hash_files``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud._cache.HashMapping.hash_files",
        original_hash_mapping_unpatched_hash_files,
    )


@pytest.fixture(name="unpatch_plugins_load")
def fixture_unpatch_plugins_load(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unpatch ``pyaud.plugins.load``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr("pyaud.plugins.load", original_pyaud_plugin_load)


@pytest.fixture(name="unpatch_register_default_plugins")
def fixture_unpatch_register_default_plugins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unpatch ``pyaud._main._register_default_plugins``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud._main._register_default_plugins",
        original_pyaud_main_register_default_plugins,
    )


@pytest.fixture(name="unpatch_setuptools_find_packages")
def fixture_unpatch_setuptools_find_packages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unpatch ``setuptools_find_packages``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "setuptools.find_packages", original_setuptools_find_packages
    )


@pytest.fixture(name="register_plugin")
def fixture_register_plugin() -> pyaud.plugins.PluginType:
    """Register a plugin.

    :return: Registered plugin object.
    """

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name="plugin")
    class Plugin(pyaud.plugins.Action):  # pylint: disable=unused-variable
        """Nothing to do."""

        command = "some-command-that-does-not-exist"

        @property
        def exe(self) -> t.List[str]:
            return [self.command]

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""
            return self.subprocess[self.command].call(*args, **kwargs)

    # noinspection PyUnresolvedReferences,PyProtectedMember
    Plugin.__call__ = pyaud._wraps.CheckCommand.files(  # type: ignore
        Plugin.__call__
    )
    return Plugin


@pytest.fixture(name="bump_index")
def fixture_bump_index() -> None:
    """Add a dummy file to the ``pyaud.files`` index."""
    pyaud.files.append(Path.cwd() / FILES)
