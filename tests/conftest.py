"""
tests.conftest
==============
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

import appdirs
import pytest

import pyaud

from . import (
    CallStatus,
    MakeProjectTree,
    MakeWritten,
    NoColorCapsys,
    PyaudTestError,
)


@pytest.fixture(name="is_env_path_var")
def fixture_is_env_path_var() -> Any:
    """Confirm environment variable belongs in ``pyaud`` namespace.

    Ensure package env variables are prefixed with ``PYAUD_TEST_`` or
    the ``PROJECT_DIR`` environment variable.

    :return: Function for using this fixture.
    """

    def _is_env_path_var(key: str, value: str) -> bool:
        iskey = key.startswith("PYAUD_TEST_") or key == "PROJECT_DIR"
        isval = value[0] == os.sep
        return iskey and isval

    return _is_env_path_var


@pytest.fixture(name="validate_env")
def fixture_validate_env(tmpdir: Any, is_env_path_var: Any) -> Any:
    """Ensure no real paths remain or else fail and stop the test.

    :param tmpdir:          Create and return temporary directory.
    :param is_env_path_var: Key and value are a ``pyaud`` path
                            environment variable: True or False.
    :return:                Function for using this fixture.
    """

    def _validate_env() -> None:
        for key, value in pyaud.environ.env.items():
            try:
                valuevar = os.sep.join(value.split(os.sep)[:4])
                tmpdirvar = os.sep.join(str(tmpdir).split(os.sep)[:4])
                invalid = valuevar != tmpdirvar
                if is_env_path_var(key, value) and invalid:
                    raise PyaudTestError(
                        f"environment not properly set: {key} == {value}"
                    )

            except (AttributeError, TypeError):
                pass

    return _validate_env


@pytest.fixture(name="test_logging")
def fixture_test_logging() -> Any:
    """Log environment variables to debug log."""

    def _logging() -> None:
        logger = pyaud.utils.get_logger("environ.env")
        logger.debug(pyaud.environ.env)

    return _logging


@pytest.fixture(name="project_dir")
def fixture_project_dir(tmpdir: Any) -> Any:
    """Create and return testing project root.

    :param tmpdir:  Create and return temporary directory.
    :return:        Path to testing project root.
    """
    project_dir = os.path.join(tmpdir, "repo")
    os.makedirs(project_dir)
    return project_dir


@pytest.fixture(name="mock_environment", autouse=True)
def fixture_mock_environment(  # pylint: disable=too-many-arguments
    tmpdir: Any,
    project_dir: str,
    monkeypatch: Any,
    is_env_path_var: Any,
    validate_env: Any,
    test_logging: Any,
) -> Any:
    """Mock imports to reflect the temporary testing environment.

    :param tmpdir:          Create and return temporary directory.
    :param project_dir:     Create and return testing project root.
    :param monkeypatch:     Mock patch environment and attributes.
    :param is_env_path_var: Key and value are a ``pyaud`` path
                            environment variable: True or False.
    :param validate_env:    Ensure no real paths remain or else fail and
                            stop the test.
    :param test_logging:    Log environment variables for each test.
    """

    def _mockreturn_expanduser(path: str) -> str:
        return path.replace("~", str(tmpdir))

    def _mock_return_package() -> str:
        return "repo"

    def _mock_return_user_config_dir(name: str) -> str:
        return os.path.join(tmpdir, ".config", name)

    _freeze_environ = dict(os.environ)

    monkeypatch.setattr(pyaud.environ.env, "namespace", "PYAUD_TEST")
    pyaud.environ.env["PROJECT_DIR"] = project_dir
    monkeypatch.setenv("HOME", str(tmpdir))
    monkeypatch.setenv("PROJECT_DIR", project_dir)
    monkeypatch.setenv("PYAUD_TEST_PROJECT_DIR", project_dir)
    monkeypatch.setenv("PYAUD_TEST_SUPPRESS", "False")
    monkeypatch.setenv("PYAUD_TEST_CLEAN", "False")
    monkeypatch.setenv("PYAUD_TEST_AUDIT", "False")
    monkeypatch.setenv("PYAUD_TEST_DEPLOY", "False")
    monkeypatch.setenv("PYAUD_TEST_GH_NAME", "jshwi")
    monkeypatch.setenv("PYAUD_TEST_GH_EMAIL", "stephen@jshwisolutions.com")
    monkeypatch.setenv("PYAUD_TEST_GH_TOKEN", "None")
    monkeypatch.setenv("PYAUD_TEST_CODECOV_TOKEN", "None")
    monkeypatch.setenv("PYAUD_TEST_CODECOV_SLUG", "jshwi/pyaud")
    monkeypatch.setenv("PYAUD_TEST_LOG_LEVEL", "DEBUG")
    mocks = {
        "user_config_dir": (appdirs, _mock_return_user_config_dir),
        "expanduser": (os.path, _mockreturn_expanduser),
        "find_package": (pyaud.environ, _mock_return_package),
    }
    for attr in mocks:
        monkeypatch.setattr(mocks[attr][0], attr, mocks[attr][1])
    Path(os.path.join(project_dir, ".env")).touch()
    pyaud.environ.load_namespace()
    for key, value in pyaud.environ.env.items():
        if is_env_path_var(key, str(value)):
            monkeypatch.setenv(key, str(value))

    monkeypatch.setenv("PYAUD_TEST_BRANCH", str(pyaud.utils.get_branch()))
    validate_env()
    pyaud.utils.pyitems.get_files()
    test_logging()
    yield
    os.environ.clear()
    os.environ.update(_freeze_environ)


@pytest.fixture(name="set_git_creds", autouse=True)
def fixture_set_git_creds() -> None:
    """Set git credentials."""
    git = pyaud.utils.Git(pyaud.environ.env["PROJECT_DIR"])
    git.config(  # type: ignore
        "--global", "user.email", os.environ["PYAUD_TEST_GH_EMAIL"]
    )
    git.config(  # type: ignore
        "--global", "user.name", os.environ["PYAUD_TEST_GH_NAME"]
    )


@pytest.fixture(name="init_test_repo")
def fixture_init_test_repo() -> Any:
    """Initialize and make initial commit for test ``git`` repo.

    .. code-block:: console

        $ git init "$PROJECT_DIR"
        $ git commit -m "Initial commit"
    ..
    """

    def _init_test_repo() -> None:
        with pyaud.utils.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
            git.init(devnull=True)  # type: ignore

        Path(pyaud.environ.env["README_RST"]).touch()

        with pyaud.utils.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
            git.add(".")  # type: ignore
            git.commit("-m", "Initial commit", devnull=True)  # type: ignore

    return _init_test_repo


@pytest.fixture(name="mock_remote_origin")
def fixture_mock_remote_origin(tmpdir: Any) -> Any:
    """Create a local bare repository to push to instead of a remote.

    Return the path of the 'remote' as the fixture object.

    :param tmpdir: Create and return temporary directory.
    """
    remote_origin = os.path.join(tmpdir, "origin.git")
    with pyaud.utils.Git(remote_origin) as git:
        git.init("--bare", ".", devnull=True)  # type: ignore

    return remote_origin


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

    :param monkeypatch: ``pytest`` fixture for mocking attributes.
    :return:            Function for using this fixture.
    """

    def _main(*args: str) -> None:
        """Run main with custom args."""
        monkeypatch.setattr(
            "sys.argv",
            [
                pyaud.__name__,
                "--path",
                pyaud.environ.env["PROJECT_DIR"],
                *args,
            ],
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

    def _print_called(module: str, returncode: int = 0) -> None:
        return CallStatus(module, returncode).func()

    return _print_called


@pytest.fixture(name="patch_sp_call")
def fixture_patch_sp_call(monkeypatch: Any) -> Any:
    """Mock ``Subprocess.call``.

    Print the command that is being run.

    :param monkeypatch: Mock patch environment and attributes.
    :return:            Function for using this fixture.
    """

    def _patch_sp_call(returncode: int = 0, func: Optional[Any] = None) -> Any:
        def call(self: pyaud.utils.Subprocess, *args: str, **_: Any) -> int:
            if func:
                func()
            else:
                print(f"{self.exe} {' '.join(args)}")

            return returncode

        monkeypatch.setattr(pyaud.utils.Subprocess, "call", call)

    return _patch_sp_call


@pytest.fixture(name="patch_sp_returncode")
def fixture_patch_sp_returncode(monkeypatch: Any) -> Any:
    """Patch ``subprocess.Popen.wait`` to return the chosen return code.

    :param monkeypatch: Mock patch environment and attributes.
    :return:            Function for using this fixture.
    """

    def _patch_sp_wait(returncode: int) -> None:
        def open_process(*_: Any, **__: Any) -> int:
            return returncode

        monkeypatch.setattr(
            pyaud.utils.Subprocess, "open_process", open_process
        )

    return _patch_sp_wait


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
def fixture_patch_sp_output(monkeypatch: Any) -> Any:
    """Patch ``Subprocess``.

    Return test strings to ``self.stdout``.

    :return : Function for using this fixture.
    """

    def _patch_sp_output(*stdout: Any) -> Any:
        _stdout = list(stdout)

        class _Subprocess:  # pylint: disable=too-few-public-methods
            def __init__(self, *_: Any) -> None:
                self.stdout = None

            def call(self, *_: Any, **__: Any) -> None:
                """Mock call to only assign stdout to self."""
                self.stdout = _stdout.pop()

        monkeypatch.setattr(pyaud.modules, "Subprocess", _Subprocess)

    return _patch_sp_output


@pytest.fixture(name="make_written")
def fixture_make_written() -> Type[MakeWritten]:
    """Write mock data to files.

    :return: Class as fixture.
    """
    return MakeWritten


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

            # dir
            if isinstance(value, dict):
                if not os.path.isdir(fullpath):
                    os.makedirs(fullpath)

                _make_tree(fullpath, value)

            # symlink
            elif isinstance(value, str):
                os.symlink(value, fullpath)
            else:
                Path(str(fullpath)).touch()

    return _make_tree


@pytest.fixture(name="make_project_tree")
def fixture_make_project_tree(make_tree: Any) -> MakeProjectTree:
    """Create mock directory structure.

    :return: Class as fixture.
    """
    return MakeProjectTree(make_tree)


@pytest.fixture(name="make_default_toc")
def fixture_make_default_toc(
    make_project_tree: Any, make_written: Any
) -> None:
    """Create toc files as would be created by ``sphinx-apidoc``.

    :param make_project_tree:   For creating docs tree.
    :param make_written:        For writing toc file.
    """
    make_project_tree.toc()
    make_written.repo_toc()
    Path(os.path.join(pyaud.environ.env["DOCS"], "modules.rst")).touch()


@pytest.fixture(name="make_python_file")
def fixture_make_python_file() -> None:
    """Make a blank Python file with the test project root."""
    Path(pyaud.environ.env["PROJECT_DIR"], "file.py").touch()


@pytest.fixture(name="make_test_file")
def fixture_make_test_file() -> None:
    """Create a test file with 20"""
    os.makedirs(pyaud.environ.env["TESTS"])
    testfile = os.path.join(pyaud.environ.env["TESTS"], "_test.py")
    with open(testfile, "w") as fout:
        for num in range(20):
            if num != 0:
                fout.write("\n\n")

            fout.write(f"def test_{num}():\n    pass")


@pytest.fixture(name="make_deploy_docs_env")
def fixture_make_deploy_docs_env(
    init_test_repo: Any, make_written: Any
) -> Any:
    """Setup environment for successfully running ``pyaud deploy-docs``.

    :param init_test_repo:  Initialize a test repository.
    :param make_written:    Create files containing content.
    :return:                Function for using this fixture.
    """

    def _make_deploy_env() -> None:
        init_test_repo()
        make_written.readme()
        Path(pyaud.environ.env["PROJECT_DIR"], "emptyfile").touch()
        with pyaud.utils.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
            git.add(".", devnull=True)  # type: ignore
            git.commit("-m", "empty commit", devnull=True)  # type: ignore

        with pyaud.utils.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
            git.remote("add", "origin", "origin", devnull=True)  # type: ignore

    return _make_deploy_env


@pytest.fixture(name="mock_make_docs")
def fixture_mock_make_docs(monkeypatch: Any) -> Any:
    """Mock ``pymake docs`` so that it simply creates docs/_build.

    This is sufficient for successfully triggering
    ``pymake deploy-docs``

    :param monkeypatch: Mock patch environment and attributes.
    """

    def _make_docs(*_: Any, **__: Any) -> None:
        os.makedirs(os.path.join(pyaud.environ.env["DOCS_BUILD"], "html"))

    monkeypatch.setattr(pyaud.modules, "make_docs", _make_docs)


@pytest.fixture(name="other_dir")
def fixture_other_dir(tmpdir: Any) -> Any:
    """Make a random directory named ``other_dir``.

    Dir exists alongside the cloned version of this repository in /tmp
    and returns the path.

    :param tmpdir:  Create and return temporary directory.
    :return:        Path to /tmp/*/**/other_dir
    """
    other_dir = os.path.join(tmpdir, "other")
    os.makedirs(other_dir)
    return other_dir


@pytest.fixture(name="failing_lint")
def fixture_failing_lint() -> Union[bytes, str, os.PathLike]:
    """Create and return a failing file to lint.

    :return: Path to failing file.
    """
    os.makedirs(pyaud.environ.env["PKG_PATH"])
    failing_file = os.path.join(pyaud.environ.env["PKG_PATH"], "fail.py")
    with open(failing_file, "w") as fout:
        fout.write("import this_package_does_not_exist")

    return failing_file


@pytest.fixture(name="make_readme")
def fixture_make_readme() -> Any:
    """Make temp README.

    :return Function for using this fixture.
    """

    def _make_readme(template: str) -> None:
        with open(pyaud.environ.env["README_RST"], "w") as fout:
            fout.write(template)

    return _make_readme
