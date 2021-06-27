"""
pyaud.modules
=============
"""
import os
import shutil
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Callable, List

from .config import generate_rcfile, toml
from .environ import NAME, TempEnvVar
from .utils import (
    Git,
    HashCap,
    LineSwitch,
    PyAuditError,
    Subprocess,
    check_command,
    colors,
    deploy_docs,
    get_branch,
    tree,
    write_command,
)


def make_audit(**kwargs: bool) -> int:
    """Run all modules for complete package audit.

    :param kwargs:  Pass keyword arguments to audit submodule.
    :key clean:     Insert clean module to the beginning of module list
                    to remove all unversioned files before executing
                    rest of audit.
    :key deploy:    Append deploy modules (docs and coverage) to end of
                    modules list to deploy package data after executing
                    audit.
    :return:        Exit status.
    """
    audit_modules: List[Callable[..., Any]] = [
        make_format,
        make_format_docs,
        make_format_str,
        make_imports,
        make_typecheck,
        make_unused,
        make_lint,
        make_coverage,
        make_readme,
        make_docs,
    ]
    if kwargs.get("clean", False):
        audit_modules.insert(0, make_clean)

    if kwargs.get("deploy", False):
        audit_modules.append(make_deploy)

    for audit_module in audit_modules:
        colors.cyan.bold.print(
            "\n{}".format(
                audit_module.__name__.replace("make_", f"{NAME} ").replace(
                    "_", "-"
                )
            )
        )
        audit_module(**kwargs)

    return 0


def make_clean(**kwargs: bool) -> int:
    """Remove all unversioned package files recursively.

    :param kwargs:  Additional keyword arguments for ``git clean``.
    :return:        Exit status.
    """
    exclude = toml["clean"]["exclude"]
    with Git(os.environ["PROJECT_DIR"]) as git:
        return git.clean(  # type: ignore
            "-fdx", *[f"--exclude={e}" for e in exclude], **kwargs
        )


def make_coverage(**kwargs: bool) -> int:
    """Run package unit-tests with ``pytest`` and ``coverage``.

    :param kwargs:  Pass keyword arguments to ``pytest`` and ``call``.
    :return:        Exit status.
    """
    coverage = Subprocess("coverage")
    returncode = make_tests(*[f"--cov={e}" for e in tree.reduce()], **kwargs)
    if not returncode:
        with TempEnvVar(kwargs, suppress=True):
            return coverage.call("xml", **kwargs)

    print("No coverage to report")
    return 0


def make_deploy(**kwargs: bool) -> int:
    """Deploy package documentation and test coverage.

    :param kwargs:  Keyword arguments for ``deploy_module``.
    :return:        Exit status.
    """

    deploy_modules = [make_deploy_cov, make_deploy_docs]
    for deploy_module in deploy_modules:
        colors.cyan.bold.print(
            "\n{}".format(
                deploy_module.__name__.replace("make_", f"{NAME} ").replace(
                    "_", "-"
                )
            )
        )
        returncode = deploy_module(**kwargs)
        if returncode:
            return returncode

    return 0


def make_deploy_cov(**kwargs: bool) -> int:
    """Upload coverage data to ``Codecov``.

    If no file exists otherwise announce that no file has been created
    yet. If no ``CODECOV_TOKEN`` environment variable has been exported
    or defined in ``.env`` announce that no authorization token has been
    created yet.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    codecov = Subprocess("codecov")
    coverage_xml = os.environ["PYAUD_COVERAGE_XML"]
    if os.path.isfile(coverage_xml):
        if os.environ["CODECOV_TOKEN"] != "":
            return codecov.call("--file", coverage_xml, **kwargs)

        print("CODECOV_TOKEN not set")
    else:
        print("No coverage report found")

    return 0


def make_deploy_docs(**kwargs: bool) -> int:
    """Deploy package documentation to ``gh-pages``.

    Check that the branch is being pushed as master (or other branch
    for tests). If the correct branch is the one in use deploy.
    ``gh-pages`` to the orphaned branch - otherwise do nothing and
    announce.

    :param kwargs:  Pass keyword arguments to ``make_docs``.
    :return:        Exit status.
    """
    if get_branch() == "master":
        git_credentials = ["PYAUD_GH_NAME", "PYAUD_GH_EMAIL", "PYAUD_GH_TOKEN"]
        null_vals = [k for k in git_credentials if os.environ[k] == ""]
        if not null_vals:
            if not os.path.isdir(os.path.join(os.environ["BUILDDIR"], "html")):
                make_docs(**kwargs)

            deploy_docs()
        else:
            print("The following is not set:")
            for null_val in null_vals:
                print(f"- {null_val}")

            print()
            print("Pushing skipped")
    else:
        colors.green.print("Documentation not for master")
        print("Pushing skipped")

    return 0


def make_docs(**kwargs: bool) -> None:
    """Compile package documentation with ``Sphinx``.

    This is so the hyperlink isn't exactly the same as the package
    documentation. Build the ``Sphinx`` html documentation. Return the
    README's title to what it originally was.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    make_toc(**kwargs)

    readme_rst = "README"
    underline = len(readme_rst) * "="
    if os.path.isdir(os.environ["BUILDDIR"]):
        shutil.rmtree(os.environ["BUILDDIR"])

    sphinx_build = Subprocess("sphinx-build")
    if os.path.isdir(os.environ["PYAUD_DOCS"]):
        with LineSwitch(
            os.environ["PYAUD_README_RST"], {0: readme_rst, 1: underline}
        ):
            command = [
                "-M",
                "html",
                os.environ["PYAUD_DOCS"],
                os.environ["BUILDDIR"],
                "-W",
            ]
            sphinx_build.call(*command, **kwargs)
            colors.green.bold.print("Build successful")
    else:
        print("No docs found")


def make_files(**kwargs: bool) -> int:
    """Audit project data files.

    Make ``docs/<APPNAME>.rst``, ``whitelist.py``, and
    ``requirements.txt`` if none already exist, update them if they do
    and changes are needed or pass if nothing needs to be done.

    :param kwargs:  Pass keyword arguments to ``func``.
    :return:        Exit status.
    """
    for func in (make_requirements, make_toc, make_whitelist):
        returncode = func(**kwargs)
        if returncode:
            return returncode

    return 0


@check_command
def make_format(**kwargs: bool) -> int:
    """Audit code against ``Black``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    black = Subprocess("black", loglevel="debug")
    args = tree.reduce()
    try:
        return black.call("--check", *args, **kwargs)

    except CalledProcessError as err:
        black.call(*args, **kwargs)
        raise PyAuditError(f"{black} {args}") from err


@check_command
def make_lint(**kwargs: bool) -> int:
    """Lint code with ``pylint``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    with TempEnvVar(os.environ, PYCHARM_HOSTED="True"):
        args = tree.reduce()
        pylint = Subprocess("pylint")
        return pylint.call("--output-format=colorized", *args, **kwargs)


@write_command("PYAUD_REQUIREMENTS", required="PYAUD_PIPFILE_LOCK")
def make_requirements(**kwargs: bool) -> int:
    """Audit requirements.txt with Pipfile.lock.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    # get the stdout for both production and development packages
    p2req = Subprocess("pipfile2req", capture=True)
    p2req.call(os.environ["PYAUD_PIPFILE_LOCK"], **kwargs)
    p2req.call(os.environ["PYAUD_PIPFILE_LOCK"], "--dev", **kwargs)

    # write to file and then use sed to remove the additional
    # information following the semi-colon
    stdout = list(set("\n".join(p2req.stdout()).splitlines()))
    stdout.sort()
    with open(os.environ["PYAUD_REQUIREMENTS"], "w") as fout:
        for content in stdout:
            fout.write(f"{content.split(';')[0]}\n")

    return 0


def make_tests(*args: str, **kwargs: bool) -> int:
    """Run the package unit-tests with ``pytest``.

    :param args:    Additional positional arguments for ``pytest``.
    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    tests = os.environ["PYAUD_TESTS"]
    project_dir = os.environ["PROJECT_DIR"]
    patterns = ("test_*.py", "*_test.py")
    rglob = [p for a in patterns for p in Path(project_dir).rglob(a)]
    pytest = Subprocess("pytest")
    if os.path.isdir(tests) and rglob:
        return pytest.call(*args, **kwargs)

    print("No tests found")
    return 1


@write_command("PYAUD_TOC", required="PYAUD_DOCS")
def make_toc(**kwargs: bool) -> int:
    """Audit docs/<NAME>.rst toc-file.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    kwargs["devnull"] = True
    toc_attrs = [
        ".. automodule::",
        "   :members:",
        "   :undoc-members:",
        "   :show-inheritance:",
    ]
    if os.path.isfile(os.environ["PYAUD_DOCS_CONF"]):
        apidoc = Subprocess("sphinx-apidoc", devnull=True)
        apidoc.call(
            "-o", os.environ["PYAUD_DOCS"], os.environ["PYAUD_PKG_PATH"], "-f"
        )
        with open(os.environ["PYAUD_TOC"]) as fin:
            contents = fin.read().splitlines()

        with open(os.environ["PYAUD_TOC"], "w") as fout:
            fout.write(
                f"{os.environ['PYAUD_PKG']}\n"
                f"{len(os.environ['PYAUD_PKG']) * '='}\n\n"
            )
            for content in contents:
                if any(a in content for a in toc_attrs):
                    fout.write(f"{content}\n")

        modules = (
            os.path.join(
                os.environ["PYAUD_DOCS"], f"{os.environ['PYAUD_PKG']}.src.rst"
            ),
            os.path.join(os.environ["PYAUD_DOCS"], "modules.rst"),
        )
        for module in modules:
            if os.path.isfile(module):
                os.remove(module)

    return 0


@check_command
def make_typecheck(**kwargs: bool) -> int:
    """Typecheck code with ``mypy``.

    Check that there are no errors between the files and their
    stub-files.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    mypy = Subprocess("mypy")
    return mypy.call("--ignore-missing-imports", *tree.reduce(), **kwargs)


@check_command
def make_unused(**kwargs: bool) -> int:
    """Audit unused code with ``vulture``.

    Create whitelist first with --fix.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    args = tree.reduce()
    if os.path.isfile(os.environ["PYAUD_WHITELIST"]):
        args.append(os.environ["PYAUD_WHITELIST"])

    vulture = Subprocess("vulture")
    return vulture.call(*args, **kwargs)


@write_command("PYAUD_WHITELIST")
def make_whitelist(**kwargs: bool) -> int:
    """Check whitelist.py file with ``vulture``.

    This will consider all unused code an exception so resolve code that
    is not to be excluded from the ``vulture`` search first.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    vulture = Subprocess("vulture", capture=True)

    # append whitelist exceptions for each individual module
    for item in tree.reduce():
        if os.path.exists(item):
            with TempEnvVar(kwargs, suppress=True):
                vulture.call(item, "--make-whitelist", **kwargs)

    # clear contents of instantiated ``TextIO' object to write a new
    # file and not append
    stdout = [i for i in "\n".join(vulture.stdout()).splitlines() if i != ""]
    stdout.sort()
    with open(os.environ["PYAUD_WHITELIST"], "w") as fout:
        for line in stdout:
            fout.write(
                f"{line.replace(os.environ['PROJECT_DIR'] + os.sep, '')}\n"
            )

    return 0


@check_command
def make_imports(**kwargs: bool) -> int:
    """Audit imports with ``isort``.

    ``Black`` and ``isort`` clash in some areas when it comes to
    ``Black`` and sorting imports. To avoid running into false positives
    when running both in conjunction run ``Black`` straight after. Use
    ``HashCap`` to determine if any files have changed for presenting
    data to user.
    """
    changed = []
    isort = Subprocess("isort", capture=True)
    black = Subprocess("black", loglevel="debug", devnull=True)
    for item in tree:
        if os.path.isfile(item):
            with HashCap(item) as cap:
                isort.call(item, **kwargs)
                black.call(item, **kwargs)

            if not cap.compare:
                changed.append(
                    os.path.relpath(item, os.environ["PROJECT_DIR"])
                )
                for stdout in isort.stdout():
                    print(stdout)

    if changed:
        raise PyAuditError(f"{make_imports.__name__} {tuple(changed)}")

    return 0


def make_readme(**kwargs: bool) -> None:
    """Parse, test, and assert RST code-blocks.

    :key suppress:  Suppress error and continue running even with a
                    non-zero exit status.
    :return:        Subprocess exit status.
    """
    with TempEnvVar(os.environ, PYCHARM_HOSTED="True"):
        readmtester = Subprocess("readmetester")
        if os.path.isfile(os.environ["PYAUD_README_RST"]):
            readmtester.call(os.environ["PYAUD_README_RST"], **kwargs)
        else:
            print("No README.rst found in project root")


@check_command
def make_format_str(**kwargs: bool) -> int:
    """Format f-strings with ``flynt``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    flynt = Subprocess("flynt")
    args = ("--line-length", "72", "--transform-concats", *tree.reduce())
    try:
        return flynt.call(
            "--dry-run", "--fail-on-change", *args, devnull=True, **kwargs
        )

    except CalledProcessError as err:
        flynt.call(*args, **kwargs)
        raise PyAuditError(f"{flynt} {args}") from err


@check_command
def make_format_docs(**kwargs: bool) -> int:
    """Format docstrings with ``docformatter``.

    :param kwargs: Keyword arguments (later implemented).
    """
    docformatter = Subprocess("docformatter")
    args = ("--recursive", "--wrap-summaries", "72", *tree.reduce())
    try:
        return docformatter.call("--check", *args, **kwargs)

    except CalledProcessError as err:
        args = ("--in-place", *args)
        docformatter.call(*args, **kwargs)
        raise PyAuditError(f"{docformatter} {args}") from err


def make_generate_rcfile(**__: bool) -> None:
    """Print rcfile to stdout.

    Print rcfile to stdout so it may be piped to chosen filepath.
    """
    generate_rcfile()
