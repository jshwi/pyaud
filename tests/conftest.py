"""
tests.conftest
==============
"""
# pylint: disable=protected-access,no-member,import-outside-toplevel
# pylint: disable=cell-var-from-loop
from __future__ import annotations

import os
import typing as t
from pathlib import Path

import pytest
from mypy_extensions import KwArg, VarArg

import pyaud

# noinspection PyUnresolvedReferences,PyProtectedMember
from pyaud import _builtins

from . import (
    UNPATCH_REGISTER_DEFAULT_PLUGINS,
    FixtureMain,
    FixtureMakeTree,
    FixtureMockActionPluginFactory,
    FixtureMockRepo,
    MockActionPluginList,
    PluginTuple,
    repo,
)

# noinspection PyProtectedMember

original_pyaud_plugin_load = pyaud.plugins.load
original_pyaud_main_register_builtin_plugins = (
    _builtins.register_builtin_plugins
)


@pytest.fixture(name="mock_environment", autouse=True)
def fixture_mock_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_repo: FixtureMockRepo
) -> None:
    """Mock imports to reflect the temporary testing environment.

    :param tmp_path: Create and return temporary directory.
    :param monkeypatch: Mock patch environment and attributes.
    :param mock_repo: Mock ``git.Repo`` class.
    """
    repo_abs = tmp_path / repo[1]
    mock_repo()
    monkeypatch.setenv("PYAUD_CACHE", str(tmp_path / ".pyaud_cache"))
    monkeypatch.setattr("os.getcwd", lambda: str(repo_abs))
    monkeypatch.setattr("pyaud.plugins._plugins", pyaud.plugins.Plugins())
    monkeypatch.setattr("pyaud.plugins.load", lambda: None)
    monkeypatch.setattr("pyaud._core._register_builtin_plugins", lambda: None)
    monkeypatch.setattr("pyaud._core._files.populate", lambda _: None)
    pyaud.files.clear()
    repo_abs.mkdir()
    # noinspection PyProtectedMember
    pyaud._core._create_cachedir()


@pytest.fixture(name="main")
def fixture_main(monkeypatch: pytest.MonkeyPatch) -> FixtureMain:
    """Pass patched commandline arguments to package's main function.

    :param monkeypatch: Mock patch environment and attributes.
    :return: Function for using this fixture.
    """

    def _main(*args: str) -> int:
        """Run main with custom args."""
        from pyaud import main

        monkeypatch.setattr("sys.argv", [pyaud.__name__, *args])
        return main()

    return _main


@pytest.fixture(name="make_tree")
def fixture_make_tree() -> FixtureMakeTree:
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
    """Unpatch ``pyaud._core._register_builtin_plugins``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud._core._register_builtin_plugins",
        original_pyaud_main_register_builtin_plugins,
    )


@pytest.fixture(name="mock_action_plugin_factory")
def fixture_mock_action_plugin_factory() -> FixtureMockActionPluginFactory:
    """Returns a list of ``Action`` objects.

    Returns variable number, depending on the quantity of names
        provided.

    :return: List of mock ``Action`` plugin types.
    """

    def _mock_action_plugin_factory(
        *params: PluginTuple,
    ) -> MockActionPluginList:
        mock_action_plugins = []
        for param in params:

            class MockActionPlugin(pyaud.plugins.Action):
                """Nothing to do."""

                def action(self, *args: str, **kwargs: bool) -> int:
                    """Nothing to do."""
                    if param.action is not None:  # noqa
                        return param.action(self, *args, **kwargs)  # noqa

                    return 0

            MockActionPlugin.__name__ = param.name
            mock_action_plugins.append(MockActionPlugin)

        return mock_action_plugins

    return _mock_action_plugin_factory


@pytest.fixture(name="mock_repo")
def fixture_mock_repo(monkeypatch: pytest.MonkeyPatch) -> FixtureMockRepo:
    """Mock ``git.Repo`` class.

    :param monkeypatch: Mock patch environment and attributes.
    :return: Function for using this fixture.
    """

    def _mock_repo(
        **kwargs: t.Callable[[VarArg(t.Any), KwArg(t.Any)], None]
    ) -> None:
        default_kwargs = {
            "rev_parse": lambda *_, **__: None,
            "status": lambda *_, **__: None,
            "rev_list": lambda *_, **__: "",
        }
        default_kwargs.update(kwargs)
        git_repo = type("Repo", (), {})
        git_repo.git = type("git", (), {})  # type: ignore
        for key, value in default_kwargs.items():
            setattr(git_repo.git, key, value)  # type: ignore

        monkeypatch.setattr("pyaud.plugins._git.Repo", lambda _: git_repo)

    return _mock_repo


@pytest.fixture(name="cache_file")
def fixture_cache_file() -> Path:
    """Create test cache dir and return a test cache file.

    :return: Path to test cache file.
    """
    cache_file = (
        Path(os.environ["PYAUD_CACHE"]) / pyaud.__version__ / "files.json"
    )
    cache_file.parent.mkdir(exist_ok=True, parents=True)
    return cache_file
