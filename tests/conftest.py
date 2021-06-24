"""
tests.conftest
==============
"""
# pylint: disable=too-many-arguments,too-many-locals,too-few-public-methods
import copy
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Any, Dict, Union

import pytest

import pyaud

from . import GH_EMAIL, GH_NAME, GH_TOKEN, REPO, NoColorCapsys, PyaudTestError


@pytest.fixture(name="is_env_path_var")
def fixture_is_env_path_var() -> Any:
    """Confirm environment variable belongs in ``pyaud`` namespace.

    Ensure package env variables are prefixed with ``PYAUD_TEST_`` or
    the ``PROJECT_DIR`` environment variable.

    :return: Function for using this fixture.
    """

    def _is_env_path_var(key: str, value: str) -> bool:
        iskey = key.startswith("PYAUD_") or key == "PROJECT_DIR"
        try:
            isval = value[0] == os.sep
            return iskey and isval
        except IndexError:
            return False

    return _is_env_path_var


@pytest.fixture(name="validate_env")
def fixture_validate_env(tmp_path: Path, is_env_path_var: Any) -> Any:
    """Ensure no real paths remain or else fail and stop the test.

    :param tmp_path:        Create and return temporary directory.
    :param is_env_path_var: Key and value are a ``pyaud`` path
                            environment variable: True or False.
    :return:                Function for using this fixture.
    """

    def _validate_env() -> None:
        for key, value in os.environ.items():
            valuevar = os.sep.join(value.split(os.sep)[:4])
            tmpdirvar = os.sep.join(str(tmp_path).split(os.sep)[:4])
            invalid = valuevar != tmpdirvar
            if is_env_path_var(key, value) and invalid:
                raise PyaudTestError(
                    f"environment not properly set: {key} == {value}"
                )

    return _validate_env


@pytest.fixture(name="mock_environment", autouse=True)
def fixture_mock_environment(
    tmp_path: Path, monkeypatch: Any, validate_env: Any
) -> None:
    """Mock imports to reflect the temporary testing environment.

    :param tmp_path:        Create and return temporary directory.
    :param monkeypatch:     Mock patch environment and attributes.
    :param validate_env:    Ensure no real paths remain or else fail and
                            stop the test.
    """
    # set environment variables
    # =========================
    # load generic env variables so as to avoid a KeyError and override
    # relevant variables for test environment
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CODECOV_SLUG", f"{GH_NAME}/{REPO}")
    monkeypatch.setenv(
        "PROJECT_DIR", os.path.join(os.path.expanduser("~"), REPO)
    )

    # patch 3rd party attributes
    # ==========================
    # set the cwd to the temporary project dir
    # ensure no real .env file interferes with tests
    # patch ``setuptools.find_package`` to return package as existing
    monkeypatch.setattr(
        "dotenv.find_dotenv",
        lambda: os.path.join(os.environ["PROJECT_DIR"], ".env"),
    )
    monkeypatch.setattr("setuptools.find_packages", lambda *_, **__: [REPO])

    # patch pyaud attributes
    # ======================
    # make default testing branch ``master``
    # replace default config with changes values from above
    # set config file to test config within the temporary home dir
    monkeypatch.setattr("pyaud.modules.get_branch", lambda: "master")
    monkeypatch.setattr(
        "pyaud.config.CONFIGDIR",
        os.path.join(tmp_path, ".config", pyaud.utils.__name__),
    )
    logfile = os.path.join(
        tmp_path,
        ".cache",
        pyaud.utils.__name__,
        "log",
        f"{pyaud.__name__}.log",
    )

    # load default key-value pairs
    # ============================
    # monkeypatch implemented on prefixes and override other
    pyaud.environ.load_namespace()
    monkeypatch.setenv("PYAUD_GH_NAME", GH_NAME)
    monkeypatch.setenv("PYAUD_GH_EMAIL", GH_EMAIL)
    monkeypatch.setenv("PYAUD_GH_TOKEN", GH_TOKEN)
    monkeypatch.setenv("CODECOV_TOKEN", "")
    monkeypatch.setenv(
        "PYAUD_GH_REMOTE", os.path.join(os.path.expanduser("~"), "origin.git")
    )

    # confirm all environment variables changed
    # =========================================
    validate_env()

    # prepare test locations
    # ======================
    # create test directories
    # ~/.cache/pyaud/log/pyaud.utils.log needs to exist before running
    # ``logging.config.dictConfig(config: Dict[str, Any])``
    os.makedirs(os.environ["PROJECT_DIR"])
    os.makedirs(os.path.dirname(logfile))

    # initialize repository
    # =====================
    with pyaud.utils.Git(os.environ["PROJECT_DIR"]) as git:
        git.init(devnull=True)  # type: ignore

    # prepare default config
    # ======================
    # override log file path to point to test repository
    # loglevel to DEBUG
    default_config: Dict[str, Any] = copy.deepcopy(pyaud.config.DEFAULT_CONFIG)
    default_config["logging"]["handlers"]["default"]["filename"] = logfile
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
    with open(
        os.path.join(os.path.expanduser("~"), ".gitconfig"), "w"
    ) as fout:
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
        monkeypatch.setattr(
            "sys.argv",
            [pyaud.__name__, "--path", os.environ["PROJECT_DIR"], *args],
        )
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
            self.stdout = ""
            self.stdout += _stdout.pop()

        patch_sp_call(_call)

    return _patch_sp_output


@pytest.fixture(name="make_tree")
def fixture_make_tree() -> Any:
    """Recursively create directory tree from dict mapping.

    :return: Function for using this fixture.
    """

    def _make_tree(
        root: Union[bytes, str, os.PathLike], obj: Dict[Any, Any]
    ) -> None:
        for key, value in obj.items():
            fullpath = os.path.join(root, key)
            if isinstance(value, dict):
                os.makedirs(fullpath, exist_ok=True)
                _make_tree(fullpath, value)

            elif isinstance(value, str):
                os.symlink(value, fullpath)
            else:
                Path(str(fullpath)).touch()

    return _make_tree


@pytest.fixture(name="make_test_file")
def fixture_make_test_file() -> None:
    """Create a test file with 20."""
    testdir = os.environ["PYAUD_TESTS"]
    os.makedirs(testdir)
    testfile = os.path.join(testdir, "_test.py")
    with open(testfile, "w") as fout:
        for num in range(20):
            fout.write(f"def test_{num}():\n    pass\n")


@pytest.fixture(name="init_remote")
def fixture_init_remote() -> None:
    """Initialize local "remote origin".

    :return: Function for using this fixture.
    """
    with pyaud.utils.Git(os.environ["PYAUD_GH_REMOTE"]) as git:
        git.init("--bare", ".", devnull=True)  # type: ignore

    with pyaud.utils.Git(os.environ["PROJECT_DIR"]) as git:
        git.remote("add", "origin", "origin", devnull=True)  # type: ignore


@pytest.fixture(name="patch_sp_print_called")
def fixture_patch_sp_print_called(patch_sp_call: Any) -> Any:
    """Mock ``Subprocess.call``to print the command that is being run.

    :param patch_sp_call:   Mock ``Subprocess.call`` by injecting a new
                            function into it.
    :return:                Function for using this fixture.
    """

    def _patch_sp_print_called() -> Any:
        def _call(self: pyaud.utils.Subprocess, *args: str, **_: Any) -> None:
            print(f"{self.exe} {' '.join(str(i) for i in args)}")

        return patch_sp_call(_call)

    return _patch_sp_print_called
