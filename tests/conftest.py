"""
tests.conftest
==============
"""
# pylint: disable=protected-access,no-member,import-outside-toplevel
from __future__ import annotations

import os
from configparser import ConfigParser
from pathlib import Path

import pytest

import pyaud

# noinspection PyProtectedMember
import pyaud._config as pc

# noinspection PyUnresolvedReferences,PyProtectedMember
from pyaud import _builtins

from . import (
    FILE,
    GH_EMAIL,
    GH_NAME,
    OS_GETCWD,
    REPO,
    UNPATCH_REGISTER_DEFAULT_PLUGINS,
    MakeTreeType,
    MockActionPluginFactoryType,
    MockActionPluginList,
    MockMainType,
    NoColorCapsys,
    git,
)

# noinspection PyProtectedMember,PyUnresolvedReferences
original_hash_mapping_match_file = pyaud._cache.HashMapping.match_file
# noinspection PyUnresolvedReferences,PyProtectedMember
original_hash_mapping_unpatched_save_hash = pyaud._cache.HashMapping.save_hash
original_pyaud_plugin_load = pyaud.plugins.load
original_pyaud_main_register_builtin_plugins = (
    _builtins.register_builtin_plugins
)


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

    #: CONFIG
    default_config = dict(pc.DEFAULT_CONFIG)

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
    monkeypatch.setenv("PYAUD_CACHE", str(tmp_path / ".pyaud_cache"))

    #: ATTRS
    monkeypatch.setattr(OS_GETCWD, lambda: str(repo_abs))
    monkeypatch.setattr("inspect.currentframe", lambda: current_frame)
    monkeypatch.setattr("pyaud._config.DEFAULT_CONFIG", default_config)
    monkeypatch.setattr("pyaud._utils.git.status", lambda *_, **__: True)
    monkeypatch.setattr("pyaud._utils.git.rev_parse", lambda *_, **__: None)
    monkeypatch.setattr(
        "pyaud._cache.HashMapping.match_file", lambda *_: False
    )
    monkeypatch.setattr(
        "pyaud._cache.HashMapping.save_hash", lambda _, __: None
    )
    monkeypatch.setattr("pyaud.plugins._plugins", pyaud.plugins.Plugins())
    monkeypatch.setattr("pyaud.plugins.load", lambda: None)
    monkeypatch.setattr("pyaud._main._register_builtin_plugins", lambda: None)

    #: RESET
    pyaud.files.clear()
    pc.toml.clear()

    #: CREATE
    repo_abs.mkdir()
    git.init(file=os.devnull)
    with open(home / ".gitconfig", "w", encoding="utf-8") as fout:
        config.write(fout)

    #: MAIN - essential setup tasks
    # noinspection PyProtectedMember
    pyaud.files.populate_regex()
    # noinspection PyProtectedMember,PyUnresolvedReferences
    pyaud._main._create_cachedir()
    pc.load_config()


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
        from pyaud._main import main

        monkeypatch.setattr("sys.argv", [pyaud.__name__, *args])
        main()

    return _main


@pytest.fixture(name="make_tree")
def fixture_make_tree() -> MakeTreeType:
    """Recursively create directory tree from dict mapping.

    :return: Function for using this fixture.
    """

    def _make_tree(root: Path, obj: dict[str, object]) -> None:
        for key, value in obj.items():
            fullpath = root / key
            if isinstance(value, dict):
                fullpath.mkdir(exist_ok=True)
                _make_tree(fullpath, value)

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


@pytest.fixture(name="unpatch_hash_mapping_save_hash")
def fixture_unpatch_hash_mapping_save_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unpatch ``pyaud._cache.HashMapping.save_hash``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud._cache.HashMapping.save_hash",
        original_hash_mapping_unpatched_save_hash,
    )


@pytest.fixture(name="unpatch_plugins_load")
def fixture_unpatch_plugins_load(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unpatch ``pyaud.plugins.load``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr("pyaud.plugins.load", original_pyaud_plugin_load)


@pytest.fixture(name=UNPATCH_REGISTER_DEFAULT_PLUGINS)
def fixture_unpatch_register_builtin_plugins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unpatch ``pyaud._main._register_builtin_plugins``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud._main._register_builtin_plugins",
        original_pyaud_main_register_builtin_plugins,
    )


@pytest.fixture(name="bump_index")
def fixture_bump_index() -> None:
    """Add a dummy file to the ``pyaud.files`` index."""
    pyaud.files.append(Path.cwd() / FILE)


@pytest.fixture(name="mock_action_plugin_factory")
def fixture_mock_action_plugin_factory() -> MockActionPluginFactoryType:
    """Returns a list of ``Action`` objects.

    Returns variable number, depending on the quantity of names
        provided.

    :return: List of mock ``Action`` plugin types.
    """

    def _mock_action_plugin_factory(*params) -> MockActionPluginList:
        mock_action_plugins = []
        for param in params:
            _name = param.get("name")

            class MockActionPlugin(pyaud.plugins.Action):
                """Nothing to do."""

                exe_str = param.get("exe") or "exe"
                _action = param.get("action")

                @property
                def exe(self) -> list[str]:
                    return [self.exe_str]

                def action(self, *args: str, **kwargs: bool) -> int:
                    """Nothing to do."""
                    if self._action is not None:
                        return self._action(self, *args, **kwargs)

                    return 0

            MockActionPlugin.__name__ = _name
            mock_action_plugins.append(MockActionPlugin)

        return mock_action_plugins

    return _mock_action_plugin_factory
