"""
tests.conftest
==============
"""
# pylint: disable=too-many-arguments,too-many-locals,too-few-public-methods
import copy
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Any, Dict

import pytest

import pyaud

from . import GH_EMAIL, GH_NAME, GH_TOKEN, REPO, NoColorCapsys


@pytest.fixture(name="mock_environment", autouse=True)
def fixture_mock_environment(tmp_path: Path, monkeypatch: Any) -> None:
    """Mock imports to reflect the temporary testing environment.

    :param tmp_path:     Create and return temporary directory.
    :param monkeypatch: Mock patch environment and attributes.
    """
    # set environment variables
    # =========================
    # load generic env variables so as to avoid a KeyError and override
    # relevant variables for test environment
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CODECOV_SLUG", f"{GH_NAME}/{REPO}")

    # patch 3rd party attributes
    # ==========================
    # set the cwd to the temporary project dir
    # ensure no real .env file interferes with tests
    # patch ``setuptools.find_package`` to return package as existing
    monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / REPO))
    monkeypatch.setattr("dotenv.find_dotenv", lambda: str(Path.cwd() / ".env"))
    monkeypatch.setattr("setuptools.find_packages", lambda *_, **__: [REPO])

    # patch pyaud attributes
    # ======================
    # make default testing branch ``master``
    # replace default config with changes values from above
    # set config file to test config within the temporary home dir
    monkeypatch.setattr("pyaud.modules.get_branch", lambda: "master")
    monkeypatch.setattr(
        "pyaud.config.CONFIGDIR", tmp_path / ".config" / pyaud.__name__
    )
    logfile = Path(
        tmp_path / ".cache" / pyaud.__name__ / "log" / f"{pyaud.__name__}.log"
    )

    # load default key-value pairs
    # ============================
    # monkeypatch implemented on prefixes and override other
    pyaud.environ.load_namespace()
    monkeypatch.setenv("PYAUD_GH_NAME", GH_NAME)
    monkeypatch.setenv("PYAUD_GH_EMAIL", GH_EMAIL)
    monkeypatch.setenv("PYAUD_GH_TOKEN", GH_TOKEN)
    monkeypatch.setenv("CODECOV_TOKEN", "")
    monkeypatch.setenv("PYAUD_GH_REMOTE", str(Path.home() / "origin.git"))

    # prepare test locations
    # ======================
    # create test directories
    # ~/.cache/pyaud/log/pyaud.log needs to exist before running
    # ``logging.config.dictConfig(config: Dict[str, Any])``
    Path.cwd().mkdir()
    logfile.parent.mkdir(parents=True)

    # initialize repository
    # =====================
    pyaud.utils.git.init(devnull=True)  # type: ignore

    # prepare default config
    # ======================
    # override log file path to point to test repository
    # loglevel to DEBUG
    default_config: Dict[str, Any] = copy.deepcopy(pyaud.config.DEFAULT_CONFIG)
    default_config["logging"]["handlers"]["default"]["filename"] = str(logfile)
    default_config["logging"]["root"]["level"] = pyaud.config.DEBUG
    monkeypatch.setattr("pyaud.config.DEFAULT_CONFIG", default_config)

    # create ~/.gitconfig
    # ===================
    config = ConfigParser(default_section="")
    config.read_dict(
        {
            "user": {"name": GH_NAME, "email": GH_EMAIL},
            "advice": {"detachedHead": "false"},
            "init": {"defaultBranch": "master"},
        }
    )
    with open(Path.home() / ".gitconfig", "w") as fout:
        config.write(fout)

    # setup singletons
    # ================
    pyaud.utils.tree.clear()
    pyaud.config.toml.clear()
    pyaud.utils.tree.populate()
    pyaud.config.configure_global()
    pyaud.config.load_config()
    pyaud.config.configure_logging()


@pytest.fixture(name="nocolorcapsys")
def fixture_nocolorcapsys(capsys: Any) -> NoColorCapsys:
    """Instantiate capsys with the regex method.

    :param capsys:  Capture ``sys`` stdout and stderr..
    :return:        Instantiated ``NoColorCapsys`` object for capturing
                    output stream and sanitizing the string if it
                    contains ANSI escape codes.
    """
    return NoColorCapsys(capsys)


@pytest.fixture(name="main")
def fixture_main(monkeypatch: Any) -> Any:
    """Pass patched commandline arguments to package's main function.

    :param monkeypatch: Mock patch environment and attributes.
    :return:            Function for using this fixture.
    """

    def _main(*args: str) -> None:
        """Run main with custom args."""
        monkeypatch.setattr("sys.argv", [pyaud.__name__, *args])
        pyaud.main()

    return _main


@pytest.fixture(name="call_status")
def fixture_call_status() -> Any:
    """Disable all usage of function apart from selected returncode.

    Useful for processes programmed to return a value for the function
    depending on the value of ``__name__``.

    :return: Function for using this fixture.
    """

    def _call_status(module: str, returncode: int = 0) -> Any:
        def _func(*_, **__) -> int:
            return returncode

        _func.__name__ = module
        return _func

    return _call_status


@pytest.fixture(name="patch_sp_call")
def fixture_patch_sp_call(monkeypatch: Any) -> Any:
    """Mock ``Subprocess.call``.

    Print the command that is being run.

    :param monkeypatch: Mock patch environment and attributes.
    :return:            Function for using this fixture.
    """

    def _patch_sp_call(func: Any, returncode: int = 0) -> Any:
        def call(*args: str, **kwargs: bool) -> int:
            func(*args, **kwargs)

            return returncode

        monkeypatch.setattr("pyaud.utils.Subprocess.call", call)

    return _patch_sp_call


@pytest.fixture(name="track_called")
def fixture_track_called() -> Any:
    """Decorate a mocked function to print what was called.

    :return: Function for using this fixture.
    """

    def _track_called(func: Any) -> Any:
        def _track(*_: Any, **__: Any) -> Any:
            print(func.__name__)
            return func()

        return _track

    return _track_called


@pytest.fixture(name="patch_sp_output")
def fixture_patch_sp_output(patch_sp_call: Any) -> Any:
    """Patch ``Subprocess``.

    Return test strings to ``self.stdout``.

    :return : Function for using this fixture.
    """

    def _patch_sp_output(*stdout: str) -> None:
        _stdout = list(stdout)

        def _call(self: pyaud.utils.Subprocess, *_: Any, **__: Any) -> None:
            """Mock call to to do nothing except send the expected
            stdout to self."""
            self._stdout.append(  # pylint: disable=protected-access
                _stdout.pop()
            )

        patch_sp_call(_call)

    return _patch_sp_output


@pytest.fixture(name="make_tree")
def fixture_make_tree() -> Any:
    """Recursively create directory tree from dict mapping.

    :return: Function for using this fixture.
    """

    def _make_tree(root: Path, obj: Dict[Any, Any]) -> None:
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


@pytest.fixture(name="make_test_file")
def fixture_make_test_file() -> None:
    """Create a test file with 20."""
    file = Path.cwd() / pyaud.environ.TESTS / "_test.py"
    file.parent.mkdir()
    with open(file, "w") as fout:
        for num in range(20):
            fout.write(f"def test_{num}():\n    pass\n")


@pytest.fixture(name="init_remote")
def fixture_init_remote() -> None:
    """Initialize local "remote origin".

    :return: Function for using this fixture.
    """
    pyaud.utils.git.init(  # type: ignore
        "--bare", Path(os.environ["PYAUD_GH_REMOTE"]), devnull=True
    )
    pyaud.utils.git.remote(  # type: ignore
        "add", "origin", "origin", devnull=True
    )


@pytest.fixture(name="patch_sp_print_called")
def fixture_patch_sp_print_called(patch_sp_call: Any) -> Any:
    """Mock ``Subprocess.call``to print the command that is being run.

    :param patch_sp_call:   Mock ``Subprocess.call`` by injecting a new
                            function into it.
    :return:                Function for using this fixture.
    """

    def _patch_sp_print_called() -> Any:
        def _call(self: pyaud.utils.Subprocess, *args: str, **_: Any) -> None:
            print(f"{self} {' '.join(str(i) for i in args)}")

        return patch_sp_call(_call)

    return _patch_sp_print_called
