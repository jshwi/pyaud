"""
tests.conftest
==============
"""
import os
import pathlib
import sys
from typing import Any, Dict, Union

import appdirs
import pytest

import pyaud
import tests


@pytest.fixture(name="is_env_path_var")
def fixture_is_env_path_var():
    """Confirm that an environment variable belongs in the ``pyaud``
    namespace, that are prefixed with ``PYAUD_TEST_`` or the ``PROJECT_DIR``
    environment variable.

    :return: Function for using this fixture.
    """

    def _is_env_path_var(key, value):
        iskey = key.startswith("PYAUD_TEST_") or key == "PROJECT_DIR"
        isval = value[0] == os.sep
        return iskey and isval

    return _is_env_path_var


@pytest.fixture(name="validate_env")
def fixture_validate_env(tmpdir, is_env_path_var):
    """Ensure no real paths remain or else fail and stop the test

    :param tmpdir:          ``pytest`` ``tmpdir`` fixture for creating
                            and returning a temporary directory.
    :param is_env_path_var: Key and value are a ``pyaud`` path
                            environment variable: True or False.
    :return:                Function for using this fixture.
    """

    def _validate_env():
        for key, value in pyaud.environ.env.items():
            try:
                valuevar = os.sep.join(value.split(os.sep)[:4])
                tmpdirvar = os.sep.join(str(tmpdir).split(os.sep)[:4])
                invalid = valuevar != tmpdirvar
                if is_env_path_var(key, value) and invalid:
                    raise tests.PyaudTestError(
                        f"environment not properly set: {key} == {value}"
                    )

            except (AttributeError, TypeError):
                pass

    return _validate_env


@pytest.fixture(name="test_logging")
def fixture_test_logging():
    """Log environment variables to debug log."""

    def _logging():
        logger = pyaud.get_logger("environ.env")
        logger.debug(pyaud.environ.env)

    return _logging


@pytest.fixture(name="project_dir")
def fixture_project_dir(tmpdir):
    """Create and return testing project root.

    :param tmpdir:  ``pytest`` ``tmpdir`` fixture for creating and
                    returning a temporary directory.
    :return:        Path to testing project root.
    """
    project_dir = os.path.join(tmpdir, "repo")
    os.makedirs(project_dir)
    return project_dir


@pytest.fixture(name="mock_environment", autouse=True)
def fixture_mock_environment(  # pylint: disable=too-many-arguments
    tmpdir,
    project_dir,
    monkeypatch,
    is_env_path_var,
    validate_env,
    test_logging,
):
    """Mock the ary imports to reflect the temporary testing
    environment.

    :param tmpdir:          ``pytest`` ``tmpdir`` fixture for creating
                            and returning a temporary directory.
    :param project_dir:     Create and return testing project root.
    :param monkeypatch:     ``pytest`` fixture for mocking attributes.
    :param is_env_path_var: Key and value are a ``pyaud`` path
                            environment variable: True or False.
    :param validate_env:    Ensure no real paths remain or else fail and
                            stop the test.
    :param test_logging:    Log environment variables for each test.
    """

    def _mockreturn_expanduser(path):
        return path.replace("~", str(tmpdir))

    def _mock_return_package():
        return "repo"

    def _mock_return_user_config_dir(name):
        return os.path.join(tmpdir, ".config", name)

    _freeze_environ = dict(os.environ)

    pyaud.colors.populate_colors()
    monkeypatch.setattr(pyaud.environ.env, "namespace", "PYAUD_TEST")
    pyaud.environ.env["PROJECT_DIR"] = project_dir
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
    pathlib.Path(os.path.join(project_dir, ".env")).touch()
    pyaud.environ.load_namespace()
    for key, value in pyaud.environ.env.items():
        if is_env_path_var(key, str(value)):
            monkeypatch.setenv(key, str(value))

    monkeypatch.setenv("PYAUD_TEST_BRANCH", str(pyaud.get_branch()))
    validate_env()
    pyaud.pyitems.get_files()
    test_logging()
    yield
    os.environ.clear()
    os.environ.update(_freeze_environ)


@pytest.fixture(name="set_git_creds", autouse=True)
def fixture_set_git_creds():
    """Set git credentials."""
    git = pyaud.Git(pyaud.environ.env["PROJECT_DIR"])
    git.config("--global", "user.email", os.environ["PYAUD_TEST_GH_EMAIL"])
    git.config("--global", "user.name", os.environ["PYAUD_TEST_GH_NAME"])


@pytest.fixture(name="init_test_repo")
def fixture_init_test_repo():
    """Initialize and make initial commit for test ``git`` repo.

    .. code-block:: console

        $ git init "$PROJECT_DIR"
        $ git commit -m "Initial commit"
    ..
    """

    def _init_test_repo():
        with pyaud.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
            git.init(devnull=True)

        pathlib.Path(pyaud.environ.env["README_RST"]).touch()

        with pyaud.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
            git.add(".")
            git.commit("-m", "Initial commit", devnull=True)

    return _init_test_repo


@pytest.fixture(name="mock_remote_origin")
def fixture_mock_remote_origin(tmpdir):
    """Create a local bare repository to push to instead of a remote
    origin URL. Return the path of the 'remote' as the fixture object.

    :param tmpdir:  ``pytest`` ``tmpdir`` fixture for creating and
                    returning a temporary directory.
    """
    remote_origin = os.path.join(tmpdir, "origin.git")
    with pyaud.Git(remote_origin) as git:
        git.init("--bare", ".", devnull=True)

    return remote_origin


@pytest.fixture(name="nocolorcapsys")
def fixture_nocolorcapsys(capsys):
    """Instantiate capsys with the regex method

    :param capsys: ``pytest`` fixture for capturing output stream.
    :return:        Instantiated ``NoColorCapsys`` object for capturing
                    output stream and sanitizing the string if it
                    contains ANSI escape codes.
    """
    return tests.NoColorCapsys(capsys)


@pytest.fixture(name="patch_argv")
def fixture_patch_argv(monkeypatch):
    """Function for passing mock commandline arguments to ``sys.argv``.

    :param monkeypatch: ``pytest`` fixture for mocking attributes.
    :return:            Function for using this fixture.
    """

    def _argv(*args):
        args = [__name__, "--path", pyaud.environ.env["PROJECT_DIR"], *args]
        monkeypatch.setattr(sys, "argv", args)

    return _argv


@pytest.fixture(name="parser")
def fixture_parser(patch_argv):
    """Function for passing mock commandline arguments to ``Parser``
    class.

    :param patch_argv:  Set args with ``sys.argv``
    :return:            Function for using this fixture.
    """

    def _parser(*args):
        patch_argv(*args)
        return pyaud.Parser(__name__)

    return _parser


@pytest.fixture(name="main")
def fixture_main(patch_argv):
    """Function for passing mock ``pyaud.main`` commandline arguments
    to package's main function.

    :param patch_argv:  Set args with ``sys.argv``
    :return:            Function for using this fixture.
    """

    def _main(*args):
        """Run pyaud.main with custom args."""
        patch_argv(*args)
        pyaud.main()

    return _main


@pytest.fixture(name="call_status")
def fixture_call_status():
    """Fixture for ``CallStatus`` factory class.

    :return: Function for using this fixture.
    """

    def _print_called(module, returncode=0):
        return tests.CallStatus(module, returncode).func()

    return _print_called


@pytest.fixture(name="patch_sp_call")
def fixture_patch_sp_call(monkeypatch):
    """Mock ``pyaud.Subprocess.call``to print the command that is
    being run.

    :param monkeypatch: ``pytest`` fixture for mocking attributes.
    :return:            Function for using this fixture.
    """

    def _patch_sp_call(returncode=0, func=None):
        def call(self, *args, **_):
            if func:
                func()
            else:
                print(self.exe + " " + " ".join(args))

            return returncode

        monkeypatch.setattr(pyaud.Subprocess, "call", call)

    return _patch_sp_call


@pytest.fixture(name="patch_sp_returncode")
def fixture_patch_sp_returncode(monkeypatch):
    """Patch ``subprocess.Popen.wait`` to return the chosen return code.

    :param monkeypatch: ``pytest`` fixture for mocking attributes.
    :return:            Function for using this fixture.
    """

    def _patch_sp_wait(returncode):
        def open_process(*_, **__):
            return returncode

        monkeypatch.setattr(pyaud.Subprocess, "open_process", open_process)

    return _patch_sp_wait


@pytest.fixture(name="track_called")
def fixture_track_called():
    """Decorate a mocked function to print what was called.

    :return: Function for using this fixture.
    """

    def _track_called(func):
        def _track(*_, **__):
            print(func.__name__)
            return func()

        return _track

    return _track_called


@pytest.fixture(name="patch_sp_output")
def fixture_patch_sp_output():
    """Patch ``pyaud.Subprocess`` to return test strings to
    ``self.stdout``.

    :return : Function for using this fixture.
    """
    pyaud_sp = pyaud.Subprocess

    def _patch_sp_output(*stdout):
        stdout = list(stdout)

        class _Subprocess:  # pylint: disable=too-few-public-methods
            def __init__(self, *_):
                self.stdout = None

            def call(self, *_, **__):
                """Mock call to to do nothing except send the expected
                stdout to self
                """
                self.stdout = stdout.pop()

        pyaud.modules.Subprocess = _Subprocess

    yield _patch_sp_output
    pyaud.modules.Subprocess = pyaud_sp


@pytest.fixture(name="make_written")
def fixture_make_written():
    """Write mock data to files.

    :return: Class as fixture.
    """
    return tests.MakeWritten


@pytest.fixture(name="make_tree")
def fixture_make_tree():
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
                pathlib.Path(str(fullpath)).touch()

    return _make_tree


@pytest.fixture(name="make_project_tree")
def fixture_make_project_tree(make_tree):
    """Create mock directory structure.

    :return: Class as fixture.
    """
    return tests.MakeProjectTree(make_tree)


@pytest.fixture(name="make_default_toc")
def fixture_make_default_toc(make_project_tree, make_written):
    """Create toc files as would be created by ``sphinx-apidoc``.

    :param make_project_tree:   For creating docs tree.
    :param make_written:        For writing toc file.
    """
    make_project_tree.toc()
    make_written.repo_toc()
    pathlib.Path(
        os.path.join(pyaud.environ.env["DOCS"], "modules.rst")
    ).touch()


@pytest.fixture(name="make_python_file")
def fixture_make_python_file():
    """Make a blank Python file with the test project root."""
    pathlib.Path(pyaud.environ.env["PROJECT_DIR"], "file.py").touch()


@pytest.fixture(name="make_test_file")
def fixture_make_test_file():
    """Create a test file with 20 tests."""
    os.makedirs(pyaud.environ.env["TESTS"])
    testfile = os.path.join(pyaud.environ.env["TESTS"], "_test.py")
    with open(testfile, "w") as fout:
        for num in range(20):
            if num != 0:
                fout.write("\n\n")

            fout.write(f"def test_{num}():\n    pass")


@pytest.fixture(name="make_deploy_docs_env")
def fixture_make_deploy_docs_env(init_test_repo, make_written):
    """Set up the environment suitable for successfully running
    ``pyaud deploy-docs``.

    :param init_test_repo:  Initialize a test repository.
    :param make_written:    Create files containing content.
    :return:                Function for using this fixture.
    """

    def _make_deploy_env():
        init_test_repo()
        make_written.readme()
        pathlib.Path(pyaud.environ.env["PROJECT_DIR"], "emptyfile").touch()
        with pyaud.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
            git.add(".", devnull=True)
            git.commit("-m", "empty commit", devnull=True)

        with pyaud.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
            git.remote("add", "origin", "origin", devnull=True)

    return _make_deploy_env


@pytest.fixture(name="mock_make_docs")
def fixture_mock_make_docs(monkeypatch):
    """Mock ``pymake docs`` so that it simply creates a docs/_build dir
    and docs/_build/html dir. This will sufficient for successfully
    triggering ``pymake deploy-docs``

    :param monkeypatch: ``pytest`` fixture for mocking attributes.
    """

    def _make_docs(*_, **__):
        os.makedirs(os.path.join(pyaud.environ.env["DOCS_BUILD"], "html"))

    monkeypatch.setattr(pyaud.modules, "make_docs", _make_docs)


@pytest.fixture(name="other_dir")
def fixture_other_dir(tmpdir):
    """Make a random directory named ``other_dir`` to exist alongside
    the cloned version of this repository in /tmp and return the path.

    :param tmpdir:  ``pytest`` ``tmpdir`` fixture for creating and
                    returning a temporary directory.
    :return:        Path to /tmp/*/**/other_dir
    """
    other_dir = os.path.join(tmpdir, "other")
    os.makedirs(other_dir)
    return other_dir


@pytest.fixture(name="failing_lint")
def fixture_failing_lint():
    """Create a failing file to lint."""
    os.makedirs(pyaud.environ.env["PKG_PATH"])
    failing_file = os.path.join(pyaud.environ.env["PKG_PATH"], "fail.py")
    with open(failing_file, "w") as fout:
        fout.write("import this_package_does_not_exist")

    return failing_file


@pytest.fixture(name="make_readme")
def fixture_make_readme():
    """Make temp README."""

    def _make_readme(template):
        with open(pyaud.environ.env["README_RST"], "w") as fout:
            fout.write(template)

    return _make_readme
