"""
tests.plugins_test
==================
"""
# pylint: disable=too-many-lines,too-many-arguments,cell-var-from-loop
# pylint: disable=too-few-public-methods,unused-variable
import os
import random
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, List, Tuple

import pytest

import plugins
import pyaud

from . import (
    CONFPY,
    FILES,
    INIT,
    INITIAL_COMMIT,
    NO_ISSUES,
    PLUGINS_MODULES_PLUGINS,
    PUSHING_SKIPPED,
    PYAUD_MODULES,
    README,
    REPO,
    SP_OPEN_PROC,
    files,
)


def test_no_files_found(main: Any, nocolorcapsys: Any) -> None:
    """Test the correct output is produced when no file exists.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    main("typecheck")
    assert nocolorcapsys.stdout().strip() == "No files found"


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
    main: Any,
    monkeypatch: Any,
    nocolorcapsys: Any,
    contents: List[str],
    expected: str,
) -> None:
    """Test the ``@write_command`` decorator.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param monkeypatch:     Mock patch environment and attributes.
    :param contents:        Content to write to file.
    :param expected:        Expected output.
    """
    for content in contents:

        def mock_write_whitelist(*_: Any, **__: Any) -> None:
            with open(Path.cwd() / os.environ["PYAUD_WHITELIST"], "w") as fout:
                fout.write(content)

        mocked_plugins = dict(pyaud.plugins.plugins)
        mocked_plugins["whitelist"] = pyaud.plugins.write_command(
            "PYAUD_WHITELIST"
        )(mock_write_whitelist)
        monkeypatch.setattr(PYAUD_MODULES, mocked_plugins)
        main("whitelist")

    assert expected in nocolorcapsys.stdout()


def test_make_audit_error(
    main: Any, monkeypatch: Any, nocolorcapsys: Any
) -> None:
    """Test errors are handled correctly when running ``pyaud audit``.

    :param main:            Patch package entry point.
    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    monkeypatch.setattr(
        "pyaud.utils.Subprocess._open_process", lambda *_, **__: 1
    )
    pyaud.utils.tree.append(Path.cwd() / FILES)
    with pytest.raises(CalledProcessError):
        main("audit")

    assert nocolorcapsys.stdout().strip() == "pyaud format"


def test_call_coverage_xml(
    main: Any, monkeypatch: Any, patch_sp_print_called: Any, nocolorcapsys: Any
) -> None:
    """Test ``coverage xml`` is called after successful test run.

    :param main:                    Patch package entry point.
    :param monkeypatch:             Mock patch environment and
                                    attributes.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    """
    patch_sp_print_called()
    monkeypatch.setattr("plugins.modules.make_tests", lambda *_, **__: 0)
    main("coverage")
    assert nocolorcapsys.stdout().strip() == "<Subprocess (coverage)> xml"


def test_make_deploy_all(
    main: Any, monkeypatch: Any, nocolorcapsys: Any, call_status: Any
) -> None:
    """Test the correct commands are run when running ``pyaud deploy``.

    Patch functions with ``call_status`` to remove functionality from
    function and only return a zero exit-status. ``make_deploy_*``
    functions should still be able to print what functions are being run
    as announced to the console in cyan.

    :param main:            Patch package entry point.
    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param call_status:    Patch function to not do anything.
                            Optionally returns non-zero exit code (0 by
                            default).
    """
    modules = "make_deploy_cov", "make_deploy_docs"
    for module in modules:
        monkeypatch.setattr(f"plugins.modules.{module}", call_status(module))

    main("deploy")
    out = nocolorcapsys.stdout().splitlines()
    for module in modules:
        assert (
            module.replace("make_", f"{pyaud.__name__} ").replace("_", "-")
            in out
        )


def test_make_deploy_all_fail(
    main: Any, call_status: Any, monkeypatch: Any, nocolorcapsys: Any
) -> None:
    """Test ``pyaud deploy`` fails correctly when encountering an error.

    :param main:            Patch package entry point.
    :param call_status:     Patch function to return specific exit-code.
    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    deploy_module = "make_deploy_docs"
    monkeypatch.setattr(
        f"plugins.modules.{deploy_module}", call_status(deploy_module, 1)
    )
    main("deploy")
    assert (
        deploy_module.replace("make_", f"{pyaud.__name__} ").replace("_", "-")
        in nocolorcapsys.stdout().splitlines()
    )


def test_make_docs_no_docs(main: Any, nocolorcapsys: Any) -> None:
    """Test correct message is produced.

    Test when running ``pyaud docs`` when no docs are present.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    Path(Path.cwd() / FILES).touch()
    main("docs")
    assert nocolorcapsys.stdout().strip() == "No docs found"


def test_suppress(
    main: Any, monkeypatch: Any, nocolorcapsys: Any, make_tree: Any
) -> None:
    """Test that audit proceeds through errors with ``--suppress``.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param monkeypatch:     Mock patch environment and attributes.
    :param make_tree:       Create directory tree from dict mapping.
    """
    make_tree(Path.cwd(), {FILES: None, "docs": {CONFPY: None}})
    pyaud.utils.tree.append(Path.cwd() / FILES)
    fix_modules = 6
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    main("audit", "--suppress")
    assert (
        len(
            [
                i
                for i in nocolorcapsys.stderr().splitlines()
                if "Failed: returned non-zero exit status" in i
            ]
        )
        == fix_modules
    )


def test_coverage_no_tests(main: Any, nocolorcapsys: Any) -> None:
    """Test the correct output is produced when no tests exists.

     Ensure message is displayed if ``pytest`` could not find a valid
     test folder.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    main("coverage")
    assert nocolorcapsys.stdout().strip() == (
        "No tests found\nNo coverage to report"
    )


def test_make_docs_toc_fail(
    main: Any, monkeypatch: Any, make_tree: Any
) -> None:
    """Test that error message is produced when ``make_toc`` fails.

    Test process stops when ``make_toc`` fails before running the main
    ``make_docs`` process.

    :param main:        Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree:   Create directory tree from dict mapping.
    """
    make_tree(Path.cwd(), {"docs": {CONFPY: None}})
    monkeypatch.setattr(
        "pyaud.utils.Subprocess._open_process", lambda *_, **__: 1
    )
    with pytest.raises(CalledProcessError) as err:
        main("docs")

    assert str(err.value) == (
        "Command 'sphinx-apidoc -o {} {} -f' "
        "returned non-zero exit status 1.".format(
            Path.cwd() / pyaud.environ.DOCS, Path.cwd() / REPO
        )
    )


def test_make_docs_rm_cache(
    main: Any, monkeypatch: Any, call_status: Any, make_tree: Any
) -> None:
    """Test ``make_docs`` removes all builds before starting a new one.

    :param main:            Patch package entry point.
    :param monkeypatch:     Mock patch environment and attributes.
    :param call_status:     Patch function to return specific exit-code.
    :param make_tree:       Create directory tree from dict mapping.
    """
    builddir = Path.cwd() / os.environ["BUILDDIR"]
    readme = Path.cwd() / README

    # disable call to ``Subprocess`` to only create ./docs/_build
    # directory so tests can continue
    def _call(*_: Any, **__: Any) -> int:
        builddir.mkdir(parents=True)
        return 0

    # patch ``make_toc`` and ``Subprocess.call``
    monkeypatch.setattr("plugins.modules.make_toc", call_status("make_toc"))
    monkeypatch.setattr("pyaud.utils.Subprocess.call", _call)
    make_tree(Path.cwd(), {"docs": {CONFPY: None, "readme.rst": None}})
    with open(readme, "w") as fout:
        fout.write(files.README_RST)

    builddir.mkdir(parents=True)
    Path(builddir / "marker").touch()
    freeze_docs_build = builddir.iterdir()

    # to test creation of README.rst content needs to be written to file
    with open(readme, "w") as fout:
        fout.write(files.README_RST)

    main("docs")
    assert freeze_docs_build != builddir.iterdir()


def test_make_files(
    main: Any,
    monkeypatch: Any,
    call_status: Any,
    nocolorcapsys: Any,
    track_called: Any,
) -> None:
    """Test correct commands are executed when running ``make_files``.

    :param main:            Patch package entry point.
    :param monkeypatch:     Mock patch environment and attributes.
    :param call_status:     Patch function to return specific exit-code.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    file_funcs = "make_toc", "make_whitelist", "make_requirements"
    for file_func in file_funcs:
        monkeypatch.setattr(
            f"plugins.modules.{file_func}",
            track_called(call_status(file_func)),
        )
    main("files")
    assert (
        nocolorcapsys.stdout()
        == "make_requirements\nmake_toc\nmake_whitelist\n"
    )


def test_make_format(main: Any) -> None:
    """Test ``make_format`` when successful and when it fails.

    :param main: Patch package entry point.
    """
    file = Path.cwd() / FILES
    with open(file, "w") as fout:
        fout.write(files.UNFORMATTED)

    pyaud.utils.tree.append(file)
    with pytest.raises(pyaud.exceptions.PyAuditError):
        main("format")


def test_pipfile2req_commands(
    main: Any, patch_sp_print_called: Any, nocolorcapsys: Any
) -> None:
    """Test that the correct commands are executed.

    :param main:                    Patch package entry point.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    """
    requirements = Path.cwd() / os.environ["PYAUD_REQUIREMENTS"]
    pipfile_lock = Path.cwd() / pyaud.environ.PIPFILE_LOCK
    with open(pipfile_lock, "w") as fout:
        fout.write(files.PIPFILE_LOCK)

    patch_sp_print_called()
    main("requirements")
    out = nocolorcapsys.stdout()
    assert all(
        e in out
        for e in (
            f"Updating ``{requirements}``",
            f"<Subprocess (pipfile2req)> {pipfile_lock}",
            f"<Subprocess (pipfile2req)> {pipfile_lock} --dev",
            f"created ``{requirements.name}``",
        )
    )


@pytest.mark.parametrize(
    "args,add,first,last",
    [
        ([], [], "pyaud format", "pyaud docs"),
        (["--clean"], ["clean"], "pyaud clean", "pyaud docs"),
        (["--deploy"], ["deploy"], "pyaud format", "pyaud deploy"),
        (
            ["--clean", "--deploy"],
            ["clean", "deploy"],
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
    mocked_modules = dict(pyaud.plugins.plugins)
    modules = list(pyaud.config.DEFAULT_CONFIG["audit"]["modules"])
    modules.extend(add)
    for module in modules:
        mocked_modules[module] = call_status(module)

    monkeypatch.setattr(PLUGINS_MODULES_PLUGINS, mocked_modules)
    main("audit", *args)
    output = [i for i in nocolorcapsys.stdout().splitlines() if i != ""]
    assert all([f"pyaud {i}" in output for i in modules])
    assert output[0] == first
    assert output[-1] == last


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
    Path(Path.cwd() / README).touch()
    pyaud.utils.git.init(devnull=True)  # type: ignore
    pyaud.utils.git.add(".")  # type: ignore
    pyaud.utils.git.commit(  # type: ignore
        "-m", "Initial commit", devnull=True
    )
    for exclusion in exclude:
        Path(Path.cwd() / exclusion).touch()

    main("clean")
    assert nocolorcapsys.stdout() == expected


def test_readme_replace() -> None:
    """Test that ``LineSwitch`` properly edits a file."""
    path = Path.cwd() / README

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
    with plugins.utils.LineSwitch(path, {0: readme, 1: readme_underline}):
        _test_file_index(readme, readme_underline)

    _test_file_index(repo, repo_underline)


def test_append_whitelist(
    main: Any, nocolorcapsys: Any, patch_sp_print_called: Any
) -> None:
    """Test that whitelist file argument is appended ``vulture`` call.

    Test for when whitelist.py exists and is not appended if it does
    not, thus avoiding an error.

    :param main:                    Patch package entry point.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    """
    project_dir = Path.cwd()
    whitelist = project_dir / os.environ["PYAUD_WHITELIST"]
    Path(project_dir / FILES).touch()
    patch_sp_print_called()
    whitelist.touch()
    pyaud.utils.tree.populate()
    pyaud.plugins.plugins["unused"]()
    main("unused")
    assert str(whitelist) in nocolorcapsys.stdout()


def test_mypy_expected(
    main: Any, patch_sp_print_called: Any, nocolorcapsys: Any
) -> None:
    """Test that the ``mypy`` command is correctly called.

    :param main:                    Patch package entry point.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    """
    path = Path(os.getcwd(), FILES)
    pyaud.utils.tree.append(path)
    patch_sp_print_called()
    main("typecheck")
    assert (
        f"<Subprocess (mypy)> --ignore-missing-imports {path}"
        in nocolorcapsys.stdout()
    )


@pytest.mark.parametrize(
    "relpath,expected",
    [
        (Path("tests"), "No tests found"),
        (Path("tests", "test.py"), "No tests found"),
        (Path("tests", "filename.py"), "No tests found"),
        (Path("tests", "_test.py"), "<Subprocess (pytest)>"),
        (Path("tests", "test_.py"), "<Subprocess (pytest)>"),
        (Path("tests", "three_test.py"), "<Subprocess (pytest)>"),
        (Path("tests", "test_four.py"), "<Subprocess (pytest)>"),
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
    main: Any,
    nocolorcapsys: Any,
    patch_sp_print_called: Any,
    relpath: Path,
    expected: str,
) -> None:
    """Test that ``pytest`` is correctly called.

    Test that ``pytest`` is not called if:

        - there is a tests dir without tests
        - incorrect names within tests dir
        - no tests at all within tests dir.

    :param main:                    Patch package entry point.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
                                    mapping.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param relpath:                 Relative path to file.
    :param expected:                Expected stdout.
    """
    pyaud.utils.tree.append(Path.cwd() / relpath)
    patch_sp_print_called()
    main("tests")
    assert nocolorcapsys.stdout().strip() == expected


def test_make_toc(
    main: Any, patch_sp_print_called: Any, make_tree: Any
) -> None:
    """Test that the default toc file is edited correctly.

    Ensure additional files generated by ``sphinx-api`` doc are removed.

    :param main:                    Patch package entry point.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    :param make_tree:               Create directory tree from dict
                                    mapping.
    """
    project_dir = Path.cwd()
    modules = "modules.rst"
    path = project_dir / pyaud.environ.DOCS / f"{REPO}.rst"
    make_tree(project_dir, {"docs": {modules: None, CONFPY: None}})
    with open(path, "w") as fout:
        assert fout.write(files.DEFAULT_TOC)

    patch_sp_print_called()
    main("toc")
    with open(path) as fin:
        assert fin.read() == files.ALTERED_TOC

    assert not Path(project_dir / pyaud.environ.DOCS / modules).is_file()


def test_make_requirements(
    main: Any, patch_sp_output: Any, nocolorcapsys: Any
) -> None:
    """Test that requirements.txt file is correctly edited.

     Tested for use with ``pipfile2req``.

    :param main:            Patch package entry point.
    :param patch_sp_output: Patch ``Subprocess`` so that ``call`` sends
                            expected stdout out to self.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    path = Path.cwd() / os.environ["PYAUD_REQUIREMENTS"]
    with open(Path.cwd() / pyaud.environ.PIPFILE_LOCK, "w") as fout:
        fout.write(files.PIPFILE_LOCK)

    patch_sp_output(files.PIPFILE2REQ_PROD, files.PIPFILE2REQ_DEV)
    main("requirements")
    assert nocolorcapsys.stdout() == (
        f"Updating ``{path}``\ncreated ``{path.name}``\n"
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
    project_dir = Path.cwd()
    whitelist = project_dir / os.environ["PYAUD_WHITELIST"]
    make_tree(
        project_dir,
        {
            "tests": {"conftest.py": None, FILES: None},
            "pyaud": {"src": {"__init__.py": None, "modules.py": None}},
        },
    )
    pyaud.utils.git.init(devnull=True)  # type: ignore
    pyaud.utils.git.add(".")  # type: ignore
    pyaud.utils.tree.populate()
    patch_sp_output(
        files.Whitelist.be8a443_tests, files.Whitelist.be8a443_pyaud
    )
    pyaud.plugins.plugins["whitelist"]()
    assert nocolorcapsys.stdout() == (
        f"Updating ``{whitelist}``\ncreated ``{whitelist.name}``\n"
    )
    with open(whitelist) as fin:
        assert fin.read() == files.Whitelist.be8a443_all()


def test_pylint_colorized(main: Any, capsys: Any) -> None:
    """Test that color codes are produced with ``process.PIPE``.

    Test ``pylint --output-format=colorized``. If ``colorama`` is
    installed and a process calls ``colorama.init()`` a process pipe
    will be stripped. Using environment variable ``PYCHARM_HOSTED`` for
    now as a workaround as this voids this action.

    :param main:    Patch package entry point.
    :param capsys:  Capture sys output.
    """
    path = Path.cwd() / FILES
    with open(path, "w") as fout:
        fout.write("import this_package_does_not_exist")

    pyaud.utils.tree.append(path)
    main("lint", "--suppress")
    output = capsys.readouterr()[0]
    assert all(
        i in output
        for i in ["\x1b[7;33m", "\x1b[0m", "\x1b[1m", "\x1b[1;31m", "\x1b[35m"]
    )


def test_isort_imports(main: Any, nocolorcapsys: Any) -> None:
    """Test isort properly sorts file imports.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    path = Path.cwd() / FILES
    with open(path, "w") as fout:
        fout.write(files.IMPORTS_UNSORTED)

    pyaud.utils.tree.append(path)
    main("imports", "--fix")
    with open(path) as fin:
        assert (
            files.IMPORTS_SORTED.splitlines()[1:]
            == fin.read().splitlines()[:20]
        )

    out = nocolorcapsys.stdout()
    assert all(i in out for i in (f"Fixed {path.name}", NO_ISSUES))
    main("imports")


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
    with open(Path.cwd() / README, "w") as fout:
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
        ("imports", "imports", files.IMPORTS_UNSORTED),
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
    project_dir = Path.cwd()
    file = project_dir / FILES
    make_tree(project_dir, {"tests": {"_test.py": None}, REPO: {INIT: None}})
    with open(file, "w") as fout:
        fout.write(content)

    pyaud.utils.git.add(".")  # type: ignore
    pyaud.utils.tree.populate()
    with pytest.raises(pyaud.exceptions.PyAuditError) as err:
        main(module)

    stderr = str(err.value)
    assert all(
        i in stderr for i in (process, file.name, "did not pass all checks")
    )
    assert "Path" not in stderr


@pytest.mark.usefixtures("init_remote")
def test_deploy_not_master(
    main: Any, monkeypatch: Any, nocolorcapsys: Any
) -> None:
    """Test that deployment is skipped when branch is not ``master``.

    :param main:            Patch package entry point.
    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    monkeypatch.setattr("plugins.modules.get_branch", lambda: "not_master")
    main("deploy-docs")
    out = [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    assert all(
        i in out for i in ["Documentation not for master", PUSHING_SKIPPED]
    )


@pytest.mark.usefixtures("init_remote")
def test_deploy_master_not_set(
    main: Any, monkeypatch: Any, nocolorcapsys: Any
) -> None:
    """Test correct notification is displayed.

    Test for when essential environment variables are not set in
    ``master``.

    :param main:            Patch package entry point.
    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    monkeypatch.setenv("PYAUD_GH_NAME", "")
    monkeypatch.setenv("PYAUD_GH_EMAIL", "")
    monkeypatch.setenv("PYAUD_GH_TOKEN", "")
    main("deploy-docs")
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
def test_deploy_master(
    main: Any, monkeypatch: Any, nocolorcapsys: Any
) -> None:
    """Test docs are properly deployed.

    Test for when environment variables are set and checked out at
    ``master``.

    :param main:            Patch package entry point.
    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    project_dir = Path.cwd()
    readme = project_dir / README
    monkeypatch.setattr(
        "plugins.modules.make_docs",
        lambda *_, **__: Path(
            Path.cwd() / os.environ["BUILDDIR"] / "html"
        ).mkdir(parents=True),
    )
    readme.touch()  # force stash
    pyaud.utils.git.add(".")  # type: ignore
    pyaud.utils.git.commit("-m", INITIAL_COMMIT, devnull=True)  # type: ignore

    with open(readme, "w") as fout:
        fout.write(files.README_RST)

    main("deploy-docs", "--fix")
    out = nocolorcapsys.stdout().splitlines()
    assert all(
        i in out
        for i in [
            "Pushing updated documentation",
            "Documentation Successfully deployed",
        ]
    )
    main("deploy-docs", "--fix")
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
    main: Any,
    monkeypatch: Any,
    nocolorcapsys: Any,
    rounds: int,
    expected: List[str],
) -> None:
    """Check that nothing happens when not checkout at at master.

    :param main:            Patch package entry point.
    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param rounds:          How many times ``make_deploy_docs`` needs to
                            be run.
    :param expected:        Expected stdout result.
    """
    path = Path.cwd()
    monkeypatch.setattr(
        "plugins.modules.make_docs",
        lambda *_, **__: Path(path / os.environ["BUILDDIR"] / "html").mkdir(
            parents=True
        ),
    )
    with open(path / README, "w") as fout:
        fout.write(files.README_RST)

    Path(path, FILES).touch()
    pyaud.utils.git.add(".", devnull=True)  # type: ignore
    pyaud.utils.git.commit("-m", INITIAL_COMMIT, devnull=True)  # type: ignore
    for _ in range(rounds):
        main("deploy-docs", "--fix")

    out = [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    assert all(i in out for i in expected)


def test_deploy_cov_report_token(
    main: Any, monkeypatch: Any, nocolorcapsys: Any, patch_sp_print_called: Any
) -> None:
    """Test ``make_deploy_cov`` when ``CODECOV_TOKEN`` is set.

    Test for when ``CODECOV_TOKEN`` is set and a coverage.xml file
    exists.

    :param main:                    Patch package entry point.
    :param monkeypatch:             Mock patch environment and
                                    attributes.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    """
    Path(Path.cwd() / os.environ["PYAUD_COVERAGE_XML"]).touch()
    patch_sp_print_called()
    monkeypatch.setenv("CODECOV_TOKEN", "token")
    main("deploy-cov")
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["<Subprocess (codecov)>", "--file"])


def test_deploy_cov_no_token(main: Any, nocolorcapsys: Any) -> None:
    """Test ``make_deploy_cov``.

    Test for when ``CODECOV_TOKEN`` when only a coverage.xml file
    exists.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    Path(Path.cwd() / os.environ["PYAUD_COVERAGE_XML"]).touch()
    main("deploy-cov")
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["CODECOV_TOKEN not set"])


def test_deploy_cov_no_report_token(main: Any, nocolorcapsys: Any) -> None:
    """Test ``make_deploy_cov``.

     Test for when ``CODECOV_TOKEN`` is not set and a coverage.xml file
     does not. exist.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    main("deploy-cov")
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["No coverage report found"])


def test_make_format_success(
    main: Any, nocolorcapsys: Any, patch_sp_print_called: Any
) -> None:
    """Test ``Format`` when successful.

    :param main:                    Patch package entry point.
    :param nocolorcapsys:           Capture system output while
                                    stripping ANSI color codes.
    :param patch_sp_print_called:   Patch ``Subprocess.call`` to only
                                    announce what is called.
    """
    pyaud.utils.tree.append(Path.cwd() / FILES)
    patch_sp_print_called()
    main("format")
    nocolorcapsys.readouterr()


def test_make_format_docs_fail(main: Any) -> None:
    """Test ``make_format`` when it fails.

    Ensure process fails when unformatted docstrings are found.

    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILES
    with open(path, "w") as fout:
        fout.write(files.DOCFORMATTER_EXAMPLE)

    pyaud.utils.tree.append(path)
    with pytest.raises(pyaud.exceptions.PyAuditError):
        main("format-docs")


def test_make_format_docs_suppress(main: Any, nocolorcapsys: Any) -> None:
    """Test ``make_format`` when running with ``-s/--suppress``.

    Ensure process announces it failed but does not actually return a
    non-zero exit-status.


    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    path = Path.cwd() / FILES
    with open(path, "w") as fout:
        fout.write(files.DOCFORMATTER_EXAMPLE)

    pyaud.utils.tree.append(path)
    main("format-docs", "--suppress")
    assert (
        nocolorcapsys.stderr().strip()
        == "Failed: returned non-zero exit status 3"
    )


def test_make_generate_rcfile(nocolorcapsys: Any):
    """Test for correct output when running ``generate-rcfile``.

    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    pyaud.plugins.plugins["generate-rcfile"]()
    assert (
        nocolorcapsys.stdout().strip()
        == pyaud.config.toml.dumps(pyaud.config.DEFAULT_CONFIG).strip()
    )


def test_isort_and_black(main: Any) -> None:
    """Test ``PyAuditError`` is raised.

    For failed checks when looking for formatted inputs run through
    ``isort`` and ``Black``.

    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILES
    with open(path, "w") as fout:
        fout.write(files.BEFORE_ISORT)

    pyaud.utils.tree.append(path)
    with pytest.raises(pyaud.exceptions.PyAuditError):
        main("imports")


def test_isort_and_black_fix(main: Any, nocolorcapsys: Any) -> None:
    """Test file is correctly fixed  for failed check.

    When looking for formatted inputs run through ``isort`` and
    ``Black`` ensure no errors are raised, and output is as expected.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    with open(Path.cwd() / FILES, "w") as fout:
        fout.write(files.BEFORE_ISORT)

    pyaud.utils.tree.append(Path.cwd() / FILES)
    main("imports", "--suppress", "--fix")
    out = nocolorcapsys.stdout()
    assert f"Fixed {Path(Path.cwd() / FILES).relative_to(Path.cwd())}" in out


def test_make_format_fix(main: Any) -> None:
    """Test ``make_format`` when it fails.

    :param main: Patch package entry point.
    """
    with open(Path.cwd() / FILES, "w") as fout:
        fout.write(files.UNFORMATTED)

    pyaud.utils.tree.append(Path.cwd() / FILES)
    main("format", "--fix")
    with open(Path.cwd() / FILES) as fin:
        assert fin.read().strip() == files.UNFORMATTED.replace("'", '"')


def test_make_unused_fix(main: Any, nocolorcapsys: Any) -> None:
    """Test ``make_unused`` when ``-f/--fix`` is provided.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    with open(Path.cwd() / FILES, "w") as fout:
        fout.write(files.UNFORMATTED)  # also an unused function

    pyaud.utils.tree.append(Path.cwd() / FILES)
    main("unused", "--fix")
    assert nocolorcapsys.stdout() == (
        "{}:1: unused function 'reformat_this' (60% confidence)\n"
        "Updating ``{}``\n"
        "created ``whitelist.py``\n"
        "Success: no issues found in 1 source files\n".format(
            Path.cwd() / FILES, Path.cwd() / os.environ["PYAUD_WHITELIST"]
        )
    )
    with open(Path.cwd() / os.environ["PYAUD_WHITELIST"]) as fin:
        assert fin.read().strip() == (
            "reformat_this  # unused function (file.py:1)"
        )


def test_make_unused_fail(main: Any) -> None:
    """Test ``make_unused`` with neither ``--fix`` or ``--suppress``.

    :param main: Patch package entry point.
    """
    with open(Path.cwd() / FILES, "w") as fout:
        fout.write(files.UNFORMATTED)  # also an unused function

    pyaud.utils.tree.append(Path.cwd() / FILES)
    with pytest.raises(pyaud.exceptions.PyAuditError) as err:
        main("unused")

    assert str(
        err.value
    ) == "<Subprocess (vulture)> ('{}',) did not pass all checks".format(
        Path.cwd() / FILES
    )


def test_make_format_docs_fix(main: Any, nocolorcapsys: Any) -> None:
    """Test ``make_format`` when running with ``-f/--fix``.

    Ensure process fixes checked failure.


    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    pyaud.utils.tree.append(Path.cwd() / FILES)
    with open(Path.cwd() / FILES, "w") as fout:
        fout.write(files.DOCFORMATTER_EXAMPLE)

    main("format-docs", "--fix")
    assert nocolorcapsys.stdout().strip() == NO_ISSUES


def test_format_str_fix(main: Any, nocolorcapsys: Any) -> None:
    """Test fix audit when f-strings can be created with ``flynt``.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    """
    with open(Path.cwd() / FILES, "w") as fout:
        fout.write(files.FORMAT_STR_FUNCS_PRE)

    pyaud.utils.git.add(".", devnull=True)  # type: ignore
    pyaud.utils.tree.populate()
    main("format-str", "--fix")
    nocolorcapsys.stdout()
    with open(Path.cwd() / FILES) as fin:
        assert fin.read() == files.FORMAT_STR_FUNCS_POST


def test_custom_modules(
    monkeypatch: Any, nocolorcapsys: Any, main: Any, call_status: Any
) -> None:
    """Test the ``custom`` arg runs what is configured in toml file.

    :param monkeypatch:     Mock patch environment and attributes.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param main:            Patch package entry point.
    :param call_status:     Patch function to not do anything.
                            Optionally returns non-zero exit code (0 by
                            default).
    """
    mocked_modules = dict(pyaud.plugins.plugins)
    modules = list(pyaud.config.DEFAULT_CONFIG["audit"]["modules"])
    random.shuffle(modules)
    pyaud.config.toml["audit"]["modules"] = modules
    for module in modules:
        mocked_modules[module] = call_status(module)

    monkeypatch.setattr(PLUGINS_MODULES_PLUGINS, mocked_modules)

    # make ``load_config`` do nothing so it does not override the toml
    # config above
    monkeypatch.setattr("pyaud.main.load_config", lambda *_: None)
    main("audit")
    out = [i for i in nocolorcapsys.stdout().splitlines() if i != ""]
    assert out == [f"pyaud {i}" for i in modules]


@pytest.mark.parametrize(
    "arg,expected",
    [
        ("", list(pyaud.plugins.plugins)),
        ("audit", ["audit -- Read from [audit] key in config"]),
        ("all", list(pyaud.plugins.plugins)),
    ],
    ids=["no-pos", "module", "all-modules"],
)
def test_help_with_plugins(
    main: Any, nocolorcapsys: Any, arg: str, expected: Tuple[str, ...]
) -> None:
    """Test expected output for help after plugins have been loaded.

    Test no positional argument for json array of keys.
    Test ``audit`` positional argument and docstring display.
    Test all and display of all module docstrings.

    :param main:            Patch package entry point.
    :param nocolorcapsys:   Capture system output while stripping ANSI
                            color codes.
    :param arg:             Positional argument for ```pyaud modules``.
    :param expected:        Expected result when calling command.
    """
    with pytest.raises(SystemExit):
        main("modules", arg)

    out = nocolorcapsys.stdout()
    assert any(i in out for i in expected)
