"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments,cell-var-from-loop
import configparser
import copy
import datetime
import logging
import logging.config as logging_config
import os
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Tuple

import dotenv
import pytest

import pyaud

from . import (
    CONFPY,
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
    NO_ISSUES,
    PUSHING_SKIPPED,
    REAL_REPO,
    REPO,
    WARNING,
    PyaudTestError,
    files,
)


def test_no_files_found(nocolorcapsys: Any) -> None:
    """Test the correct output is produced when no file exists.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    pyaud.modules.make_typecheck()
    assert nocolorcapsys.stdout().strip() == "No files found"


@pytest.mark.usefixtures("make_test_file")
@pytest.mark.parametrize(
    "module,expected",
    [
        ("make_unused", "Success: no issues found in 1 source files"),
        ("make_tests", "Success: no issues found in 1 source files"),
    ],
    ids=["files", "tests"],
)
def test_success_output(
    nocolorcapsys: Any,
    monkeypatch: Any,
    make_tree: Any,
    call_status: Any,
    module: str,
    expected: str,
) -> None:
    """Test the output returned from ``check_command`` decorator.

    Test decorator matches the function being used. Changed the
    parametrized ``func`` __name__ to match the mocked module.

    :param nocolorcapsys:       Capture system output while stripping
                                ANSI color codes.
    :param monkeypatch:         Mock patch environment and attributes.
    :param make_tree:           Create directory tree from dict mapping.
    :param call_status:         Patch function to return specific
                                exit-code.
    :param module:              Function to test.
    """
    make_tree(os.environ["PROJECT_DIR"], {"docs": {CONFPY: None}})
    with pyaud.utils.Git(os.environ["PROJECT_DIR"]) as git:
        git.add(".")  # type: ignore

    pyaud.utils.tree.populate()
    monkeypatch.setattr(
        f"pyaud.modules.{module}",
        pyaud.utils.check_command(call_status(module)),
    )
    getattr(pyaud.modules, module)()
    assert nocolorcapsys.stdout().strip() == expected


@pytest.mark.parametrize(
    "contents,expected",
    [
        (["created"], "created ``whitelist.py``"),
        (["", "updated"], "updated ``whitelist.py``"),
        (
            ["up-to-date", "up-to-date"],
            "``whitelist.py`` is already up to date",
        ),
    ],
    ids=("created", "updated", "up_to_date"),
)
def test_write_command(
    monkeypatch: Any, nocolorcapsys: Any, contents: List[str], expected: str
) -> None:
    """Test the ``@write_command`` decorator.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param monkeypatch:     Mock patch environment and attributes.
    :param contents:        Content to write to file.
    :param expected:        Expected output.
    """
    for content in contents:

        def mock_write_whitelist() -> None:
            with open(os.environ["PYAUD_WHITELIST"], "w") as fout:
                fout.write(content)

        monkeypatch.setattr(
            "pyaud.modules.make_whitelist",
            pyaud.utils.write_command("PYAUD_WHITELIST")(mock_write_whitelist),
        )
        pyaud.modules.make_whitelist()

    assert expected in nocolorcapsys.stdout()


def test_make_audit_error(monkeypatch: Any, nocolorcapsys: Any) -> None:
    """Test errors are handled correctly when running ``pyaud audit``.

    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    monkeypatch.setattr(
        "pyaud.utils.Subprocess._open_process", lambda *_, **__: 1
    )
    pyaud.utils.tree.append(FILES)
    with pytest.raises(CalledProcessError):
        pyaud.modules.make_audit()

    assert nocolorcapsys.stdout().strip() == "pyaud format"


def test_call_coverage_xml(
    monkeypatch: Any, patch_sp_print_called: Any, nocolorcapsys: Any
) -> None:
    """Test ``coverage xml`` is called after successful test run.

    :param monkeypatch:             Mock patch environment and
                                    attributes.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    """
    patch_sp_print_called()
    monkeypatch.setattr("pyaud.modules.make_tests", lambda *_, **__: 0)
    pyaud.modules.make_coverage()
    assert nocolorcapsys.stdout().strip() == "<Subprocess (coverage)> xml"


def test_make_deploy_all(
    monkeypatch: Any, nocolorcapsys: Any, call_status: Any
) -> None:
    """Test the correct commands are run when running ``pyaud deploy``.

    Patch functions with ``call_status`` to remove functionality from
    function and only return a zero exit-status. ``make_deploy_*``
    functions should still be able to print what functions are being run
    as announced to the console in cyan.

    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param call_status:    Patch function to not do anything.
                            Optionally returns non-zero exit code (0 by
                            default).
    """
    modules = "make_deploy_cov", "make_deploy_docs"
    for module in modules:
        monkeypatch.setattr(f"pyaud.modules.{module}", call_status(module))

    pyaud.modules.make_deploy()
    out = nocolorcapsys.stdout().splitlines()
    for module in modules:
        assert (
            module.replace("make_", f"{pyaud.__name__} ").replace("_", "-")
            in out
        )


def test_make_deploy_all_fail(
    call_status: Any, monkeypatch: Any, nocolorcapsys: Any
) -> None:
    """Test ``pyaud deploy`` fails correctly when encountering an error.

    :param call_status:     Patch function to return specific exit-code.
    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    deploy_module = "make_deploy_docs"
    monkeypatch.setattr(
        f"pyaud.modules.{deploy_module}", call_status(deploy_module, 1)
    )
    pyaud.modules.make_deploy()
    assert (
        deploy_module.replace("make_", f"{pyaud.__name__} ").replace("_", "-")
        in nocolorcapsys.stdout().splitlines()
    )


def test_make_docs_no_docs(nocolorcapsys: Any) -> None:
    """Test correct message is produced.

    Test when running ``pyaud docs`` when no docs are present.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    Path(os.environ["PROJECT_DIR"], FILES).touch()
    pyaud.modules.make_docs()
    assert nocolorcapsys.stdout().strip() == "No docs found"


def test_suppress(
    monkeypatch: Any, nocolorcapsys: Any, call_status: Any, make_tree: Any
) -> None:
    """Test that audit proceeds through errors with ``--suppress``.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param monkeypatch:     Mock patch environment and attributes.
    :param call_status:     Patch function to return specific exit-code.
    :param make_tree:       Create directory tree from dict mapping.
    """
    make_tree(os.environ["PROJECT_DIR"], {FILES: None, "docs": {CONFPY: None}})
    with pyaud.utils.Git(os.environ["PROJECT_DIR"]) as git:
        git.add(".")  # type: ignore

    pyaud.utils.tree.populate()
    audit_modules = [
        "make_format",
        "make_format_docs",
        "make_format_str",
        "make_imports",
        "make_typecheck",
        "make_unused",
        "make_lint",
        "make_coverage",
        "make_readme",
        "make_docs",
    ]
    for audit_module in audit_modules:
        mockreturn = call_status(audit_module, 1)
        monkeypatch.setattr(
            f"pyaud.modules.{audit_module}",
            pyaud.utils.check_command(mockreturn),
        )

    pyaud.modules.make_audit()
    errs = nocolorcapsys.stderr().splitlines()
    assert len(
        [e for e in errs if "Failed: returned non-zero exit status" in e]
    ) == len(audit_modules)


@pytest.mark.parametrize(
    "args,add,first,last",
    [
        ([], [], "pyaud format", "pyaud docs"),
        (["--clean"], ["make_clean"], "pyaud clean", "pyaud docs"),
        (["--deploy"], ["make_deploy"], "pyaud format", "pyaud deploy"),
        (
            ["--clean", "--deploy"],
            ["make_clean", "make_deploy"],
            "pyaud clean",
            "pyaud deploy",
        ),
    ],
    ids=["no_args", "clean", "deploy", "clean_and_deploy"],
)
def test_audit_modules(
    monkeypatch: Any,
    nocolorcapsys: Any,
    main: Any,
    call_status: Any,
    args: List[str],
    add: List[str],
    first: str,
    last: str,
) -> None:
    """Test that the correct functions are called with ``make_audit``.

    Mock all functions in ``MODULES`` to do nothing so the test can
    confirm that all the functions that are meant to be run are run with
    the output that is displayed to the console in cyan. Confirm what
    the first and last functions being run are with the parametrized
    values.

    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param main:            Patch package entry point.
    :param call_status:     Patch function to not do anything.
                            Optionally returns non-zero exit code (0 by
                            default).
    :param args:            Arguments for ``pyaud audit``.
    :param add:             Function to add to the ``audit_modules``
                            list
    :param first:           Expected first function executed.
    :param last:            Expected last function executed.
    """
    audit_modules = [
        "make_format",
        "make_format_docs",
        "make_format_str",
        "make_imports",
        "make_typecheck",
        "make_unused",
        "make_lint",
        "make_coverage",
        "make_readme",
        "make_docs",
    ]
    audit_modules.extend(add)
    for audit_module in audit_modules:
        monkeypatch.setattr(
            f"pyaud.modules.{audit_module}", call_status(audit_module)
        )

    main("audit", *args)
    output = [i for i in nocolorcapsys.stdout().splitlines() if i != ""]
    expected = [
        i.replace("make_", f"{pyaud.__name__} ").replace("_", "-")
        for i in audit_modules
    ]
    assert all([i in output for i in expected])
    assert output[0] == first
    assert output[-1] == last


def test_coverage_no_tests(nocolorcapsys: Any) -> None:
    """Test the correct output is produced when no tests exists.

     Ensure message is displayed if ``pytest`` could not find a valid
     test folder.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    pyaud.modules.make_coverage()
    assert nocolorcapsys.stdout().strip() == (
        "No tests found\nNo coverage to report"
    )


def test_make_docs_toc_fail(monkeypatch: Any, make_tree: Any) -> None:
    """Test that error message is produced when ``make_toc`` fails.

    Test process stops when ``make_toc`` fails before running the main
    ``make_docs`` process.

    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree:   Create directory tree from dict mapping.
    """
    make_tree(os.environ["PROJECT_DIR"], {"docs": {CONFPY: None}})
    monkeypatch.setattr(
        "pyaud.utils.Subprocess._open_process", lambda *_, **__: 1
    )
    with pytest.raises(CalledProcessError) as err:
        pyaud.modules.make_docs()

    assert str(err.value) == (
        "Command 'sphinx-apidoc -o {} {} -f' "
        "returned non-zero exit status 1.".format(
            os.environ["PYAUD_DOCS"], os.environ["PYAUD_PKG_PATH"]
        )
    )


def test_make_docs_rm_cache(
    monkeypatch: Any, call_status: Any, make_tree: Any
) -> None:
    """Test ``make_docs`` removes all builds before starting a new one.

    :param monkeypatch:     Mock patch environment and attributes.
    :param call_status:     Patch function to return specific exit-code.
    :param make_tree:       Create directory tree from dict mapping.
    """
    builddir = os.environ["BUILDDIR"]
    readme = os.environ["PYAUD_README_RST"]

    # disable call to ``Subprocess`` to only create ./docs/_build
    # directory so tests can continue
    def _call(*_: Any, **__: Any) -> int:
        os.makedirs(builddir)
        return 0

    # patch ``make_toc`` and ``Subprocess.call``
    monkeypatch.setattr("pyaud.modules.make_toc", call_status("make_toc"))
    monkeypatch.setattr("pyaud.utils.Subprocess.call", _call)
    make_tree(
        os.environ["PROJECT_DIR"], {"docs": {CONFPY: None, "readme.rst": None}}
    )
    with open(readme, "w") as fout:
        fout.write(files.README_RST)

    monkeypatch.setattr("pyaud.modules.make_toc", call_status("make_toc", 0))
    os.makedirs(builddir)
    Path(builddir, "marker").touch()
    freeze_docs_build = os.listdir(builddir)

    # to test creation of README.rst content needs to be written to file
    with open(readme, "w") as fout:
        fout.write(files.README_RST)

    pyaud.modules.make_docs()
    assert freeze_docs_build != os.listdir(builddir)


@pytest.mark.parametrize(
    "returncode,expected",
    [
        (0, "make_requirements\nmake_toc\nmake_whitelist\n"),
        (1, "make_requirements\n"),
    ],
    ids=["success", "fail"],
)
def test_make_files(
    monkeypatch: Any,
    call_status: Any,
    nocolorcapsys: Any,
    track_called: Any,
    returncode: int,
    expected: str,
) -> None:
    """Test correct commands are executed when running ``make_files``.

    :param monkeypatch:     Mock patch environment and attributes.
    :param call_status:     Patch function to return specific exit-code.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param track_called:    Decorate a mocked function to print what was
                            called.
    :param returncode:      Returncode to patch function with.
    :param expected:        Expected output.
    """
    file_funcs = "make_toc", "make_whitelist", "make_requirements"
    for file_func in file_funcs:
        monkeypatch.setattr(
            f"pyaud.modules.{file_func}",
            track_called(call_status(file_func, returncode)),
        )
    pyaud.modules.make_files()
    assert nocolorcapsys.stdout() == expected


def test_make_format() -> None:
    """Test ``make_format`` when successful and when it fails."""
    file = os.path.join(os.environ["PROJECT_DIR"], FILES)
    with open(file, "w") as fout:
        fout.write(files.UNFORMATTED)

    pyaud.utils.tree.append(file)
    with pytest.raises(pyaud.utils.PyAuditError):
        pyaud.modules.make_format()


def test_pipfile2req_commands(
    patch_sp_print_called: Any, nocolorcapsys: Any
) -> None:
    """Test that the correct commands are executed.

    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    """
    requirements = os.environ["PYAUD_REQUIREMENTS"]
    pipfile_lock = os.environ["PYAUD_PIPFILE_LOCK"]
    with open(pipfile_lock, "w") as fout:
        fout.write(files.PIPFILE_LOCK)

    patch_sp_print_called()
    pyaud.modules.make_requirements()
    out = nocolorcapsys.stdout()
    assert all(
        e in out
        for e in (
            f"Updating ``{requirements}``",
            f"<Subprocess (pipfile2req)> {pipfile_lock}",
            f"<Subprocess (pipfile2req)> {pipfile_lock} --dev",
            f"created ``{os.path.basename(requirements)}``",
        )
    )


def test_get_branch_unique() -> None:
    """Test that ``get_branch`` returns correct branch."""
    path = os.environ["PROJECT_DIR"]
    Path(path, FILES).touch()
    branch = datetime.datetime.now().strftime("%d%m%YT%H%M%S")
    with pyaud.utils.Git(path) as git:
        git.add(".", devnull=True)  # type: ignore
        git.commit("-m", INITIAL_COMMIT, devnull=True)  # type: ignore
        git.checkout("-b", branch, devnull=True)  # type: ignore
        assert pyaud.utils.get_branch() == branch


def test_get_branch_initial_commit() -> None:
    """Test that ``get_branch`` returns None.

    Test when run from a commit with no parent commits i.e. initial
    commit.
    """
    Path(os.environ["PYAUD_README_RST"]).touch()
    with pyaud.utils.Git(os.environ["PROJECT_DIR"]) as git:
        git.add(".")  # type: ignore
        git.commit("-m", INITIAL_COMMIT)  # type: ignore
        git.rev_list("--max-parents=0", "HEAD", capture=True)  # type: ignore
        git.checkout(git.stdout()[0])  # type: ignore

    assert pyaud.utils.get_branch() is None


@pytest.mark.parametrize(
    "exclude,expected",
    [
        ([], ""),
        (
            [".env_diff", "instance_diff", ".cache_diff"],
            "Removing .cache_diff\n"
            "Removing .env_diff\n"
            "Removing instance_diff\n",
        ),
    ],
    ids=["no-exclude", "exclude"],
)
def test_clean_exclude(
    main: Any, nocolorcapsys: Any, exclude: List[str], expected: str
) -> None:
    """Test clean with and without exclude parameters.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param exclude:         Files to exclude from ``git clean``.
    :param expected:        Expected output from ``pyaud clean``.
    """
    path = os.environ["PROJECT_DIR"]
    Path(path, FILES).touch()
    with pyaud.utils.Git(path) as git:
        git.init(devnull=True)  # type: ignore
        git.add(".")  # type: ignore
        git.commit("-m", "Initial commit", devnull=True)  # type: ignore

    for exclusion in exclude:
        Path(path, exclusion).touch()

    main("clean")
    assert nocolorcapsys.stdout() == expected


def test_git_context_no_artifact(tmp_path: Path) -> None:
    """Ensure that no dir remains if no action occurs.

    Test from inside created dir. This functionality exists for cloning
    directories while keeping ``Git``s context action intact.

    :param tmp_path: Create and return temporary directory.
    """
    tmprepo = os.path.join(tmp_path, "test_repo")
    with pyaud.utils.Git(tmprepo):

        # do nothing within repo but new dir is created in order for
        # context action of entering repo to work
        assert os.path.isdir(tmprepo)

    # ensure ``tmprepo`` has been removed
    assert not os.path.isdir(tmprepo)


def test_pipe_to_file() -> None:
    """Test that the ``Subprocess`` class correctly writes file.

    When the ``file`` keyword argument is used stdout should be piped to
    the filename provided.
    """
    project_dir = os.environ["PROJECT_DIR"]
    file = os.path.join(project_dir, FILES)
    with pyaud.utils.Git(project_dir) as git:
        git.init(file=file)  # type: ignore

    with open(file) as fin:
        assert (
            fin.read().strip()
            == "Reinitialized existing Git repository in {}".format(
                os.path.join(project_dir, f".git{os.sep}")
            )
        )


def test_del_item() -> None:
    """Test __delitem__ in ``Environ``."""
    os.environ["PYAUD_ITEM"] = "del this"
    assert "PYAUD_ITEM" in os.environ
    assert os.environ["PYAUD_ITEM"] == "del this"
    del os.environ["PYAUD_ITEM"]
    assert "PYAUD_ITEM" not in os.environ
    del os.environ["PYAUD_PKG"]
    assert "PYAUD_PKG" not in os.environ


def test_validate_env(validate_env: Any) -> None:
    """Ensure an error is raised.

    Tested for if the environment contains any remnants of the system's
    actual filepaths, and not just the filepaths contained within the
    /tmp directory.

    :param validate_env:    Execute the ``validate_env`` function
                            returned from this fixture.
    """
    real_tests = os.path.join(REAL_REPO, "tests")
    os.environ["PYAUD_TESTS"] = real_tests
    expected = f"environment not properly set: PYAUD_TESTS == {real_tests}"
    with pytest.raises(PyaudTestError) as err:
        validate_env()

    assert str(err.value) == expected


def test_find_package(tmpdir: Any, monkeypatch: Any) -> None:
    """Test error is raised if no Python file exists in project root.

    :param tmpdir:      Create and return a temporary  directory for
                        testing.
    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.undo()
    monkeypatch.setenv("PROJECT_DIR", os.path.join(tmpdir, REPO))
    with pytest.raises(EnvironmentError) as err:
        pyaud.environ.load_namespace()

    assert str(err.value) == "Unable to find a Python package"


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
    path = os.environ["PYAUD_TOC"]
    make_tree(
        os.environ["PROJECT_DIR"], {"docs": {os.path.basename(path): None}}
    )
    with pyaud.utils.HashCap(path) as cap:
        if change:
            with open(path, "w") as fin:
                fin.write("changed")

    assert cap.compare == expected


def test_readme_replace() -> None:
    """Test that ``LineSwitch`` properly edits a file."""
    path = os.environ["PYAUD_README_RST"]

    def _test_file_index(title: str, underline: str) -> None:
        with open(path) as fin:
            lines = fin.read().splitlines()

        assert lines[0] == title
        assert lines[1] == len(underline) * "="

    repo = "repo"
    readme = "README"
    repo_underline = len(repo) * "="
    readme_underline = len(readme) * "="
    with open(path, "w") as fout:
        fout.write(f"{repo}\n{repo_underline}\n")

    _test_file_index(repo, repo_underline)
    with pyaud.utils.LineSwitch(path, {0: readme, 1: readme_underline}):
        _test_file_index(readme, readme_underline)

    _test_file_index(repo, repo_underline)


@pytest.mark.parametrize(
    "make_relative_file,assert_relative_item,assert_true",
    [
        (FILES, FILES, True),
        (
            os.path.join("nested", "python", "file", FILES),
            os.path.join("nested"),
            True,
        ),
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
    project_dir = os.environ["PROJECT_DIR"]
    make_file = os.path.join(project_dir, make_relative_file)
    make_item = os.path.join(project_dir, assert_relative_item)
    dirname = os.path.dirname(make_file)
    if not os.path.isdir(dirname):
        os.makedirs(os.path.dirname(make_file))

    Path(make_file).touch()
    with pyaud.utils.Git(project_dir) as git:
        git.add(".")  # type: ignore

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
    project_dir = os.environ["PROJECT_DIR"]
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
    with open(os.path.join(project_dir, ".gitignore"), "w") as fout:
        fout.write("venv\n")

    pyaud.utils.tree.clear()
    pyaud.utils.tree.populate()
    assert set(pyaud.utils.tree.reduce()) == set()


def test_append_whitelist(
    nocolorcapsys: Any, patch_sp_print_called: Any
) -> None:
    """Test that whitelist file argument is appended ``vulture`` call.

    Test for when whitelist.py exists and is not appended if it does
    not, thus avoiding an error.

    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    """
    whitelist = os.environ["PYAUD_WHITELIST"]
    Path(os.environ["PROJECT_DIR"], FILES).touch()
    patch_sp_print_called()
    Path(whitelist).touch()
    pyaud.utils.tree.populate()
    pyaud.modules.make_unused()
    assert whitelist in nocolorcapsys.stdout()


def test_mypy_expected(patch_sp_print_called: Any, nocolorcapsys: Any) -> None:
    """Test that the ``mypy`` command is correctly called.

    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    """
    path = Path(os.environ["PROJECT_DIR"], FILES)
    pyaud.utils.tree.append(path)
    patch_sp_print_called()
    pyaud.modules.make_typecheck()
    assert (
        f"<Subprocess (mypy)> --ignore-missing-imports {path}"
        in nocolorcapsys.stdout()
    )


@pytest.mark.parametrize(
    "mapping,expected",
    [
        ({"tests": {}}, "No tests found"),
        ({"tests": {"test.py": None}}, "No tests found"),
        ({"tests": {"filename.py": None}}, "No tests found"),
        ({"tests": {"_test.py": None}}, "<Subprocess (pytest)>"),
        ({"tests": {"test_.py": None}}, "<Subprocess (pytest)>"),
        ({"tests": {"three_test.py": None}}, "<Subprocess (pytest)>"),
        ({"tests": {"test_four.py": None}}, "<Subprocess (pytest)>"),
    ],
    ids=(
        "tests",
        "tests/test.py",
        "tests/filename.py",
        "tests/test_.py",
        "tests/_test.py",
        "tests/three_test.py",
        "tests/test_four.py",
    ),
)
def test_pytest_is_tests(
    nocolorcapsys: Any,
    make_tree: Any,
    patch_sp_print_called: Any,
    mapping: Dict[str, Dict[str, Optional[str]]],
    expected: str,
) -> None:
    """Test that ``pytest`` is correctly called.

    Test that ``pytest`` is not called if:

        - there is a tests dir without tests
        - incorrect names within tests dir
        - no tests at all within tests dir.

    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    :param make_tree:               Create directory tree from dict
                                    mapping.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param mapping:                 Parametrized mappings.
    :param expected:                Expected stdout.
    """
    make_tree(os.environ["PROJECT_DIR"], mapping)
    patch_sp_print_called()
    pyaud.modules.make_tests()
    assert nocolorcapsys.stdout().strip() == expected


def test_make_toc(patch_sp_print_called: Any, make_tree: Any) -> None:
    """Test that the default toc file is edited correctly.

    Ensure additional files generated by ``sphinx-api`` doc are removed.

    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param make_tree:               Create directory tree from dict
                                    mapping.
    """
    path = os.environ["PYAUD_TOC"]
    modules = "modules.rst"
    make_tree(
        os.environ["PROJECT_DIR"], {"docs": {modules: None, CONFPY: None}}
    )
    with open(path, "w") as fout:
        assert fout.write(files.DEFAULT_TOC)

    patch_sp_print_called()
    pyaud.modules.make_toc()
    with open(path) as fin:
        assert fin.read() == files.ALTERED_TOC

    assert not os.path.isfile(os.path.join(os.environ["PYAUD_DOCS"], modules))


def test_make_requirements(patch_sp_output: Any, nocolorcapsys: Any) -> None:
    """Test that requirements.txt file is correctly edited.

     Tested for use with ``pipfile2req``.

    :param patch_sp_output: Patch ``Subprocess`` so that ``call`` sends
                            expected stdout out to self.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    path = os.environ["PYAUD_REQUIREMENTS"]
    with open(os.environ["PYAUD_PIPFILE_LOCK"], "w") as fout:
        fout.write(files.PIPFILE_LOCK)

    patch_sp_output(files.PIPFILE2REQ_PROD, files.PIPFILE2REQ_DEV)
    pyaud.modules.make_requirements()
    assert nocolorcapsys.stdout() == (
        f"Updating ``{path}``\ncreated ``{os.path.basename(path)}``\n"
    )
    with open(path) as fin:
        assert fin.read() == files.REQUIREMENTS


def test_make_whitelist(
    patch_sp_output: Any, nocolorcapsys: Any, make_tree: Any
) -> None:
    """Test a whitelist.py file is created properly.

    Test for when piping data from ``vulture --make-whitelist``.

    :param patch_sp_output:     Patch ``Subprocess`` so that ``call``
                                sends expected stdout out to self.
    :param nocolorcapsys:       Capture system output while stripping
                                ANSI color codes.
    :param make_tree:           Create directory tree from dict mapping.
    """
    project_dir = os.environ["PROJECT_DIR"]
    whitelist = os.environ["PYAUD_WHITELIST"]
    make_tree(
        project_dir,
        {
            "tests": {"conftest.py": None, FILES: None},
            "pyaud": {"src": {"__init__.py": None, "modules.py": None}},
        },
    )
    with pyaud.utils.Git(project_dir) as git:
        git.init(devnull=True)  # type: ignore
        git.add(".")  # type: ignore

    pyaud.utils.tree.populate()
    patch_sp_output(
        files.Whitelist.be8a443_tests, files.Whitelist.be8a443_pyaud
    )
    pyaud.modules.make_whitelist()
    assert nocolorcapsys.stdout() == (
        "Updating ``{}``\ncreated ``{}``\n".format(
            whitelist, os.path.basename(whitelist)
        )
    )
    with open(whitelist) as fin:
        assert fin.read() == files.Whitelist.be8a443_all()


def test_parser(
    monkeypatch: Any,
    nocolorcapsys: Any,
    track_called: Any,
    call_status: Any,
    main: Any,
) -> None:
    """Test that passed arguments call the selected module correctly.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param track_called:    Decorate a mocked function to print what was
                            called.
    :param call_status:     Patch function to return specific exit-code.
    :param main:            Patch package entry point.
    """
    calls = [
        "audit",
        "clean",
        "coverage",
        "deploy",
        "deploy-cov",
        "deploy-docs",
        "docs",
        "files",
        "format",
        "format-docs",
        "format-str",
        "lint",
        "requirements",
        "tests",
        "toc",
        "typecheck",
        "unused",
        "whitelist",
    ]
    monkeypatch.setattr(
        "pyaud.MODULES",
        {
            k: track_called(call_status(v.__name__, 0))
            for k, v in pyaud.MODULES.items()
        },
    )
    for call in calls:
        main(call)
        module = f"make_{call.replace('-', '_')}"
        assert nocolorcapsys.stdout().strip() == module


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
    path = os.path.join(tmp_path, REPO)
    with pyaud.utils.Git(path) as git:
        git.clone(  # type: ignore
            "--depth", "1", "--branch", "v1.1.0", REAL_REPO
        )

    assert (
        nocolorcapsys.stdout().strip()
        == "<Git (git)> clone --depth 1 --branch v1.1.0 {} {}".format(
            REAL_REPO, path
        )
    )


def test_pylint_colorized(capsys: Any) -> None:
    """Test that color codes are produced with ``process.PIPE``.

    Test ``pylint --output-format=colorized``. If ``colorama`` is
    installed and a process calls ``colorama.init()`` a process pipe
    will be stripped. Using environment variable ``PYCHARM_HOSTED`` for
    now as a workaround as this voids this action.

    :param capsys: Capture sys output.
    """
    path = os.path.join(os.environ["PROJECT_DIR"], FILES)
    with open(path, "w") as fout:
        fout.write("import this_package_does_not_exist")

    pyaud.utils.tree.append(path)
    pyaud.modules.make_lint(suppress=True)
    output = capsys.readouterr()[0]
    assert all(
        i in output
        for i in ["\x1b[7;33m", "\x1b[0m", "\x1b[1m", "\x1b[1;31m", "\x1b[35m"]
    )


@pytest.mark.parametrize(
    "iskey,key",
    [
        (False, datetime.datetime.now().strftime("%d%m%YT%H%M%S")),
        (True, "PROJECT_DIR"),
    ],
    ids=["iskey", "nokey"],
)
def test_temp_env_var(iskey: bool, key: str) -> None:
    """Test ``TempEnvVar`` sets environment variables.

    Ensure class leaves everything as it originally was once the context
    action is complete.

    :param iskey:   Assert key is or is not already in ``os.environ.``
    :param key:     Dictionary key to test with.
    """
    if iskey:
        assert key in os.environ
    else:
        assert key not in os.environ

    with pyaud.environ.TempEnvVar(os.environ, **{key: "True"}):
        assert key in os.environ and os.environ[key] == "True"

    if iskey:
        assert key in os.environ
    else:
        assert key not in os.environ


@pytest.mark.parametrize("default", [CRITICAL, ERROR, WARNING, INFO, DEBUG])
@pytest.mark.parametrize("flag", ["", "-v", "-vv", "-vvv", "-vvvv"])
def test_loglevel(main: Any, default: str, flag: str) -> None:
    """Test the right loglevel is set when parsing the commandline.

    :param main:    Patch package entry point.
    :param default: Default loglevel configuration.
    :param flag:    Verbosity level commandline flag.
    """
    levels = {
        "": [CRITICAL, ERROR, WARNING, INFO, DEBUG],
        "-v": [ERROR, WARNING, INFO, DEBUG, DEBUG],
        "-vv": [WARNING, INFO, DEBUG, DEBUG, DEBUG],
        "-vvv": [INFO, DEBUG, DEBUG, DEBUG, DEBUG],
        "-vvvv": [DEBUG, DEBUG, DEBUG, DEBUG, DEBUG],
    }
    pyaud.config.toml["logging"]["root"]["level"] = default
    with open(
        os.path.join(pyaud.config.CONFIGDIR, pyaud.config.TOMLFILE), "w"
    ) as fout:
        pyaud.config.toml.dump(fout)

    pyaud.config.configure_global()
    main("unused", flag)
    assert (
        logging.getLevelName(logging.root.level)
        == levels[flag][levels[""].index(default)]
    )


def test_isort_imports(nocolorcapsys: Any) -> None:
    """Test isort properly sorts file imports.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    path = os.path.join(os.environ["PROJECT_DIR"], FILES)
    with open(path, "w") as fout:
        fout.write(files.IMPORTS_UNSORTED)

    pyaud.utils.tree.append(path)
    with pytest.raises(pyaud.utils.PyAuditError):
        pyaud.modules.make_imports()

    with open(path) as fin:
        assert (
            files.IMPORTS_SORTED.splitlines()[1:]
            == fin.read().splitlines()[:20]
        )

    pyaud.modules.make_imports()
    out = nocolorcapsys.stdout()
    assert all(i in out for i in (f"Fixing {path}", NO_ISSUES))


def test_readme(main: Any, nocolorcapsys: Any) -> None:
    """Test standard README and return values.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    main("readme")
    assert (
        nocolorcapsys.stdout().strip() == "No README.rst found in project root"
    )
    with open(os.environ["PYAUD_README_RST"], "w") as fout:
        fout.write(files.CODE_BLOCK_TEMPLATE)

    main("readme")
    assert (
        "\n".join([i.strip() for i in nocolorcapsys.stdout().splitlines()])
        == files.CODE_BLOCK_EXPECTED
    )


@pytest.mark.parametrize(
    "module,process,content",
    [
        ("format", "black", files.UNFORMATTED),
        ("imports", "make_imports", files.IMPORTS_UNSORTED),
        ("format-str", "flynt", files.FORMAT_STR_FUNCS_PRE),
        ("format-docs", "docformatter", files.DOCFORMATTER_EXAMPLE),
    ],
    ids=["format", "imports", "format-str", "format-docs"],
)
def test_py_audit_error(
    main: Any, make_tree: Any, module: str, process: str, content: str
) -> None:
    """Test ``PyAuditError`` message.

    :param main:        Patch package entry point.
    :param make_tree:   Create directory tree from dict mapping.
    :param module:      [<module>].__name__.
    :param process:     Subprocess being called.
    :param content:     Content to write to file.
    """
    project_dir = os.environ["PROJECT_DIR"]
    file = os.path.join(project_dir, FILES)
    make_tree(project_dir, {"tests": {"_test.py": None}, REPO: {INIT: None}})
    with open(file, "w") as fout:
        fout.write(content)

    with pyaud.utils.Git(project_dir) as git:
        git.add(".")  # type: ignore

    pyaud.utils.tree.populate()
    with pytest.raises(pyaud.utils.PyAuditError) as err:
        main(module)

    stderr = str(err.value)
    assert all(
        i in stderr
        for i in (process, os.path.basename(file), "did not pass all checks")
    )
    assert "Path" not in stderr


def test_format_str(main: Any, nocolorcapsys: Any) -> None:
    """Test failing audit when f-strings can be created with ``flynt``.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    path = os.environ["PROJECT_DIR"]
    with open(os.path.join(path, FILES), "w") as fout:
        fout.write(files.FORMAT_STR_FUNCS_PRE)

    with pyaud.utils.Git(path) as git:
        git.init()  # type: ignore
        git.add(".")  # type: ignore

    pyaud.utils.tree.populate()
    with pytest.raises(pyaud.utils.PyAuditError):
        main("format-str")

    expected = (
        "Files modified:                            1",
        "Character count reduction:                 10 (2.04%)",
        "`.format(...)` calls attempted:            1/1 (100.0%)",
        "String concatenations attempted:           1/1 (100.0%)",
        "F-string expressions created:              2",
    )
    out = nocolorcapsys.stdout()
    assert all(i in out for i in expected)
    with open(os.path.join(path, FILES)) as fin:
        assert fin.read() == files.FORMAT_STR_FUNCS_POST


def test_del_key_in_context():
    """Confirm there is no error raised when deleting temp key-value."""
    obj = {}
    with pyaud.environ.TempEnvVar(obj, key="value"):
        assert obj["key"] == "value"
        del obj["key"]


@pytest.mark.usefixtures("init_remote")
def test_deploy_not_master(monkeypatch: Any, nocolorcapsys: Any) -> None:
    """Test that deployment is skipped when branch is not ``master``.

    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    monkeypatch.setattr("pyaud.modules.get_branch", lambda: "not_master")
    pyaud.modules.make_deploy_docs()
    out = [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    assert all(
        i in out for i in ["Documentation not for master", PUSHING_SKIPPED]
    )


@pytest.mark.usefixtures("init_remote")
def test_deploy_master_not_set(monkeypatch: Any, nocolorcapsys: Any) -> None:
    """Test correct notification is displayed.

    Test for when essential environment variables are not set in
    ``master``.

    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    monkeypatch.setenv("PYAUD_GH_NAME", "")
    monkeypatch.setenv("PYAUD_GH_EMAIL", "")
    monkeypatch.setenv("PYAUD_GH_TOKEN", "")
    pyaud.modules.make_deploy_docs()
    out = nocolorcapsys.stdout().splitlines()
    assert all(
        [
            i in out
            for i in [
                "The following is not set:",
                "- PYAUD_GH_NAME",
                "- PYAUD_GH_EMAIL",
                "- PYAUD_GH_TOKEN",
                PUSHING_SKIPPED,
            ]
        ]
    )


@pytest.mark.usefixtures("init_remote")
def test_deploy_master(monkeypatch: Any, nocolorcapsys: Any) -> None:
    """Test docs are properly deployed.

    Test for when environment variables are set and checked out at
    ``master``.

    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    path = os.environ["PYAUD_README_RST"]
    monkeypatch.setattr(
        "pyaud.modules.make_docs",
        lambda *_, **__: os.makedirs(
            os.path.join(os.environ["BUILDDIR"], "html")
        ),
    )
    Path(path).touch()  # force stash
    with pyaud.utils.Git(os.environ["PROJECT_DIR"]) as git:
        git.add(".")  # type: ignore
        git.commit("-m", INITIAL_COMMIT, devnull=True)  # type: ignore

    with open(path, "w") as fout:
        fout.write(files.README_RST)

    pyaud.modules.make_deploy_docs()
    out = nocolorcapsys.stdout().splitlines()
    assert all(
        i in out
        for i in [
            "Pushing updated documentation",
            "Documentation Successfully deployed",
        ]
    )
    pyaud.modules.make_deploy_docs()
    out = nocolorcapsys.stdout().splitlines()
    assert all(
        i in out
        for i in [
            "No difference between local branch and remote",
            PUSHING_SKIPPED,
        ]
    )


@pytest.mark.parametrize(
    "rounds,expected",
    [
        (
            1,
            [
                "Pushing updated documentation",
                "Documentation Successfully deployed",
            ],
        ),
        (
            2,
            ["No difference between local branch and remote", PUSHING_SKIPPED],
        ),
    ],
    ids=["stashed", "multi"],
)
@pytest.mark.usefixtures("init_remote")
def test_deploy_master_param(
    monkeypatch: Any, nocolorcapsys: Any, rounds: int, expected: List[str]
) -> None:
    """Check that nothing happens when not checkout at at master.

    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param rounds:          How many times ``make_deploy_docs`` needs to
                            be run.
    :param expected:        Expected stdout result.
    """
    path = os.environ["PROJECT_DIR"]
    monkeypatch.setattr(
        "pyaud.modules.make_docs",
        lambda *_, **__: os.makedirs(
            os.path.join(os.environ["BUILDDIR"], "html")
        ),
    )
    with open(os.environ["PYAUD_README_RST"], "w") as fout:
        fout.write(files.README_RST)

    Path(path, FILES).touch()
    with pyaud.utils.Git(path) as git:
        git.add(".", devnull=True)  # type: ignore
        git.commit("-m", INITIAL_COMMIT, devnull=True)  # type: ignore

    for _ in range(rounds):
        pyaud.modules.make_deploy_docs()

    out = [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    assert all(i in out for i in expected)


def test_deploy_cov_report_token(
    monkeypatch: Any, nocolorcapsys: Any, patch_sp_print_called: Any
) -> None:
    """Test ``make_deploy_cov`` when ``CODECOV_TOKEN`` is set.

    Test for when ``CODECOV_TOKEN`` is set and a coverage.xml file
    exists.

    :param monkeypatch:             Mock patch environment and
                                    attributes.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    """
    Path(os.environ["PYAUD_COVERAGE_XML"]).touch()
    patch_sp_print_called()
    monkeypatch.setenv("CODECOV_TOKEN", "token")
    pyaud.modules.make_deploy_cov()
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["codecov", "--file"])


def test_deploy_cov_no_token(nocolorcapsys: Any) -> None:
    """Test ``make_deploy_cov``.

    Test for when ``CODECOV_TOKEN`` when only a coverage.xml file
    exists.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    Path(os.environ["PYAUD_COVERAGE_XML"]).touch()
    pyaud.modules.make_deploy_cov()
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["CODECOV_TOKEN not set"])


def test_deploy_cov_no_report_token(nocolorcapsys: Any) -> None:
    """Test ``make_deploy_cov``.

     Test for when ``CODECOV_TOKEN`` is not set and a coverage.xml file
     does not. exist.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    pyaud.modules.make_deploy_cov()
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["No coverage report found"])


def test_make_format_success(
    nocolorcapsys: Any, patch_sp_print_called: Any
) -> None:
    """Test ``make_format`` when successful.

    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    """
    pyaud.utils.tree.append(os.path.join(os.environ["PROJECT_DIR"], FILES))
    patch_sp_print_called()
    pyaud.modules.make_format()
    nocolorcapsys.readouterr()


@pytest.mark.parametrize(
    "arg,index,expected",
    [
        ("", 0, pyaud.MODULES.keys()),
        ("audit", 0, ("audit -- Run all modules for complete package audit",)),
        ("all", 0, pyaud.MODULES.keys()),
        ("not-a-module", 1, ("No such module: not-a-module",)),
    ],
    ids=["no-pos", "module", "all-modules", "invalid-pos"],
)
def test_help(
    main: Any,
    nocolorcapsys: Any,
    arg: str,
    index: int,
    expected: Tuple[str, ...],
) -> None:
    """Test expected output for ``pyaud modules``.

    Test call with no arguments, with ``all``, and when querying a
    non-existent module.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param arg:             Positional argument for ```pyaud modules``.
    :param expected:        Expected result when calling command.
    """
    with pytest.raises(SystemExit):
        main("modules", arg)

    # index 0 returns stdout from ``readouterr`` and 1 returns stderr
    assert any(i in nocolorcapsys.readouterr()[index] for i in expected)


def test_make_format_docs_fail() -> None:
    """Test ``make_format`` when it fails.

    Ensure process fails when unformatted docstrings are found.
    """
    file = os.path.join(os.environ["PROJECT_DIR"], FILES)
    with open(file, "w") as fout:
        fout.write(files.DOCFORMATTER_EXAMPLE)

    pyaud.utils.tree.append(file)
    with pytest.raises(pyaud.utils.PyAuditError):
        pyaud.modules.make_format_docs()


def test_make_format_docs_suppress(nocolorcapsys: Any) -> None:
    """Test ``make_format`` when running with ``-s/--suppress``.

    Ensure process announces it failed but does not actually return a
    non-zero exit-status.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    path = os.path.join(os.environ["PROJECT_DIR"], FILES)
    with open(path, "w") as fout:
        fout.write(files.DOCFORMATTER_EXAMPLE)

    pyaud.utils.tree.append(path)
    pyaud.modules.make_format_docs(suppress=True)
    assert (
        nocolorcapsys.stderr().strip()
        == "Failed: returned non-zero exit status 3"
    )


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
    assert "PROJECT_DIR" in os.environ
    project_dir = os.environ["PROJECT_DIR"]
    with pyaud.environ.TempEnvVar(os.environ, PROJECT_DIR="True"):
        assert (
            "PROJECT_DIR" in os.environ and os.environ["PROJECT_DIR"] == "True"
        )
    assert (
        "PROJECT_DIR" in os.environ
        and os.environ["PROJECT_DIR"] == project_dir
    )


@pytest.mark.usefixtures("init_remote")
def test_gen_default_remote(monkeypatch: Any) -> None:
    """Test ``PYAUD_GH_REMOTE`` is properly loaded from .env variables.

    :param monkeypatch: Mock patch environment and attributes.
    """
    with pyaud.utils.Git(os.environ["PYAUD_GH_REMOTE"]) as git:
        git.init("--bare", ".", devnull=True)  # type: ignore

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
    test_default: Dict[Any, Any] = copy.deepcopy(pyaud.config.DEFAULT_CONFIG)
    assert dict(pyaud.config.toml) == test_default
    project_rc = os.path.join(os.environ["PROJECT_DIR"], pyaud.config.RCFILE)
    pyproject_path = os.path.join(
        os.environ["PROJECT_DIR"], pyaud.config.PYPROJECT
    )

    # instantiate a new dict object
    # =============================
    # preserve the test default config
    home_rcfile = dict(test_default)
    home_rcfile["clean"]["exclude"].append("_build")
    home_rcfile["logging"]["handlers"]["default"].update(
        {"class": "logging.handlers.StreamHandler"}
    )
    home_rcfile["logging"]["version"] = 2
    with open(
        os.path.join(os.path.expanduser("~"), pyaud.config.RCFILE), "w"
    ) as fout:
        pyaud.config.toml.dump(fout, home_rcfile)

    # reset the dict to the test default
    # ==================================
    # test the the changes made to clean are inherited through the
    # config hierarchy but not configured in this dict
    project_rcfile = dict(test_default)
    project_rcfile["logging"]["version"] = 3
    with open(os.path.join(project_rc), "w") as fout:
        pyaud.config.toml.dump(fout, project_rcfile)

    # load "$HOME/.pyaudrc" and then "$PROJECT_DIR/.pyaudrc"
    # ======================================================
    # override "$HOME/.pyaudrc"
    pyaud.config.load_config()
    subtotal: Dict[str, Any] = dict(home_rcfile)
    subtotal["logging"]["version"] = 3
    subtotal["logging"]["handlers"]["default"][
        "filename"
    ] = os.path.expanduser(
        subtotal["logging"]["handlers"]["default"]["filename"]
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
    opt_rc = os.path.join(os.environ["PROJECT_DIR"], "opt_rc")
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
    tomlfile = os.path.join(pyaud.config.CONFIGDIR, pyaud.config.TOMLFILE)
    inifile = os.path.join(pyaud.config.CONFIGDIR, f"{pyaud.__name__}.ini")
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


def test_make_generate_rcfile(nocolorcapsys: Any):
    """Test for correct output when running ``generate-rcfile``.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    pyaud.modules.make_generate_rcfile()
    assert (
        nocolorcapsys.stdout().strip()
        == pyaud.config.toml.dumps(pyaud.config.DEFAULT_CONFIG).strip()
    )


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
    with open(
        os.path.join(pyaud.config.CONFIGDIR, pyaud.config.TOMLFILE)
    ) as fin:
        pyaud.config.toml.load(fin)  # base key-values

    assert dict(pyaud.config.toml) == pyaud.config.DEFAULT_CONFIG
    with open(
        os.path.join(os.path.expanduser("~"), pyaud.config.RCFILE), "w"
    ) as fout:
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
    configfile = os.path.join(pyaud.config.CONFIGDIR, pyaud.config.TOMLFILE)
    backupfile = os.path.join(
        pyaud.config.CONFIGDIR, f".{pyaud.config.TOMLFILE}.bak"
    )

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
    assert not os.path.isfile(backupfile)

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
    assert os.path.isfile(backupfile)

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
