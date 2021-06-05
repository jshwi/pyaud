"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments
import datetime
import filecmp
import inspect
import os
import pathlib

import pytest

import pyaud
import tests

NAME = "pyaud"
FILES = "file.py"
PUSHING_SKIPPED = "Pushing skipped"


def test_no_files_found(nocolorcapsys):
    """Test the correct output is produced when no file exists when
    compiling the Python files list with ``get_pyfiles``.

    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    pyaud.modules.make_typecheck()
    assert nocolorcapsys.stdout().strip() == "No files found"


@pytest.mark.usefixtures("make_test_file")
@pytest.mark.parametrize(
    "module,expected",
    [
        ("make_unused", "Success: no issues found in 1 source files"),
        ("make_tests", "Success: no issues found in 20 tests"),
        ("make_docs", "Build successful"),
    ],
    ids=["files", "tests", "build"],
)
def test_success_output(
    nocolorcapsys,
    monkeypatch,
    make_project_tree,
    call_status,
    module,
    expected,
):
    """Test the output returned from the ``pyaud.check_command``
    decorator matches the function being used. Changed the parametrized
    ``func`` __name__ to match the mocked module.

    :param nocolorcapsys:       ``capsys`` without ANSI color codes.
    :param monkeypatch:         ``pytest`` fixture for mocking
                                attributes.
    :param make_project_tree:   Make directory structure.
    :param call_status:         Patch function to return specific
                                exit-code.
    :param module:              Function to test.
    :param expected:            Expected function output
    """
    make_project_tree.docs_conf()
    pyaud.pyitems.get_files()
    monkeypatch.setattr(
        pyaud.modules, module, pyaud.check_command(call_status(module))
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
def test_write_command(monkeypatch, nocolorcapsys, contents, expected):
    """Test the ``@write_command`` decorator to correctly document when
    a file has been created, updated or whether no changes needed to be
    made.

    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param monkeypatch:     ``pytest`` fixture for mocking attributes.
    :param contents:        Content to write to file.
    :param expected:        Expected output.
    """
    write_command = pyaud.write_command("WHITELIST")
    for content in contents:

        def mock_write_whitelist():
            with open(pyaud.environ.env["WHITELIST"], "w") as fout:
                fout.write(content)  # pylint: disable=cell-var-from-loop

        monkeypatch.setattr(
            pyaud.modules,
            "make_whitelist",
            write_command(mock_write_whitelist),
        )
        pyaud.modules.make_whitelist()

    assert expected in nocolorcapsys.stdout()


def test_make_audit_error(nocolorcapsys, patch_sp_returncode):
    """Test errors are handled correctly when running ``pyaud audit``.

    :param nocolorcapsys:       ``capsys`` without ANSI color codes.
    :param patch_sp_returncode: Patch ``pyaud.Subprocess`` to return
                                specific exit-code.
    """
    patch_sp_returncode(1)
    pathlib.Path(pyaud.environ.env["PROJECT_DIR"], "python_file.py").touch()
    pyaud.pyitems.get_files()
    with pytest.raises(pyaud.PyaudSubprocessError):
        pyaud.modules.make_audit()

    assert nocolorcapsys.stdout().strip() == "pyaud format"


def test_call_coverage_xml(monkeypatch, patch_sp_call, nocolorcapsys):
    """Test ``coverage xml`` is called after successful test run.

    :param monkeypatch:     ``pytest`` fixture for mocking attributes.
    :param patch_sp_call:   Patch ``pyaud.Subprocess.call``.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """

    def make_tests(*_):
        return 0

    patch_sp_call()
    monkeypatch.setattr(pyaud.modules, "make_tests", make_tests)
    pyaud.modules.make_coverage()
    assert nocolorcapsys.stdout().strip() == "coverage xml"


def test_make_deploy_all(call_status, monkeypatch, nocolorcapsys):
    """Test the correct commands are run when running ``pyaud deploy``.

    :param call_status:     Patch function to return specific exit-code.
    :param monkeypatch:     ``pytest`` fixture for mocking attributes.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    deploy_modules = ["make_deploy_cov", "make_deploy_docs"]
    for deploy_module in deploy_modules:
        mockreturn = call_status(deploy_module, 0)
        monkeypatch.setattr(pyaud.modules, deploy_module, mockreturn)

    pyaud.modules.make_deploy()
    out = nocolorcapsys.stdout().splitlines()
    for deploy_module in deploy_modules:
        assert (
            deploy_module.replace("make_", NAME + " ").replace("_", "-") in out
        )


def test_make_deploy_all_fail(call_status, monkeypatch, nocolorcapsys):
    """Test ``pyaud deploy`` fails correctly when encountering an
    error.

    :param call_status:     Patch function to return specific exit-code.
    :param monkeypatch:     ``pytest`` fixture for mocking attributes.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    deploy_module = "make_deploy_docs"
    mockreturn = call_status(deploy_module, 1)
    monkeypatch.setattr(pyaud.modules, deploy_module, mockreturn)

    pyaud.modules.make_deploy()
    out = nocolorcapsys.stdout().splitlines()
    assert deploy_module.replace("make_", NAME + " ").replace("_", "-") in out


def test_make_docs_no_docs(nocolorcapsys):
    """Test correct message is produced when running ``pyaud docs``
    when no docs are present.

    :param nocolorcapsys: ``capsys`` without ANSI color codes.
    """
    pathlib.Path(pyaud.environ.env["PROJECT_DIR"], FILES).touch()
    pyaud.modules.make_docs()
    assert nocolorcapsys.stdout() == "No docs found\n"


@pytest.mark.usefixtures("make_python_file")
def test_suppress(nocolorcapsys, monkeypatch, call_status, make_project_tree):
    """Test that the audit still makes it to the end when errors are
    raised but ``--suppress`` is passed to the commandline.

    :param nocolorcapsys:       ``capsys`` without ANSI color codes.
    :param monkeypatch:         ``pytest`` fixture for mocking
                                attributes.
    :param call_status:         Patch function to return specific
                                exit-code.
    :param make_project_tree:   Make directory structure.
    """
    make_project_tree.docs_conf()
    pyaud.pyitems.get_files()
    audit_modules = [
        "make_format",
        "make_imports",
        "make_typecheck",
        "make_unused",
        "make_lint",
        "make_coverage",
        "make_docs",
    ]

    audit_count = len(audit_modules)
    for audit_module in audit_modules:
        mockreturn = call_status(audit_module, 1)
        monkeypatch.setattr(
            pyaud.modules, audit_module, pyaud.check_command(mockreturn)
        )

    monkeypatch.setenv("PYAUD_TEST_SUPPRESS", "True")
    pyaud.modules.make_audit()
    errs = nocolorcapsys.stderr().splitlines()
    total = len(
        [e for e in errs if "Failed: returned non-zero exit status" in e]
    )
    assert total == audit_count


@pytest.mark.usefixtures("mock_make_docs")
@pytest.mark.parametrize(
    (
        "gh_name",
        "gh_email",
        "gh_token",
        "branch",
        "working_tree_clean",
        "deploy_twice",
        "test_id",
    ),
    [
        (None, None, None, "not_master", True, False, "not_master"),
        (None, None, None, "master", True, False, "master_not_set"),
        (
            "jshwi",
            "stephen@jshwisolutions.com",
            "token",
            "master",
            True,
            False,
            "master",
        ),
        (
            "jshwi",
            "stephen@jshwisolutions.com",
            "token",
            "master",
            False,
            False,
            "master_stashed",
        ),
        (
            "jshwi",
            "stephen@jshwisolutions.com",
            "token",
            "master",
            False,
            True,
            "master_twice",
        ),
    ],
    ids=(
        "not_master",
        "master_not_set",
        "master",
        "master_stashed",
        "master_twice",
    ),  # pylint: disable=too-many-locals
)
def test_deploy_docs_branch(
    nocolorcapsys,
    monkeypatch,
    gh_name,
    gh_email,
    gh_token,
    branch,
    working_tree_clean,
    deploy_twice,
    make_deploy_docs_env,
    mock_remote_origin,
    test_id,
):
    """Check that nothing happens when not checkout at at master.

    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param branch:          Test's current branch.
    """
    base_method = pyaud.Subprocess.run
    expected = [
        "git init",
        "git add .",
        "git commit -m Initial commit",
        "git commit -m empty commit",
        "git remote add origin origin",
        "git diff-index --cached HEAD",
        "git rev-list --max-parents=0 HEAD",
        "git checkout --orphan gh-pages",
        "git config --global user.name jshwi",
        "git config --global user.email stephen@jshwisolutions.com",
        "git rm -rf .",
        "git clean -fdx --exclude=html",
        'git commit -m "[ci skip] Publishes updated documentation"',
        "git remote rm origin",
        f"git remote add origin {mock_remote_origin}",
        "git fetch",
        "git checkout master",
        "git branch -D gh-pages",
    ]

    def run(self, exe, *args, **kwargs):
        print(f"{exe} {' '.join(args)}")
        base_method(self, exe, *args, **kwargs)

    monkeypatch.setattr(pyaud.Subprocess, "run", run)
    pyaud.environ.env["GH_NAME"] = gh_name
    pyaud.environ.env["GH_EMAIL"] = gh_email
    pyaud.environ.env["GH_TOKEN"] = gh_token
    pyaud.environ.env["BRANCH"] = branch
    if gh_name and gh_email and gh_token:
        make_deploy_docs_env()

    if not working_tree_clean:
        pathlib.Path(pyaud.environ.env["PROJECT_DIR"], "files.py").touch()

    pyaud.modules.make_deploy_docs(url=mock_remote_origin)
    if deploy_twice:
        pyaud.modules.make_deploy_docs(url=mock_remote_origin)

    if test_id == "master":
        expected.extend(
            [
                "Pushing updated documentation",
                "Documentation Successfully deployed",
            ]
        )

    elif test_id == "master_twice":
        expected.extend(
            [
                "Pushing updated documentation",
                "Documentation Successfully deployed",
                "git diff gh-pages origin/gh-pages",
                "No difference between local branch and remote",
                PUSHING_SKIPPED,
            ]
        )

    elif test_id == "master_stashed":
        expected.extend(["git stash", "git stash pop"])

    elif test_id == "master_not_set":
        expected = [
            "The following is not set:",
            "- GH_NAME",
            "- GH_EMAIL",
            "- GH_TOKEN",
            "",
            PUSHING_SKIPPED,
        ]

    elif test_id == "not_master":
        expected = ["Documentation not for master", PUSHING_SKIPPED]

    out_list = [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    for expect in expected:
        assert expect in out_list


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
    monkeypatch, nocolorcapsys, main, call_status, args, add, first, last
):
    """Test that the correct functions are called when using the
    ``make_audit`` meta function.

    :param monkeypatch:     ``pytest`` fixture for mocking attributes.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param main:            Fixture for mocking ``pyaud.main``
    :param call_status:     Patch function to return specific exit-code.
    :param args:            Arguments for ``pyaud audit``.
    :param add:             Function to add to the ``audit_modules``
                            list
    :param first:           Expected first function executed.
    :param last:            Expected last function executed.
    """
    audit_modules = [
        "make_format",
        "make_typecheck",
        "make_unused",
        "make_lint",
        "make_coverage",
        "make_docs",
    ]
    audit_modules.extend(add)
    for audit_module in audit_modules:
        monkeypatch.setattr(
            pyaud.modules, audit_module, call_status(audit_module)
        )

    main("audit", *args)
    output = [i for i in nocolorcapsys.stdout().splitlines() if i != ""]
    expected = [i.replace("make_", NAME + " ") for i in audit_modules]
    assert all([i in output for i in expected])
    assert output[0] == first
    assert output[-1] == last


def test_coverage_no_tests(nocolorcapsys):
    """Ensure the correct message is displayed if ``pytest`` could not
    find a valid test folder.

    :param nocolorcapsys: ``capsys`` without ANSI color codes.
    """
    pyaud.modules.make_coverage()
    assert nocolorcapsys.stdout().strip() == (
        "No tests found\nNo coverage to report"
    )


@pytest.mark.parametrize(
    "is_report,is_token,expected",
    [
        (True, True, ["codecov", "--file", "--token", "token"]),
        (True, False, ["CODECOV_TOKEN not set"]),
        (False, False, ["No coverage report found"]),
    ],
    ids=["report_token", "no_token", "no_report_token"],
)
def test_deploy_cov(
    monkeypatch, nocolorcapsys, patch_sp_call, is_report, is_token, expected
):
    """Test ``make_deploy_cov`` when ``CODECOV_TOKEN`` is set and a
    coverage.xml file exists, when only a coverage.xml file exists and
    when ``CODECOV_TOKEN`` is not set and a coverage.xml file does not
    exist.

    :param monkeypatch:     ``pytest`` fixture for mocking attributes.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param patch_sp_call:   Patch ``pyaud.Subprocess.call``.
    :param is_report:       Coverage report exists: True or False.
    :param is_token:        ``CODECOV_TOKEN`` has been set: True or
                            False
    :param expected:        Expected output.
    """
    if is_report:
        pathlib.Path(pyaud.environ.env["COVERAGE_XML"]).touch()

    if is_token:
        patch_sp_call()
        monkeypatch.setenv("PYAUD_TEST_CODECOV_TOKEN", "token")

    pyaud.modules.make_deploy_cov()
    out = nocolorcapsys.stdout()
    assert all(e in out for e in expected)


def test_make_docs_toc_fail(
    nocolorcapsys, patch_sp_returncode, make_project_tree
):
    """Test that the correct error message is produced and the process
    stops when ``make_toc`` fails before running the main ``make_docs``
    process.

    :param nocolorcapsys:       ``capsys`` without ANSI color codes.
    :param patch_sp_returncode: Patch ``pyaud.Subprocess`` to return
                                specific exit-code.
    :param make_project_tree:   Make directory structure.
    """
    make_project_tree.docs_conf()
    patch_sp_returncode(1)
    with pytest.raises(pyaud.PyaudSubprocessError) as err:
        pyaud.modules.make_docs()

    assert str(err.value) == (
        "Command "
        "'sphinx-apidoc "
        "-o "
        + pyaud.environ.env["DOCS"]
        + " "
        + pyaud.environ.env["PKG_PATH"]
        + " "
        + "-f' "
        "returned non-zero exit status 1."
    )
    nocolorcapsys.readouterr()


def test_make_docs_rm_cache(
    monkeypatch,
    nocolorcapsys,
    call_status,
    patch_sp_call,
    make_written,
    make_project_tree,
):
    """Test that ``make_docs`` properly removed all existing builds
    before starting a new one.

    :param monkeypatch:         ``pytest`` fixture for mocking
                                attributes.
    :param nocolorcapsys:       ``capsys`` without ANSI color codes.
    :param call_status:         Patch function to return specific
                                exit-code.
    :param patch_sp_call:       Patch ``pyaud.Subprocess.call``.
    :param make_written:        Create files with written content.
    :param make_project_tree:   Make directory structure.
    """

    def call_func():
        os.makedirs(pyaud.environ.env["DOCS_BUILD"])

    make_project_tree.docs_conf()
    make_written.readme()
    make_written.index_rst()
    make_written.readme_toc()
    make_written.repo_toc()
    make_toc = call_status("make_toc", 0)
    monkeypatch.setattr(pyaud.modules, "make_toc", make_toc)
    docs_build = pyaud.environ.env["DOCS_BUILD"]
    os.makedirs(docs_build)
    pathlib.Path(docs_build, "marker").touch()
    freeze_docs_build = os.listdir(docs_build)
    patch_sp_call(0, call_func)
    pyaud.modules.make_docs()
    assert freeze_docs_build != os.listdir(docs_build)
    nocolorcapsys.readouterr()


@pytest.mark.parametrize(
    "returncode,expected",
    [
        (0, "make_requirements\nmake_toc\nmake_whitelist\n"),
        (1, "make_requirements\n"),
    ],
    ids=["success", "fail"],
)
def test_make_files(
    monkeypatch, call_status, nocolorcapsys, track_called, returncode, expected
):
    """Test that the correct commands are executed when running
    ``make_files`` and that the process properly exits if one of the
    commands fails.

    :param monkeypatch:     ``pytest`` fixture for mocking attributes.
    :param call_status:     Patch function to return specific  exit-code.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param track_called:    Decorate a mocked function to print what was
                            called.
    :param returncode:      Returncode to patch function with.
    :param expected:        Expected output.
    """
    file_funcs = ["make_toc", "make_whitelist", "make_requirements"]
    for file_func in file_funcs:
        monkeypatch.setattr(
            pyaud.modules,
            file_func,
            track_called(call_status(file_func, returncode)),
        )
    pyaud.modules.make_files()
    assert nocolorcapsys.stdout() == expected


@pytest.mark.usefixtures("make_python_file")
@pytest.mark.parametrize(
    "assert_error", [False, True], ids=["success", "fail"]
)
def test_make_format(patch_sp_call, assert_error, nocolorcapsys):
    """Test ``make_format`` when successful and when it fails. Ensure
    process fails when "reformatted" is found in the ``black`` log as
    ``Black`` does not return a non-zero exit code for a format but in
    this instance we want it to fail in accordance with all the other
    processes.

    :param patch_sp_call:   Patch ``pyaud.Subprocess.call``.
    :param assert_error:    Assert error was raised: True or False.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    pyaud.pyitems.get_files()
    patch_sp_call(0)
    if assert_error:
        blacklogs = os.path.join(
            pyaud.environ.env["LOG_DIR"], pyaud.environ.env["PKG"] + ".log"
        )
        with open(blacklogs, "w") as fout:
            fout.write("reformatted")

        with pytest.raises(pyaud.PyaudSubprocessError):
            pyaud.modules.make_format()
    else:
        pyaud.modules.make_format()
        nocolorcapsys.readouterr()


@pytest.mark.usefixtures("make_python_file")
@pytest.mark.parametrize("is_file", [False, True])
def test_find_pylintrc_file(patch_sp_call, nocolorcapsys, is_file):
    """Test the ``pytest`` process when an rc-file exists and when one
    doesn't.

    :param patch_sp_call:   Patch ``pyaud.Subprocess.call``.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param is_file:         File exists: True or False.
    """
    patch_sp_call()
    expected = "--rcfile=" + pyaud.environ.env["PYLINTRC"]
    if is_file:
        pathlib.Path(pyaud.environ.env["PYLINTRC"]).touch()
        pyaud.pyitems.get_files()
        pyaud.modules.make_lint()
        assert expected in nocolorcapsys.stdout()
    else:
        pyaud.pyitems.get_files()
        assert expected not in nocolorcapsys.stdout()


def test_pipfile2req_commands(patch_sp_call, nocolorcapsys, make_written):
    """Test that the correct commands are executed when running
    ``make_requirements``.

    :param patch_sp_call:   Patch ``pyaud.Subprocess.call``.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param make_written:    Create files with written content.
    """
    make_written.pipfile_lock()
    patch_sp_call()
    pyaud.modules.make_requirements()
    expected = (
        f"Updating ``{pyaud.environ.env['REQUIREMENTS']}``",
        f"pipfile2req {pyaud.environ.env['PIPFILE_LOCK']}",
        f"pipfile2req {pyaud.environ.env['PIPFILE_LOCK']} --dev",
        "created ``requirements.txt``",
    )
    out = nocolorcapsys.stdout()
    assert all(e in out for e in expected)


def test_list_modules(main, nocolorcapsys):
    """Test that all modules are listed when running ``pyaud modules``.

    :param main:            Fixture for mocking ``pyaud.main``
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    with pytest.raises(SystemExit):
        main("modules")

    out = nocolorcapsys.stdout().splitlines()
    for key in [m.replace("_", "-") for m in pyaud.MODULES]:
        assert any(key in i for i in out)


def test_module_help(main, nocolorcapsys):
    """Test that all modules and their docs are listed when running
    ``pyaud modules MODULE``.

    :param main:            Mock main function.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    with pytest.raises(SystemExit):
        main("modules", "all")

    out = nocolorcapsys.stdout().splitlines()
    for key in pyaud.MODULES:
        assert "pyaud " + key.replace("_", "-") in out


def test_module_not_valid(main, nocolorcapsys):
    """Test that the right error message is displayed when a
    non-existing module is called.

    :param main:            Fixture for mocking ``pyaud.main``
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    with pytest.raises(SystemExit):
        main("modules", "not_a_module")

    out = nocolorcapsys.stderr().splitlines()
    assert "No such module: ``not_a_module``" in out


def test_get_branch_unique(init_test_repo):
    """Test that ``pyaud.pyaud.get_branch`` returns a unique
    timestamped branch after checkout out new branch from ``master``.
    """
    init_test_repo()
    branch = datetime.datetime.now().strftime("%d%m%YT%H%M%S")
    with pyaud.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
        git.checkout("-b", branch, devnull=True)
        assert pyaud.get_branch() == branch


def test_get_branch_initial_commit(init_test_repo):
    """Test that ``pyaud.pyaud.get_branch`` returns None when run from
    the a commit with no parent commits i.e. initial commit.
    """
    init_test_repo()
    with pyaud.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
        git.config("advice.detachedHead", "false")
        git.rev_list("--max-parents=0", "HEAD", capture=True)
        git.checkout(git.stdout.strip(), devnull=True)
        assert pyaud.get_branch() is None


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
    ids=["no_exclude", "exclude"],
)
def test_clean_exclude(main, nocolorcapsys, init_test_repo, exclude, expected):
    """Test clean files including exclude parameters

    :param main:            Mock main function.
    :param nocolorcapsys:   ``capsys`` without ANSI escape codes.
    :param exclude:         Files to exclude from ``git clean``.
    :param expected:        Expected output from ``pyaud clean``.

    """
    init_test_repo()
    for exclusion in exclude:
        obj = os.path.join(pyaud.environ.env["PROJECT_DIR"], exclusion)
        pathlib.Path(obj).touch()

    main("clean")
    assert nocolorcapsys.stdout() == expected


@pytest.mark.usefixtures("make_project_tree")
def test_git_context_no_artifact(tmpdir):
    """Ensure that no dir remains if no action occurs inside created
    dir. This functionality exists for cloning directories to keep
    ``pyaud.Git``s context action intact.

    :param tmpdir:  ``pytest`` ``tmpdir`` fixture for creating and
                    returning a temporary directory.
    """
    tmprepo = os.path.join(tmpdir, "test_repo")
    with pyaud.Git(tmprepo):

        # do nothing within repo but new dir is created in order for
        # context action of entering repo to work
        assert os.path.isdir(tmprepo)

    # ensure ``tmprepo`` has been removed
    assert not os.path.isdir(tmprepo)


def test_git_clone(tmpdir):
    """Test that the ``pyaud.Git`` class can properly clone a
    repository

    :param tmpdir:  ``pytest`` ``tmpdir`` fixture for creating and
                    returning a temporary directory.
    """
    with pyaud.Git(os.path.join(tmpdir, "cloned_repo")) as git:
        git.clone(tests.REAL_REPO)

    assert filecmp.dircmp(tests.REAL_REPO, pyaud.environ.env["PROJECT_DIR"])


def test_pipe_to_file():
    """Test that the ``pyaud.Subprocess`` class correctly writes to a
    file when the ``file`` keyword argument is used.
    """
    gitdir = os.path.join(pyaud.environ.env["PROJECT_DIR"], ".git") + os.sep
    piped_file = os.path.join(pyaud.environ.env["PROJECT_DIR"], "pipe.txt")
    expected = "Initialized empty Git repository in " + gitdir
    with pyaud.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
        git.init(file=piped_file)

    with open(piped_file) as fin:
        assert fin.read().strip() == expected


def test_del_item():
    """Test __delitem__ in ``Environ``."""
    os.environ["item"] = "del this"
    assert "item" in pyaud.environ.env
    assert pyaud.environ.env["item"] == "del this"
    del pyaud.environ.env["item"]
    assert "item" not in pyaud.environ.env
    del pyaud.environ.env["PKG"]
    assert "PYAUD_TEST_PKG" not in pyaud.environ.env


def test_len_env():
    """Test __len__ in ``Environ``."""
    environ_len = len(os.environ)
    for key in pyaud.environ.env:
        if key.startswith("PYAUD_TEST_"):
            del pyaud.environ.env[key]

    assert len(pyaud.environ.env) == environ_len - 32


def test_validate_env(validate_env):
    """Ensure an error is raised if the environment contains any
    remnants of the system's actual filepaths, and not just the
    filepaths contained within the /tmp directory.

    :param validate_env:    Execute the ``validate_env`` function
                            returned from this fixture.
    """
    real_tests = os.path.join(tests.REAL_REPO, "tests")
    pyaud.environ.env["TESTS"] = real_tests
    expected = (
        "environment not properly set: PYAUD_TEST_TESTS == " + real_tests
    )
    with pytest.raises(tests.PyaudTestError) as err:
        validate_env()

    assert str(err.value) == expected


def test_env_empty_keys():
    """Test that keys with no value are assigned as None."""
    with open(pyaud.environ.env["ENV"], "w") as fout:
        fout.write("NEW_KEY=")

    pyaud.environ.read_env(pyaud.environ.env["ENV"])
    assert pyaud.environ.env["NEW_KEY"] is None


@pytest.mark.parametrize("find_package", [True, False])
def test_find_package(
    monkeypatch, project_dir, make_project_tree, find_package
):
    """Test that Python package is found.

    :param monkeypatch:         ``pytest`` fixture for mocking
                                attributes.
    :param project_dir:         Create and return testing project root.
    :param make_project_tree:   Make directory structure.
    :param find_package:        Package exists and
                                ``pyaud.find_package`` should succeed.
    """
    monkeypatch.undo()
    os.environ["PROJECT_DIR"] = project_dir
    pyaud.environ.env["PROJECT_DIR"] = project_dir
    if find_package:
        make_project_tree.package()
        _ = pyaud.environ.find_package()
        assert pyaud.environ.find_package() == "repo"

    else:
        with pytest.raises(pyaud.environ.PyaudEnvironmentError) as err:
            pyaud.environ.find_package()

        assert str(err.value) == "Unable to find a Python package"


def test_config():
    """Test that the config properly parser a comma separated list and
    can resolve paths by expanding environment variables.
    """
    config = pyaud.config.ConfigParser()
    assert config.getlist("CLEAN", "exclude") == [
        "*.egg*",
        ".mypy_cache",
        ".env",
        "instance",
    ]


@pytest.mark.usefixtures("make_project_tree")
@pytest.mark.parametrize(
    "change,expected",
    [(False, True), (True, False)],
    ids=["no_change", "change"],
)
def test_hash_file(make_project_tree, change, expected):
    """Test that ``pyaud.HashCap`` can properly determine changes
    within a file.

    :param make_project_tree:   Make directory structure.
    :param change:              True or False: Change the file.
    :param expected:            Expected result from ``cap.compare``.
    """
    make_project_tree.toc()
    with pyaud.HashCap(pyaud.environ.env["TOC"]) as cap:
        if change:
            with open(pyaud.environ.env["TOC"], "w") as fin:
                fin.write("changed")

    assert cap.compare == expected


@pytest.mark.usefixtures("make_project_tree")
def test_readme_replace():
    """Test that ``pyaud.LineSwitch`` properly returns a file to
    how it was before the context action.
    """

    def _test_file_index(title, underline):
        with open(pyaud.environ.env["README_RST"]) as fin:
            lines = fin.read().splitlines()

        assert lines[0] == title
        assert lines[1] == len(underline) * "="

    repo = "repo"
    repo_underline = len(repo) * "="
    readme = "README"
    readme_underline = len(readme) * "="
    with open(pyaud.environ.env["README_RST"], "w") as fout:
        fout.write(repo + "\n" + repo_underline + "\n")

    _test_file_index(repo, repo_underline)
    with pyaud.LineSwitch(
        pyaud.environ.env["README_RST"], {0: readme, 1: readme_underline}
    ):
        _test_file_index(readme, readme_underline)

    _test_file_index(repo, repo_underline)


@pytest.mark.usefixtures("make_test_file")
def test_test_quantity():
    """Test that the right amount of tests are recorded."""
    test_total = pyaud.Tally.tests("test_*.py", "*_test.py")
    assert test_total == 20


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
def test_get_pyfiles(make_relative_file, assert_relative_item, assert_true):
    """Test ``get_pyfiles`` for standard files, nested directories (only
    return the directory root) or files that are excluded.

    :param make_relative_file:      Relative path to Python file.
    :param assert_relative_item:    Relative path to Python item to
                                    check for.
    :param assert_true:             Assert True or assert False.
    """
    project_dir = pyaud.environ.env["PROJECT_DIR"]
    make_file = os.path.join(project_dir, make_relative_file)
    make_item = os.path.join(project_dir, assert_relative_item)
    dirname = os.path.dirname(make_file)
    if not os.path.isdir(dirname):
        os.makedirs(os.path.dirname(make_file))

    pathlib.Path(make_file).touch()
    pyaud.pyitems.get_files()
    if assert_true:
        assert make_item in pyaud.pyitems.items
    else:
        assert make_item not in pyaud.pyitems.items


def test_pyitems_exclude_venv(make_project_tree):
    """Test that virtualenv dir is excluded from ``PythonItems.items``
    after running ``venv_exclude``.

    :param make_project_tree: Make directory structure.
    """
    make_project_tree.package()
    make_project_tree.mock_virtualenv()
    package = pyaud.environ.env["PKG_PATH"]
    venv = os.path.join(pyaud.environ.env["PROJECT_DIR"], "venv")
    pyaud.pyitems.get_files()
    assert set(pyaud.pyitems.items) == {package, venv}
    pyaud.pyitems.exclude_virtualenv()
    assert set(pyaud.pyitems.items) == {package}


@pytest.mark.usefixtures("make_python_file")
@pytest.mark.parametrize("is_file", [False, True])
def test_append_whitelist(nocolorcapsys, patch_sp_call, is_file):
    """Test that the whitelist file argument is appended to the
    ``vulture`` call if it exists and is not appended if it does not.

    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param patch_sp_call:   Patch ``pyaud.Subprocess.call``.
    :param is_file:         File exists: True or False.
    """
    patch_sp_call()
    expected = pyaud.environ.env["WHITELIST"]
    if is_file:
        pathlib.Path(pyaud.environ.env["WHITELIST"]).touch()
        pyaud.pyitems.get_files()
        pyaud.modules.make_unused()
        assert expected in nocolorcapsys.stdout()
    else:
        pyaud.pyitems.get_files()
        assert expected not in nocolorcapsys.stdout()


@pytest.mark.usefixtures("make_python_file")
def test_mypy_expected(patch_sp_call, nocolorcapsys):
    """Test that the ``mypy`` command is correctly called.

    :param patch_sp_call:   Patch ``pyaud.Subprocess.call``.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    patch_sp_call()
    pyaud.pyitems.get_files()
    pyaud.modules.make_typecheck()
    file_py = os.path.join(pyaud.environ.env["PROJECT_DIR"], FILES)
    assert f"mypy --ignore-missing-imports {file_py}" in nocolorcapsys.stdout()


@pytest.mark.parametrize(
    "test_mapping,call",
    [
        ({}, False),
        ({"tests": {}}, False),
        ({"tests": {"test.py": None}}, False),
        ({"tests": {"filename.py": None}}, False),
        ({"tests": {"_test.py": None}}, True),
        ({"tests": {"test_.py": None}}, True),
        ({"tests": {"three_test.py": None}}, True),
        ({"tests": {"test_four.py": None}}, True),
    ],
    ids=(
        "no_test_dir",
        "empty_test_dir",
        "invalid_name_1",
        "invalid_name_2",
        "valid_name_1",
        "valid_name_2",
        "valid_name_3",
        "valid_name_4",
    ),
)
def test_pytest_is_tests(
    patch_sp_call, nocolorcapsys, make_tree, test_mapping, call
):
    """Test that ``pytest`` is correctly called if:

        - tests with valid name exist within a tests dir

    Test that ``pytest`` is not called if:

        - there is a tests dir without tests
        - incorrect names within tests dir
        - no tests at all within tests dir.

    :param patch_sp_call:   Patch ``pyaud.Subprocess.call``.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param make_tree:       Make tree from parametrized mappings.
    :param test_mapping:    Parametrized mappings.
    :param call:            Pytest should be called.
    """
    patch_sp_call()
    make_tree(pyaud.environ.env["PROJECT_DIR"], test_mapping)
    pyaud.pyitems.get_files()
    pyaud.modules.make_tests()
    if call:
        expected = "pytest"
    else:
        expected = "No tests found"

    assert nocolorcapsys.stdout().strip() == expected


@pytest.mark.usefixtures("make_default_toc")
def test_make_toc(patch_sp_call, make_project_tree):
    """Test that the default toc file is edited correctly and additional
    files generated by ``sphinx-api`` doc are removed.

    :param patch_sp_call:       Patch ``pyaud.Subprocess.call``.
    :param make_project_tree:   Make directory structure.
    """
    make_project_tree.docs_conf()
    make_project_tree.package()
    patch_sp_call()
    altered_toc = (
        "repo\n"
        "====\n\n"
        ".. automodule:: repo\n"
        "   :members:\n"
        "   :undoc-members:\n"
        "   :show-inheritance:\n"
    )
    pyaud.modules.make_toc()
    with open(pyaud.environ.env["TOC"]) as fin:
        assert fin.read() == altered_toc

    module_toc = os.path.join(pyaud.environ.env["DOCS"], "modules.rst")
    assert not os.path.isfile(module_toc)


def test_make_requirements(patch_sp_output, nocolorcapsys, make_written):
    """Test that requirements.txt file is correctly edited after calling
    ``pipfile2req``.

    :param patch_sp_output: Patch ``pyaud.Subprocess`` so that ``call``
                            sends expected stdout out to self.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param make_written:    Create files with written content.
    """
    make_written.pipfile_lock()
    patch_sp_output(tests.files.PIPFILE2REQ_PROD, tests.files.PIPFILE2REQ_DEV)
    pyaud.modules.make_requirements()
    assert nocolorcapsys.stdout() == (
        f"Updating ``{pyaud.environ.env['REQUIREMENTS']}``\n"
        f"created ``requirements.txt``\n"
    )
    with open(pyaud.environ.env["REQUIREMENTS"]) as fin:
        assert fin.read() == tests.files.REQUIREMENTS


def test_make_whitelist(patch_sp_output, nocolorcapsys, make_project_tree):
    """Test a whitelist.py file is created properly after piping data
    from ``vulture --make-whitelist``.

    :param patch_sp_output:     Patch ``pyaud.Subprocess`` so that
                                ``call`` sends expected stdout out to
                                self.
    :param nocolorcapsys:       ``capsys`` without ANSI color codes.
    :param make_project_tree:   Make directory structure.
    """
    make_project_tree.be8a443_files()
    patch_sp_output(
        tests.files.Whitelist.be8a443_tests,
        tests.files.Whitelist.be8a443_pyaud,
    )
    pyaud.modules.pyitems.get_files()
    pyaud.modules.make_whitelist()
    assert nocolorcapsys.stdout() == (
        f"Updating ``{pyaud.environ.env['WHITELIST']}``\n"
        f"created ``whitelist.py``\n"
    )
    with open(pyaud.environ.env["WHITELIST"]) as fin:
        assert fin.read() == tests.files.Whitelist.be8a443_all()


def test_parser(monkeypatch, nocolorcapsys, track_called, call_status, main):
    """Test that passed arguments call the selected module correctly and
    without any errors.

    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param track_called:    Decorate a mocked function to print what was
                            called.
    :param call_status:     Patch function to return specific exit-code.
    :param main:            Fixture for mocking ``pyaud.main``
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
        "lint",
        "requirements",
        "tests",
        "toc",
        "typecheck",
        "unused",
        "whitelist",
    ]
    monkeypatch.setattr(
        pyaud,
        "MODULES",
        {
            m[0].replace("make_", ""): track_called(call_status(m[0], 0))
            for m in inspect.getmembers(pyaud.modules)
            if m[0].startswith("make_") and inspect.isfunction(m[1])
        },
    )
    for call in calls:
        main(call)
        module = "make_" + call.replace("-", "_")
        assert nocolorcapsys.stdout().strip() == module


def test_remove_unversioned(init_test_repo):
    """Test that when a file is not under version control and the
    ``pyaud.pyitems.exclude_unversioned`` method  is called unversioned
    files are removed from ``pyitems.items`` list.

    :param init_test_repo:  Create a git repository with an initial
                            commit.
    """
    init_test_repo()
    file_py = os.path.join(pyaud.environ.env["PROJECT_DIR"], FILES)
    pathlib.Path(file_py).touch()
    pyaud.pyitems.get_files()
    assert file_py in pyaud.pyitems.items
    pyaud.pyitems.exclude_unversioned()
    assert file_py not in pyaud.pyitems.items
    with pyaud.Git(pyaud.environ.env["PROJECT_DIR"]) as git:
        git.add(".")
        git.commit("-m", "committing file.py")

    pyaud.pyitems.get_files()
    assert file_py in pyaud.pyitems.items
    pyaud.pyitems.exclude_unversioned()
    assert file_py in pyaud.pyitems.items


def test_namespace_assignment_environ_file():
    """Ensure none of the below items are leaked into the user
    environment without the prefix ``PYAUD_``
    (``PYAUD_TEST_`` for test runs)
    """
    items = [
        "COVERAGE_XML",
        "DOCS",
        "DOCS_BUILD",
        "DOCS_CONF",
        "ENV",
        "PIPFILE_LOCK",
        "PYLINTRC",
        "README_RST",
        "REQUIREMENTS",
        "TESTS",
        "WHITELIST",
    ]
    pyaud.environ.init_environ()
    pyaud.environ.load_namespace()
    for item in items:
        assert item not in os.environ


def test_arg_order_clone(tmpdir, patch_sp_call, nocolorcapsys):
    """Test that the clone destination is always the last argument.

    :param tmpdir:          ``pytest`` ``tmpdir`` fixture for creating
                            and returning a temporary directory.
    :param patch_sp_call:   Patch ``pyaud.Subprocess.call``.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    patch_sp_call()
    project_clone = os.path.join(tmpdir, "pyaud")
    expected = (
        f"git clone --depth 1 --branch v1.1.0 {tests.REAL_REPO} "
        f"{project_clone}"
    )
    with pyaud.Git(project_clone) as git:
        git.clone("--depth", "1", "--branch", "v1.1.0", tests.REAL_REPO)
        assert nocolorcapsys.stdout().strip() == expected


def test_out_of_range_unversioned(tmpdir, main, other_dir, patch_sp_call):
    """Test that ``pyaud.pyitems.items`` populates when running on a
    path outside the user's "$PWD". If no properly populated an
    IndexError like the following would be raised:

        File "/*/**/python3.8/site-packages/pyaud/src/__init__.py",
        line 62, in exclude_unversioned
        self.items.pop(count)
        IndexError: pop index out of range

    :param tmpdir:              ``pytest`` ``tmpdir`` fixture for
                                creating and returning a temporary
                                directory.
    :param main:                Fixture for mocking ``pyaud.main``.
    :param other_dir:           Random directory existing in ``tmpdir``.
    :param patch_sp_call:       Patch ``pyaud.Subprocess.call``.
    """

    def empty_func(*_, **__):
        # this is meant to be empty
        pass

    project_clone = os.path.join(tmpdir, "pyaud")
    with pyaud.Git(project_clone) as git:
        git.clone(tests.REAL_REPO)
    patch_sp_call(0, empty_func)
    items = [
        os.path.join(project_clone, "pyaud"),
        os.path.join(project_clone, "tests"),
    ]
    with pyaud.EnterDir(other_dir):
        main("lint", "--path", "../pyaud")
        for item in items:
            assert item in pyaud.pyitems.items


def test_pylint_colorized(monkeypatch, capsys, failing_lint):
    """Test that color codes make their way through
    ``pylint --output-format=colorized``. If ``colorama`` is installed
    and a process calls ``colorama.init()`` a subprocess pipe will be
    stripped. Using environment variable ``PYCHARM_HOSTED`` for now as
    a workaround as this voids this action.

    :param monkeypatch:     ``pytest`` fixture for mocking attributes.
    :param capsys:          Capture sys output.
    :param failing_lint:    Create a failing file to lint.
    """
    monkeypatch.setattr(pyaud.pyitems, "items", [failing_lint])
    pyaud.modules.make_lint(suppress=True)
    codes = ["\x1b[7;33m", "\x1b[0m", "\x1b[1m", "\x1b[1;31m", "\x1b[35m"]
    output = capsys.readouterr()[0]
    for code in codes:
        assert code in output


@pytest.mark.parametrize(
    "iskey,key",
    [
        (False, datetime.datetime.now().strftime("%d%m%YT%H%M%S")),
        (True, "PROJECT_DIR"),
    ],
    ids=["iskey", "nokey"],
)
def test_temp_env_var(iskey, key):
    """Test ``pyaud.environ.TempEnvVar`` sets an environment variable
    and leaves everything as it originally was once the context action
    is done.
    """
    if iskey:
        assert key in os.environ
    else:
        assert key not in os.environ

    with pyaud.environ.TempEnvVar(key, "True"):
        assert key in os.environ and os.environ[key] == "True"

    if iskey:
        assert key in os.environ
    else:
        assert key not in os.environ


@pytest.mark.parametrize(
    "default", ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", None]
)
def test_loglevel(parser, default):
    """Test the right loglevel is set when parsing the commandline
    alongside default ``LOG_LEVEL`` environment variable.

    :param parser:  Instantiated ``Parser`` object with mock
                    ``sys.argv`` calls.
    :param default: Default ``LOG_LEVEL`` (``PYAUD_LOG_LEVEL``,
                    ``PYAUD_TEST_LOG_LEVEL`` in this case) - set in
                    .env file or bashrc etc.
    """
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    default_index = 1 if default is None else levels.index(default)
    module_arg = "unused"
    del os.environ["PYAUD_TEST_LOG_LEVEL"]

    def _increment(_int):
        inc = default_index - _int
        if inc <= 0:
            return "DEBUG"

        return levels[inc]

    mapping = {
        "": _increment(0),
        "-v": _increment(1),
        "-vv": _increment(2),
        "-vvv": _increment(3),
        "-vvvv": _increment(4),
    }

    for key, value in mapping.items():
        if default is not None:
            os.environ["PYAUD_TEST_LOG_LEVEL"] = default

        parser_instance = parser(module_arg, key)
        parser_instance.set_loglevel()
        assert os.environ["PYAUD_TEST_LOG_LEVEL"] == value


def test_isort_imports(project_dir, nocolorcapsys):
    """Test isort properly sorts file imports.

    :param project_dir:     Create and return testing project root.
    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    """
    file = os.path.join(project_dir, "file.py")
    with open(file, "w") as fout:
        fout.write(tests.files.IMPORTS_UNSORTED)

    pyaud.pyitems.get_files()
    pyaud.pyitems.get_file_paths()
    with pytest.raises(pyaud.PyaudSubprocessError):
        pyaud.modules.make_imports()

    with open(file) as fin:
        assert (
            tests.files.IMPORTS_SORTED.splitlines()[1:]
            == fin.read().splitlines()[:20]
        )

    pyaud.modules.make_imports()
    out = nocolorcapsys.stdout()
    assert all(
        i in out
        for i in (
            f"Fixing {file}",
            "Success: no issues found in 1 source files",
        )
    )


def test_readme(nocolorcapsys, main, make_readme):
    """Test standard README and return values.

    :param nocolorcapsys:   ``capsys`` without ANSI color codes.
    :param main:            Mock the main function for the package.
                            Provide test arguments to ``sys.argv`` as
                            function parameters.
    :param make_readme:     Create a README.rst file in the temp dir
                            containing the provided ``str``.
    """
    make_readme(tests.files.CODE_BLOCK_TEMPLATE)
    main("readme")
    output = "\n".join(
        [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    )
    assert output == tests.files.CODE_BLOCK_EXPECTED
