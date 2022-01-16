"""
tests.conftest
==============
"""
# pylint: disable=too-many-arguments,too-many-locals,too-few-public-methods
# pylint: disable=protected-access,no-member,too-many-statements
import copy
import os
import typing as t
from configparser import ConfigParser
from pathlib import Path

import pytest

import pyaud

from . import DEBUG, GH_EMAIL, GH_NAME, GH_TOKEN, REPO, NoColorCapsys

original_hash_mapping_match_file = pyaud.HashMapping.match_file
original_hash_mapping_unpatched_hash_files = pyaud.HashMapping.hash_files


# noinspection PyUnresolvedReferences,PyProtectedMember
@pytest.fixture(name="mock_environment", autouse=True)
def fixture_mock_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mock imports to reflect the temporary testing environment.

    :param tmp_path: Create and return temporary directory.
    :param monkeypatch: Mock patch environment and attributes.
    """
    #: CONFIG
    default_config: t.Dict[str, t.Any] = copy.deepcopy(
        pyaud.config.DEFAULT_CONFIG
    )
    default_config["logging"]["root"]["level"] = DEBUG
    logfile = Path(
        tmp_path / ".cache" / pyaud.__name__ / "log" / f"{pyaud.__name__}.log"
    )
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
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CODECOV_SLUG", f"{GH_NAME}/{REPO}")
    monkeypatch.setenv("PYAUD_GH_NAME", GH_NAME)
    monkeypatch.setenv("PYAUD_GH_EMAIL", GH_EMAIL)
    monkeypatch.setenv("PYAUD_GH_TOKEN", GH_TOKEN)
    monkeypatch.setenv("CODECOV_TOKEN", "")
    monkeypatch.delenv("CODECOV_TOKEN")
    monkeypatch.setenv("PYAUD_GH_REMOTE", str(Path.home() / "origin.git"))
    monkeypatch.setenv(
        "PYAUD_DATADIR", str(Path.home() / ".local" / "share" / pyaud.__name__)
    )
    monkeypatch.setenv(
        "PYAUD_CACHEDIR", str(Path.home() / ".cache" / pyaud.__name__)
    )
    monkeypatch.setenv("PYAUD_TIMED", "0")
    monkeypatch.setenv("PYAUD_FIX", "0")

    #: ATTRS
    monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / REPO))
    monkeypatch.setattr("setuptools.find_packages", lambda *_, **__: [REPO])
    monkeypatch.setattr("inspect.currentframe", lambda: current_frame)
    monkeypatch.setattr(
        "pyaud.config.CONFIGDIR", tmp_path / ".config" / pyaud.__name__
    )
    monkeypatch.setattr("pyaud.config.DEFAULT_CONFIG", default_config)
    monkeypatch.setattr("pyaud.config.DEFAULT_CONFIG", default_config)
    monkeypatch.setattr("pyaud.git.status", lambda *_, **__: True)
    monkeypatch.setattr("pyaud.git.rev_parse", lambda *_, **__: None)
    monkeypatch.setattr(
        "pyaud._indexing.HashMapping.match_file", lambda *_: False
    )
    monkeypatch.setattr(
        "pyaud._indexing.HashMapping.hash_files", lambda _: None
    )
    monkeypatch.setattr(
        "pyaud.plugins._plugins", copy.deepcopy(pyaud.plugins._plugins)
    )

    #: RESET
    pyaud.files.clear()
    pyaud.config.toml.clear()

    #: CREATE
    Path.cwd().mkdir()
    pyaud.git.init(devnull=True)
    logfile.parent.mkdir(parents=True)
    with open(Path.home() / ".gitconfig", "w", encoding="utf-8") as fout:
        config.write(fout)

    #: MAIN - essential setup tasks
    pyaud.plugins.load()
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
def fixture_main(monkeypatch: pytest.MonkeyPatch) -> t.Any:
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
def fixture_call_status() -> t.Any:
    """Disable all usage of function apart from selected returncode.

    Useful for processes programmed to return a value for the function
    depending on the value of ``__name__``.

    :return: Function for using this fixture.
    """

    def _call_status(module: str, returncode: int = 0) -> t.Any:
        def _func(*_, **__) -> int:
            return returncode

        _func.__name__ = module
        return _func

    return _call_status


@pytest.fixture(name="patch_sp_call")
def fixture_patch_sp_call(monkeypatch: pytest.MonkeyPatch) -> t.Any:
    """Mock ``Subprocess.call``.

    Print the command that is being run.

    :param monkeypatch: Mock patch environment and attributes.
    :return: Function for using this fixture.
    """

    def _patch_sp_call(func: t.Any, returncode: int = 0) -> t.Any:
        def call(*args: str, **kwargs: bool) -> int:
            func(*args, **kwargs)

            return returncode

        monkeypatch.setattr("spall.Subprocess.call", call)

    return _patch_sp_call


@pytest.fixture(name="patch_sp_output")
def fixture_patch_sp_output(patch_sp_call: t.Any) -> t.Any:
    """Patch ``Subprocess``.

    Return test strings to ``self.stdout``.

    :return: Function for using this fixture.
    """

    def _patch_sp_output(*stdout: str) -> None:
        _stdout = list(stdout)

        def _call(self, *_: t.Any, **__: t.Any) -> None:
            """Mock call to do nothing except send the expected stdout
            to self."""
            self._stdout.append(  # pylint: disable=protected-access
                _stdout.pop()
            )

        patch_sp_call(_call)

    return _patch_sp_output


@pytest.fixture(name="make_tree")
def fixture_make_tree() -> t.Any:
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


@pytest.fixture(name="init_remote")
def fixture_init_remote() -> None:
    """Initialize local "remote origin".

    :return: Function for using this fixture.
    """
    pyaud.git.init(  # type: ignore
        "--bare", pyaud.environ.GH_REMOTE, devnull=True
    )
    pyaud.git.remote("add", "origin", "origin", devnull=True)  # type: ignore


@pytest.fixture(name="patch_sp_print_called")
def fixture_patch_sp_print_called(patch_sp_call: t.Any) -> t.Any:
    """Mock ``Subprocess.call``to print the command that is being run.

    :param patch_sp_call: Mock ``Subprocess.call`` by injecting a new
        function into it.
    :return: Function for using this fixture.
    """

    def _patch_sp_print_called() -> t.Any:
        def _call(self, *args: str, **_: t.Any) -> None:
            print(f"{self} {' '.join(str(i) for i in args)}")

        return patch_sp_call(_call)

    return _patch_sp_print_called


@pytest.fixture(name="unpatch_hash_mapping_match_file")
def fixture_unpatch_hash_mapping_match_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unpatch ``pyaud._indexing.HashMapping.match_file``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud._indexing.HashMapping.match_file",
        original_hash_mapping_match_file,
    )


@pytest.fixture(name="unpatch_hash_mapping_hash_files")
def fixture_unpatch_hash_mapping_hash_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unpatch ``pyaud._indexing.HashMapping.hash_files``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud._indexing.HashMapping.hash_files",
        original_hash_mapping_unpatched_hash_files,
    )
